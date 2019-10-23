#ifdef __linux__
#  define _GNU_SOURCE
#  include <sched.h>
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <getopt.h>

#include "receiver.h"
#ifdef WITH_MS
#include "write_ms_access.h"
#endif

static char* construct_output_root(const char* output_location,
                                   const char* output_name)
{
    if (!output_location || strlen(output_location) == 0) return 0;
    const size_t len = 10 + strlen(output_location) + strlen(output_name) + 3;
    char* output_root = (char*) calloc(len, sizeof(char));
    const time_t unix_time = time(NULL);
    struct tm* timeinfo = localtime(&unix_time);
    snprintf(output_root, len, "%s/%s_%.2d%.2d%.2d.ms",
             output_location, output_name,
             timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec);
    printf("Writing output to: %s\n", output_root);
    return output_root;
}

int main(int argc, char** argv)
{
    int num_streams = 1;
    int num_threads_recv = num_streams;
    int num_threads_write = 1;
    int num_times_in_buffer = 50;
    int max_num_buffers = 4;
    int num_channels_per_file = 1;
    double ra = 0;
    double dec = 0;

//    int write_autocorr = 0;
//    int write_crosscorr = 1;
//    int num_stations = 3;
    int opt;
    unsigned int timeout = 5;
    unsigned short int port_start = 41000;
//    double ref_freq_hz = 100e6;
//    double freq_inc_hz = 100e3;
    const int num_cores = sysconf(_SC_NPROCESSORS_ONLN);
    const char* output_location = 0;
    const char* output_name = "vis_recv";
//#ifdef WITH_MS
//    oskar_MeasurementSet* ms;
//#endif
    while(1) {

        static struct option lopts[] =
        {
            {"streams", required_argument, 0, 's'},
            {"recv", required_argument, 0, 'r'},
            {"write", required_argument, 0, 'w'},
            {"buffers", required_argument, 0, 'b'},
            {"buffertimes", required_argument, 0, 't'},
            {"port", required_argument, 0, 'p'},
            {"channels", required_argument, 0, 'c'},
            {"output", required_argument, 0, 'o'},
            {"expire", required_argument, 0, 'e'},
            {"declination", optional_argument, 0, 'd'},
            {"ascension", optional_argument, 0, 'a'}
        };
        int opt_index = 0;
        opt = getopt_long(argc, argv, "s:r:w:b:t:p:c:o:e:d:a:", lopts, &opt_index);
        if(opt == -1)
            break;
        switch(opt){
            case 's':
                num_streams = (atoi(optarg) < 1) ? 1 : atoi(optarg);
                break;
            case 'r':
                num_threads_recv = (atoi(optarg) < 1) ? 1 : atoi(optarg);
                break;
            case 'w':
                num_threads_write = (atoi(optarg) < 1) ? 1 : atoi(optarg);
                break;
            case 'b':
                num_times_in_buffer = (atoi(optarg) < 1) ? 1 : atoi(optarg);
                break;
            case 't':
                max_num_buffers = (atoi(optarg) < 1) ? 1 : atoi(optarg);
                break;
            case 'p':
                port_start = atoi(optarg);
                break;
            case 'c':
                num_channels_per_file = (atoi(optarg) < 1) ? 1 : atoi(optarg);
                break;
            case 'o':
                output_location = optarg;
                break;
            case 'e':
                timeout = atoi(optarg);
                break;
            case 'd':
                dec = atof(optarg);
                break;
            case 'a':
                ra = atof(optarg);
                break;
            default:
                abort();
        }
    }
    printf("Running RECV_VERSION %s\n", RECV_VERSION);
    char* output_root = construct_output_root(output_location, output_name);
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
    printf(" + Maximum number of buffers   : %d\n", max_num_buffers);
    printf(" + UDP port range              : %d-%d\n",
           (int) port_start, (int) port_start + num_streams - 1);
    printf(" + Number of channels per file : %d\n", num_channels_per_file);
    printf(" + Output root                 : %s\n", output_root);

    // Create and start the receiver.
    struct Receiver* receiver = receiver_create(
            max_num_buffers, num_times_in_buffer, num_threads_recv,
            num_threads_write, num_streams, port_start,
            num_channels_per_file, output_root);
    receiver_start(receiver);

//#ifdef WITH_MS
//    ms = open_ms(oms_file_name);
//    /* Create the empty Measurement Set if it doesn't exist. */
//    if(ms == 0)
//    {
//        printf("MS file: error opening %s, doesn't exist or unreadable, "
//               "creating one instead.\n", oms_file_name);
//        ms = create_ms(oms_file_name, "C test main",
//                       num_stations, 1, 4, ref_freq_hz, freq_inc_hz,
//                       write_autocorr, write_crosscorr);
//        if(ms == 0)
//        {
//            printf("Error creating MS file: %s\n", oms_file_name);
//            return -1;
//        }
//    }
//    struct Buffer** buf = malloc(sizeof(struct Buffer)*num_buffers);
//    for (int i = 0; i < num_buffers; i++){
//        buf[i] = receiver->buffers[i];
//        buf[i]->vis_data = receiver->buffers[i]->vis_data;
//        write_ms(ms, i, 4, buf[i]->num_channels, buf[i]->num_times,
//                 buf[i]->num_baselines, &(buf[i]->vis_data));
//    }
//    close_ms(ms);
//#endif

    receiver_free(receiver);
    free(output_root);
    return 0;
}
