#ifndef RECV_RECEIVER_H_
#define RECV_RECEIVER_H_

#include <pthread.h>
#include "buffer.h"

#ifdef WITH_MS
#   include <oskar_measurement_set.h>
#endif


#ifdef __cplusplus
extern "C" {
#endif

struct ThreadBarrier;
struct ThreadPool;
struct Timer;
struct Stream;
struct Buffer;
struct Antenna;

/**
 * Receiver data structure
 */
struct Receiver
{
    pthread_mutex_t lock;
    struct ThreadBarrier* barrier;
    struct ThreadPool* pool;
    struct Timer* tmr;
    struct Stream** streams;
    struct Buffer** buffers;
    struct Antenna* antennas;
    char* output_root;
    char** name;
    int completed_streams;
    int num_baselines;
    int num_times_in_buffer;
    int max_num_buffers;
    int num_threads_recv;
    int num_threads_write;
    int num_streams;
    int num_buffers;
    int num_channels_per_file;
    int num_stations;
    unsigned short int port_start;
    unsigned int timestamp_count;
    double ra;
    double dec;
    double* coords_x;
    double* coords_y;
    double* coords_z;
    double* diam;
#ifdef WITH_MS
    int write_counter;
    oskar_MeasurementSet* ms;
#endif
};

struct Antenna
{
    int count;
    double* coords_x;
    double* coords_y;
    double* coords_z;
    double* size;
    char** name;
};

/**
 * @brief Returns a handle to the buffer to use for the specified heap.
 */
struct Buffer* receiver_buffer(struct Receiver* self, int heap, size_t length,
        double timestamp);

/**
 * @brief Creates a new receiver object.
 */
struct Receiver* receiver_create(int num_stations, int max_num_buffers,
        int num_times_in_buffer, int num_threads_recv, int num_threads_write,
        int num_streams, unsigned short int port_start,
        int num_channels_per_file, const char* output_root);

/**
 * @brief Destroys the receiver object.
 */
void receiver_free(struct Receiver* self);

/**
 * @brief Activates the receiver and blocks until all streams have finished.
 */
void receiver_start(struct Receiver* self);

void receiver_set_phase(struct Receiver* self, double ra, double dec);

void calculate_uvw(struct Buffer* self);

#ifdef __cplusplus
}
#endif

#endif /* include guard */
