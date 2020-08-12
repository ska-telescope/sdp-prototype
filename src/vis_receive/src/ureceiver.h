 #ifndef RECV_URECEIVER_H_
#define RECV_URECEIVER_H_

#include <liburing.h>
#include <sys/uio.h>


#ifdef __cplusplus
extern "C" {
#endif


#define READ_SZ                 8192
#define EVENT_TYPE_READ         0
#define EVENT_TYPE_WRITE        1
#define NUM_READS_IN_RING       10


struct request 
{
    int event_type;
    int iovec_count;
    int client_socket;
    int stream_id;
    struct iovec iov[];
};

struct uReceiver
{
    struct Timer* tmr;
    struct uStream** streams;

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
    struct io_uring* rings;
    int write_to_file; 
};

struct uReceiver* ureceiver_create(int num_stations, int num_streams, unsigned short int port_start, int write_to_file);

void ureceiver_start(struct uReceiver* self);
void ureceiver_free(struct uReceiver* self);

//int add_read_request(struct uStream* stream, struct io_uring* ring);
int add_read_request(struct uStream* stream, struct io_uring* ring, struct request* req);
int add_write_request(struct uStream* stream, struct io_uring* ring, void* iov_base, int bytes, int offset);
int handle_packet(struct request *req, struct uStream* stream);
void free_request(struct request *req);
/* main io_uring handling loop */


#ifdef __cplusplus
}
#endif

#endif
