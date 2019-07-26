#ifdef __linux__
#  define _GNU_SOURCE
#  include <sched.h>
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "receiver.h"
#ifdef WITH_MS
#include "write_ms_access.h"
#endif

static char* construct_output_root(const char* output_location,
        const char* output_name)
{
    if (!output_location || strlen(output_location) == 0) return 0;
    const size_t len = 10 + strlen(output_location) + strlen(output_name);
    char* output_root = (char*) calloc(len, sizeof(char));
    const time_t unix_time = time(NULL);
    struct tm* timeinfo = localtime(&unix_time);
    snprintf(output_root, len, "%s/%s_%.2d%.2d%.2d",
            output_location, output_name,
            timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec);
    return output_root;
}

int main(int argc, char** argv)
{
    int num_streams = 1, num_threads_recv = 1, num_threads_write = 8;
    int num_times_in_buffer = 8, num_buffers = 2, num_channels_per_file = 1;
    int write_autocorr = 0, write_crosscorr = 1;
    int num_stations = 3;
    unsigned short int port_start = 41000;
    double ref_freq_hz = 100e6;
    double freq_inc_hz = 100e3;
    const char* output_location = 0;
    const char* output_name = "ingest";
    const char* oms_file_name = "test_ms";
    oskar_MeasurementSet* ms;
    if (argc > 1) num_streams = atoi(argv[1]);
    if (argc > 2) num_threads_recv = atoi(argv[2]);
    if (argc > 3) num_threads_write = atoi(argv[3]);
    if (argc > 4) num_times_in_buffer = atoi(argv[4]);
    if (argc > 5) num_buffers = atoi(argv[5]);
    if (argc > 6) port_start  = (unsigned short int) atoi(argv[6]);
    if (argc > 7) num_channels_per_file = atoi(argv[7]);
    if (argc > 8) output_location = argv[8];
    if (num_streams < 1) num_streams = 1;
    if (num_threads_recv < 1) num_threads_recv = 1;
    if (num_threads_write < 1) num_threads_write = 1;
    if (num_times_in_buffer < 1) num_times_in_buffer = 1;
    if (num_buffers < 1) num_buffers = 1;
    if (num_channels_per_file < 1) num_channels_per_file = 1;
    printf("Running RECV_VERSION %s\n", RECV_VERSION);
    char* output_root = construct_output_root(output_location, output_name);
    const int num_cores = sysconf(_SC_NPROCESSORS_ONLN);
    if (num_threads_recv > num_cores - 2) num_threads_recv = num_cores - 2;
#ifdef __linux__
    cpu_set_t my_set;
    CPU_ZERO(&my_set);
    for (int i = 0; i < num_cores / 2; i++)
    {
        CPU_SET(i, &my_set);
    }
    sched_setaffinity(0, sizeof(cpu_set_t), &my_set);
#endif
    printf(" + Number of system CPU cores  : %d\n", num_cores);
    printf(" + Number of SPEAD streams     : %d\n", num_streams);
    printf(" + Number of receiver threads  : %d\n", num_threads_recv);
    printf(" + Number of writer threads    : %d\n", num_threads_write);
    printf(" + Number of times in buffer   : %d\n", num_times_in_buffer);
    printf(" + Maximum number of buffers   : %d\n", num_buffers);
    printf(" + UDP port range              : %d-%d\n",
            (int) port_start, (int) port_start + num_streams - 1);
    printf(" + Number of channels per file : %d\n", num_channels_per_file);
    printf(" + Output root                 : %s\n", output_root);
    struct Receiver* receiver = receiver_create(num_buffers,
            num_times_in_buffer, num_threads_recv, num_threads_write,
            num_streams, port_start, num_channels_per_file, output_root);
    receiver_start(receiver);
#ifdef WITH_MS
    ms = open_ms(oms_file_name);
    /* Create the empty Measurement Set if it doesn't exist. */
    if(ms == 0)
    {
        printf("MS file: %s doesn't exist, creating one instead.\n", oms_file_name);
        ms = create_ms(oms_file_name, "C test main",
                num_stations, 1, 4, ref_freq_hz, freq_inc_hz,
                write_autocorr, write_crosscorr);
        if(ms == 0)
        {
            printf("Error creating MS file: %s\n", oms_file_name);
            return -1;
        }
    }	
    struct Buffer** buf = malloc(sizeof(struct Buffer)*num_buffers);
    for (int i = 0; i<num_buffers; i++){
        buf[i] = receiver->buffers[i];
        buf[i]->vis_data = receiver->buffers[i]->vis_data;
//        printf("%d %d\n",buf[i]->num_channels, receiver->buffers[i]->vis_data[1]->tci);
        write_ms(ms, 4, buf[i]->num_channels, buf[i]->num_times, buf[i]->num_baselines, 8, buf[i]->vis_data );
    }
    close_ms(ms);
#endif
    receiver_free(receiver);
    free(output_root);
    return 0;
}
