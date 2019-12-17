#ifdef __linux__
#  define _GNU_SOURCE
#  include <sched.h>
#endif
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <math.h>

#include "buffer.h"
#include "log.h"
#include "receiver.h"
#include "stream.h"
#include "thread_barrier.h"
#include "thread_pool.h"
#include "timer.h"

#ifdef WITH_MS
#   include <oskar_measurement_set.h>
#endif


/**
 * Manage the buffer and returns the buffer to use for the current data packet
 *
 * Check to see if any buffers have been locked or finished with
 * repurpose the oldest buffer not in use.
 *
 * @param self
 * @param heap
 * @param length
 * @param timestamp
 * @return
 */
struct Buffer* receiver_buffer(struct Receiver* self, int heap, size_t length,
        double timestamp)
{
    if (!self) return 0;
    struct Buffer* buf = 0;
    int oldest = -1, min_heap_start = 1 << 30;
    pthread_mutex_lock(&self->lock);
    for (int i = 0; i < self->num_buffers; ++i)
    {
        struct Buffer* buf_test = self->buffers[i];
        if (heap >= buf_test->heap_id_start && heap <= buf_test->heap_id_end &&
                !buf_test->locked_for_write)
        {
            buf_test->byte_counter += length;
            buf_test->last_updated = timestamp;
            pthread_mutex_unlock(&self->lock);
            return buf_test;
        }
        if (buf_test->heap_id_start < min_heap_start)
        {
            min_heap_start = buf_test->heap_id_start;
            oldest = i;
        }
    }
    /* Heap does not belong in any active buffer. */
    if (oldest >= 0)
    {
        if (heap < min_heap_start)
        {
            /* Dump data if it's too old. */
            pthread_mutex_unlock(&self->lock);
            return 0;
        }
        struct Buffer* buf_test = self->buffers[oldest];
        if (buf_test->byte_counter == 0 && !buf_test->locked_for_write)
        {
            /* Re-purpose the oldest buffer, if it isn't in use. */
            buf = buf_test;
            LOG_INFO(0, "Re-assigned buffer %d", buf->buffer_id);
        }
    }
    if (!buf && (self->num_buffers < self->max_num_buffers))
    {
        /* Create a new buffer. */
        buf = buffer_create(self->num_times_in_buffer, self->num_streams,
                self->num_baselines, self->num_buffers, self);
        LOG_INFO(0, "Created buffer %d", self->num_buffers);
        self->num_buffers++;
        self->buffers = (struct Buffer**) realloc(self->buffers,
                self->num_buffers * sizeof(struct Buffer*));
        self->buffers[self->num_buffers - 1] = buf;
    }
    if (buf)
    {
        buf->byte_counter += length;
        buf->last_updated = timestamp;
        buf->heap_id_start =
                self->num_times_in_buffer * (heap / self->num_times_in_buffer);
        buf->heap_id_end = buf->heap_id_start + self->num_times_in_buffer - 1;
    }
    pthread_mutex_unlock(&self->lock);
    return buf;
}

/**
 * Create a receiver object
 *
 * @param max_num_buffers
 * @param num_times_in_buffer
 * @param num_threads_recv
 * @param num_threads_write
 * @param num_streams
 * @param port_start
 * @param num_channels_per_file
 * @param output_root
 * @return
 */
struct Receiver* receiver_create(int num_stations, int max_num_buffers, int num_times_in_buffer,
        int num_threads_recv, int num_threads_write, int num_streams,
        unsigned short int port_start, int num_channels_per_file,
        const char* output_root)
{
    struct Receiver* cls =
            (struct Receiver*) calloc(1, sizeof(struct Receiver));
    pthread_mutex_init(&cls->lock, NULL);
    cls->tmr = tmr_create();
    cls->barrier = barrier_create(num_threads_recv);
    cls->pool = threadpool_create(1);
    cls->max_num_buffers = max_num_buffers;
    cls->num_times_in_buffer = num_times_in_buffer;
    cls->num_threads_recv = num_threads_recv;
    cls->num_threads_write = num_threads_write;
    cls->num_streams = num_streams;
    cls->num_channels_per_file = num_channels_per_file;
    cls->num_stations = num_stations;
    if (output_root && strlen(output_root) > 0)
    {
        cls->output_root = (char*) malloc(1 + strlen(output_root));
        strcpy(cls->output_root, output_root);
    }
    cls->port_start = port_start;
    cls->streams =
            (struct Stream**) calloc(num_streams, sizeof(struct Stream*));
    for (int i = 0; i < num_streams; ++i)
        cls->streams[i] = stream_create(
                port_start + (unsigned short int)i, i, cls);
    cls->antennas = calloc(1, sizeof(struct Antenna));
#ifdef WITH_MS
    int num_channels = num_streams;
    int num_pols = 4;
    double ref_freq_hz = 100.0e6;
    double freq_inc_hz = 100.0e3;
    int write_autocorr = 1;
    int write_crosscorr = 1;
    cls->ms = oskar_ms_create(
            cls->output_root, "vis_recv", num_stations, num_channels,
            num_pols, ref_freq_hz, freq_inc_hz, write_autocorr,
            write_crosscorr);
#endif
    return cls;
}


/**
 * Free the receiver object
 *
 * @param self
 */
void receiver_free(struct Receiver* self)
{
    if (!self) return;
    tmr_free(self->tmr);
    barrier_free(self->barrier);
    threadpool_free(self->pool);
    for (int i = 0; i < self->num_streams; ++i) stream_free(self->streams[i]);
    for (int i = 0; i < self->num_buffers; ++i) buffer_free(self->buffers[i]);
    pthread_mutex_destroy(&self->lock);
    free(self->coords_x);
    free(self->coords_y);
    free(self->coords_z);
    free(self->diam);
    free(self->name);
    free(self->streams);
    free(self->buffers);
    free(self->output_root);
#ifdef WITH_MS
    oskar_ms_close(self->ms);
#endif
    free(self);
}

struct ThreadArg
{
    int thread_id;
    struct Receiver* receiver;
    struct Buffer* buffer;
};

/**
 * Thread start routine used to write the visibility buffer.
 *
 * @param arg Thread arguments
 * @return
 */
static void* thread_write_parallel(void* arg)
{
    struct ThreadArg* thread_args = (struct ThreadArg*) arg;
    struct Receiver* receiver = thread_args->receiver;
    struct Buffer* buf = thread_args->buffer;
    const int thread_id = thread_args->thread_id;
    const int num_threads = receiver->num_threads_write;
    const int num_baselines = buf->num_baselines;
    const int num_channels = buf->num_channels;
    const int num_channels_per_file = receiver->num_channels_per_file;
    size_t len = 2 + strlen(receiver->output_root);
    len += (10 + 1 + 10 + 4);
    char* filename = (char*) calloc(len, sizeof(char));
    for (int c = thread_id * num_channels_per_file; c < num_channels;
            c += (num_threads * num_channels_per_file))
    {
        int c_end = c + num_channels_per_file - 1;
        if (c_end >= num_channels) c_end = num_channels - 1;
        int num_channels_block = c_end - c + 1;
        snprintf(filename, len, "%s_t%.4d-%.4d_c%.4d-%.4d.dat",
                receiver->output_root,
                buf->heap_id_start, buf->heap_id_end, c, c_end);
        /* Use POSIX creat(), write(), close()
         * instead of fopen(), fwrite(), fclose(),
         * as fwrite() doesn't seem to work with Alpine and BeeGFS. */
        int file_handle = creat(filename,
                S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH);
        if (file_handle < 0)
        {
            LOG_ERROR(thread_id, "Unable to open file %s", filename);
            break;
        }
        for (int t = 0; t < buf->num_times; ++t)
        {
            const struct DataType* block_start = buf->vis_data +
                    num_baselines * (num_channels * t + c);
            write(file_handle, (const void*)block_start,
                    num_channels_block * buf->block_size);
        }
        close(file_handle);
    }
    free(filename);
    return 0;
}

/**
 * Start write of visibility data buffers
 *
 * @param arg
 * @return
 */
static void* thread_write_buffer(void* arg)
{
    struct Buffer* buf = (struct Buffer*) arg;
    struct Receiver* receiver = buf->receiver;
    if (buf->byte_counter != buf->buffer_size)
        LOG_WARN(0, "Buffer %d incomplete (%zu/%zu, %.1f%%)",
                buf->buffer_id, buf->byte_counter, buf->buffer_size,
                100 * buf->byte_counter / (float)buf->buffer_size);
    if (receiver->output_root)
    {
#ifdef __linux__
        const int cpu_id = sched_getcpu();
        LOG_INFO(0, "Writing buffer %d from CPU %d...", buf->buffer_id, cpu_id);
#else
        LOG_INFO(0, "Writing buffer %d...", buf->buffer_id);
#endif
        const double start = tmr_get_timestamp();
        const int num_threads = receiver->num_threads_write;
        pthread_attr_t attr;
        pthread_attr_init(&attr);
        pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_JOINABLE);
        pthread_t* threads =
                (pthread_t*) malloc(num_threads * sizeof(pthread_t));
        struct ThreadArg* args = (struct ThreadArg*)
                malloc(num_threads * sizeof(struct ThreadArg));
        for (int i = 0; i < num_threads; ++i)
        {
            args[i].thread_id = i;
            args[i].receiver = receiver;
            args[i].buffer = buf;
            pthread_create(&threads[i], &attr,
                    &thread_write_parallel, &args[i]);
        }
        for (int i = 0; i < num_threads; ++i)
            pthread_join(threads[i], NULL);
        pthread_attr_destroy(&attr);
        free(args);
        free(threads);
        const double time_taken = tmr_get_timestamp() - start;
        LOG_INFO(0,
                "Writing buffer %d with %d threads took %.2f sec (%.2f MB/s)",
                buf->buffer_id, num_threads, time_taken,
                buf->buffer_size * 1e-6 / time_taken);
    }
    buffer_clear(buf);
    buf->locked_for_write = 0;
    return 0;
}

#ifdef WITH_MS
/**
 * Start write of visibility data buffers
 *
 * @param arg
 * @return
 */

static void* thread_write_buffer_ms(void* arg)
{
    struct Buffer* buf = (struct Buffer*) arg;
    struct Receiver* receiver = buf->receiver;
    double hour_angle = receiver->timestamp_count - receiver->ra;
    if (buf->byte_counter != buf->buffer_size)
        LOG_WARN(0, "Buffer %d incomplete (%zu/%zu, %.1f%%)",
               buf->buffer_id, buf->byte_counter, buf->buffer_size,
               100 * buf->byte_counter / (float)buf->buffer_size);
    if (receiver->output_root)
    {
#ifdef __linux__
        const int cpu_id = sched_getcpu();
        LOG_INFO(0, "Writing buffer %d from CPU %d...", buf->buffer_id, cpu_id);
#else
        LOG_INFO(0, "Writing buffer %d...", buf->buffer_id);
#endif
        const double start = tmr_get_timestamp();
        oskar_ms_set_phase_centre(receiver->ms, 0, receiver->ra, receiver->dec);

        for (unsigned int t = 0; t < buf->num_times; ++t)
        {
            if(receiver->coords_x != 0)
                calculate_uvw(buf);
            unsigned int t_global = receiver->write_counter *
                    buf->num_times + t;
            unsigned int start_row = t_global * buf->num_baselines;
            oskar_ms_write_coords_d(receiver->ms, start_row,
                    buf->num_baselines, buf->uu, buf->vv, buf->ww,
                    1.0, 1.0, 0.0);
            for (unsigned int c = 0; c < buf->num_channels; ++c)
            {
                const struct DataType* block_start = buf->vis_data +
                    buf->num_baselines * (buf->num_channels * t + c);
                for (unsigned int i = 0; i < buf->num_baselines; ++i) {
                    float* dst = buf->vis_unpacked + i * 8;
                    memcpy(dst, (float*)&(block_start[i].vis),
                            8 * sizeof(float));
                }
                oskar_ms_write_vis_f(
                        receiver->ms, start_row,
                        c, 1, buf->num_baselines,
                        buf->vis_unpacked);
            }
        }
        receiver->write_counter++;
        const double time_taken = tmr_get_timestamp() - start;
        LOG_INFO(0, "Writing buffer %d took %.2f sec (%.2f MB/s)",
               buf->buffer_id, time_taken,
               buf->buffer_size * 1e-6 / time_taken);
    }
    buffer_clear(buf);
    buf->locked_for_write = 0;
    return 0;
}
#endif



/**
 * Receiver thread start routine
 *
 * @param arg Thread argument structure
 */
static void* thread_receive(void* arg)
{
    struct ThreadArg* thread_args = (struct ThreadArg*) arg;
    struct Receiver* receiver = thread_args->receiver;
    const int thread_id = thread_args->thread_id;
    const int num_threads = receiver->num_threads_recv;
    const int num_streams = receiver->num_streams;
    LOG_DEBUG(0, "Starting receiver thread %d (num streams = %d)",
            thread_id, num_streams);

    // Wait for all streams handled by this thread to be completed.
    while (receiver->completed_streams != num_streams)
    {
        // Call receive on all current streams (non blocking)
        for (int i = thread_id; i < num_streams; i += num_threads)
        {
            struct Stream* stream = receiver->streams[i];
            if (!stream->done)
                stream_receive(stream);
        }

        // Make sure threads dont get out of sync
        if (num_threads > 1)
            barrier_wait(receiver->barrier);

        // Determine if the buffer can be written and report stream stats
        if (thread_id == 0)
        {
            double now = tmr_get_timestamp();
            const int num_buffers = receiver->num_buffers;

            // Loop over buffer to determine if they can be written
            // if yes, write buffer using a pool of threads.
            for (int i = 0; i < num_buffers; ++i)
            {
                struct Buffer* buf = receiver->buffers[i];
                // Determine if the buffer is ready to be written
                if ((buf->byte_counter > 0) && !buf->locked_for_write &&
                        (now - buf->last_updated >= 1.0))
                {
                    buf->locked_for_write = 1;
                    LOG_INFO(0,
                            "Locked buffer %d for writing", buf->buffer_id);
#ifdef WITH_MS
                    threadpool_enqueue(receiver->pool,
                            &thread_write_buffer_ms, buf);
#else
                    threadpool_enqueue(receiver->pool,
                            &thread_write_buffer, buf);
#endif
                }
            }

            // Get stats on the state of the streams
            size_t dump_byte_counter = 0;
            size_t recv_byte_counter = 0;
            receiver->completed_streams = 0;
            for (int i = 0; i < num_streams; ++i)
            {
                struct Stream* stream = receiver->streams[i];
                if (stream->done) receiver->completed_streams++;
                recv_byte_counter += stream->recv_byte_counter;
                dump_byte_counter += stream->dump_byte_counter;
            }
            const double overall_time = tmr_elapsed(receiver->tmr);

            // Report stats on the state of the stream (every GB or 1s)
            if (recv_byte_counter > 1000000000uL || overall_time > 1.0)
            {
                double memcpy_total = 0.0;
                for (int i = 0; i < num_streams; ++i)
                {
                    struct Stream* stream = receiver->streams[i];
                    stream->recv_byte_counter = 0;
                    stream->dump_byte_counter = 0;
                    memcpy_total += tmr_elapsed(stream->tmr_memcpy);
                    tmr_clear(stream->tmr_memcpy);
                }
                memcpy_total /= num_streams;
                LOG_INFO(0, "Received %.3f MB in %.3f sec (%.2f MB/s), "
                        "memcpy was %.2f%%",
                        recv_byte_counter / 1e6, overall_time,
                        (recv_byte_counter / 1e6) / overall_time,
                        100 * (memcpy_total / overall_time));
                if (dump_byte_counter > 0)
                    LOG_WARN(0, "Dumped %zu bytes", dump_byte_counter);
                tmr_start(receiver->tmr);
            }
        }

        if (num_threads > 1)
            barrier_wait(receiver->barrier);
    }
    return 0;
}


/**
 * Start the SPEAD receiver.
 *
 * @param self Receiver object
 */
void receiver_start(struct Receiver* self)
{
    if (!self) return;
    const int num_threads = self->num_threads_recv;
    pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_JOINABLE);
    pthread_t* threads = (pthread_t*) malloc(num_threads * sizeof(pthread_t));
    struct ThreadArg* args =
            (struct ThreadArg*) malloc(num_threads * sizeof(struct ThreadArg));
    tmr_start(self->tmr);
    for (int i = 0; i < num_threads; ++i)
    {
        args[i].thread_id = i;
        args[i].receiver = self;
        pthread_create(&threads[i], &attr, &thread_receive, &args[i]);
    }
    for (int i = 0; i < num_threads; ++i)
        pthread_join(threads[i], NULL);
    pthread_attr_destroy(&attr);
    free(args);
    free(threads);
    LOG_INFO(0, "All %d stream(s) completed.", self->num_streams);
}

void receiver_set_phase(struct Receiver* self, double ra, double dec)
{
    self->ra = ra;
    self->dec = dec;
}

void calculate_uvw(struct Buffer* arg)
{
    int i,j,k;
    int num_stations;
    double hour_angle, ra, dec, timestamp_count;
    double dec_sin, dec_cos, ha_sin, ha_cos;
    struct Buffer* buf = arg;
    struct Receiver* recv = (struct Receiver*) buf->receiver;
    ra = buf->receiver->ra;
    dec = buf->receiver->dec;
    timestamp_count = buf->receiver->timestamp_count;
    hour_angle = timestamp_count - ra;
    double *antenna_differences_x = malloc(buf->num_baselines*sizeof(double));
    double *antenna_differences_y = malloc(buf->num_baselines*sizeof(double));
    double *antenna_differences_z = malloc(buf->num_baselines*sizeof(double));
    num_stations = recv->num_stations;
    dec_sin = sin(dec);
    dec_cos = cos(dec);
    ha_sin = sin(hour_angle);
    ha_cos = cos(hour_angle);
    k = 0;
    for(i = 0; i < num_stations - 1; i++)
    {
        for(j = i; j < num_stations; j++)
        {
            antenna_differences_x[k] = recv->coords_x[j] - recv->coords_x[i];
            antenna_differences_y[k] = recv->coords_y[j] - recv->coords_y[i];
            antenna_differences_z[k] = recv->coords_z[j] - recv->coords_z[i];
                    k++;
        }
    }
    for( i = 0; i < buf->num_baselines; i++)
    {
        (buf->uu[i]) = ha_sin*antenna_differences_x[i]
              + ha_cos*antenna_differences_y[i];
        (buf->vv[i]) = -dec_sin*ha_cos*antenna_differences_x[i]
              + dec_sin*ha_sin*antenna_differences_y[i]
              + dec_cos*antenna_differences_z[i];
        (buf->ww[i]) = dec_cos*ha_cos*antenna_differences_x[i]
              + dec_cos*ha_sin*antenna_differences_y[i]
              + dec_sin*antenna_differences_z[i];
    }

    free(antenna_differences_x);
    free(antenna_differences_y);
    free(antenna_differences_z);
}
