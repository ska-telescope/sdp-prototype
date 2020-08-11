#ifdef __linux__
#  define _GNU_SOURCE
#  include <sched.h>
#endif

#ifdef WITH_MS
#   include <oskar_measurement_set.h>
#endif

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "receiver.h"
#include "log.h"
#include "ureceiver.h"
#include "ustream.h"
#include "timer.h"

#include <liburing.h>
#include <sys/uio.h>



static unsigned int rqueue = 0;
static unsigned int wqueue = 0;

struct uThreadArg
{
    int thread_id;
    struct uReceiver* receiver;
    //struct uStream* stream;
    //struct io_uring ring;
};


struct uReceiver* ureceiver_create(int num_stations, int num_streams, unsigned short int port_start, int write_to_file) {
    struct uReceiver* receiver = (struct uReceiver*) calloc(1, sizeof(struct uReceiver));

    receiver->tmr = tmr_create();
    receiver->streams = (struct uStream**) calloc(num_streams, sizeof(struct uStream*));
    for (int i = 0; i < num_streams; i++) {
        receiver->streams[i] = ustream_create(port_start + (unsigned short int) i, i, receiver, write_to_file);
    }

    receiver->port_start = port_start;
    receiver->num_stations = num_stations;
    receiver->num_streams = num_streams;
      
    receiver->antennas = calloc(1, sizeof(struct Antenna));

    receiver->rings = (struct io_uring*) calloc(num_streams, sizeof(struct io_uring));
    for (int s = 0; s < num_streams; s++){
        io_uring_queue_init(NUM_READS_IN_RING, &receiver->rings[s], 0);
    }
    receiver->write_to_file = write_to_file;

    return receiver;
}



void ureceiver_start(struct uReceiver* self) {
    //struct io_uring_cqe *cqe;
    //io_uring_queue_init(QUEUE_DEPTH, &ring, 0); // this is now done in the creation step

    /* we have control over the number of reads we put in the queue */ 
    /* we hard code a number defined in receiver.h */
/*    for (int s = 0; s < self->num_streams; s++){
        for (int i = 0; i < NUM_READS_IN_RING; i++) {
            LOG_DEBUG(0, "adding read request #%d to ring #%d", i, s);
            add_read_request(self->streams[s], &self->rings[s]);
            rqueue++;
        }
    }
*/
                
    /* main io_uring based server loop */

    /* each stream gets its own receive thread */
    pthread_attr_t attr; 
    pthread_attr_init(&attr);
    pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_JOINABLE);
    pthread_t* threads = (pthread_t*) malloc(self->num_streams * sizeof(pthread_t));
    struct uThreadArg* args =
        (struct uThreadArg*) malloc(self->num_streams * (sizeof(struct uThreadArg)));


    for (int i = 0; i < self->num_streams; i++) {
        args[i].thread_id = i;
        args[i].receiver = self;
        //args[i].stream = self->streams[i];
        //args[i].ring = self->rings[i];
      
        //args[i].stream->stream_id = i;

        pthread_create(&threads[i], &attr, &handle_uring, &args[i]);
    }


    for (int i = 0; i < self->num_streams; i++){
        pthread_join(threads[i], NULL);
    }
    pthread_attr_destroy(&attr);
    free(args);
    free(threads);
}

static void* handle_uring(void* arg) {
    struct uThreadArg* thread_args = (struct uThreadArg*) arg;
    struct uReceiver* receiver = thread_args->receiver;
    int thread_id = thread_args->thread_id;
    struct uStream* stream = thread_args->receiver->streams[thread_id];
    struct io_uring ring = thread_args->receiver->rings[thread_id];

    int wqueue, rqueue = 0;
    int bytes, offset = 0;
    struct io_uring_cqe *cqe;

    for (int i = 0; i < NUM_READS_IN_RING; i++) {
        //LOG_DEBUG(0, "creating read request %d in ring %d", i, thread_args->thread_id);
        add_read_request(stream, &ring);
        rqueue++;
    }

    while (stream) {
        /* now wait for completed read requests and handle them as they come in */
        /* exit the loop when the stream is closed */
        int ret = io_uring_wait_cqe(&ring , &cqe);

        if (ret < 0) {
            LOG_ERROR(0, "io_uring_wait_cqe returned < 0");
                perror("io_uring_wait_cqe");
        }

        if (cqe->res < 0) {
            if (cqe->res == -EAGAIN) {
                struct request *req = (struct request *) cqe->user_data;
                if (req->event_type == EVENT_TYPE_READ){
                    add_read_request(stream, &ring);
                } else if (req->event_type == EVENT_TYPE_WRITE){
                    add_write_request(stream, &ring, req->iov->iov_base, req->iov->iov_len, offset);
                    
                } else {
                    LOG_ERROR(0,"UNKNOWN EVENT TYPE");
                    exit(1);
                }

                io_uring_cqe_seen(&ring, cqe);
                //LOG_DEBUG(0, "resubmitting cqe. Current queue depth: %u\n",queue);
                continue;   
            } else {
                LOG_ERROR(0, "cqe->res returned < 0");
                LOG_ERROR(0, "output is %d", cqe->res);
                perror("cqe->res failed with: ");
                exit(1);
            }
        }

        struct request *req = (struct request *) cqe->user_data;

        if (req->event_type == EVENT_TYPE_READ) {
            rqueue--;
            bytes = handle_packet(req, stream);
            /* mark this request as handled */

            if (stream->write_to_file) {
                // add write request
                add_write_request(stream, &ring, req->iov->iov_base, bytes, offset);
                wqueue++;
            } else {
                // we don't write, so add read request to keep ring filled
                add_read_request(stream, &ring);
                rqueue++;
            }
            io_uring_cqe_seen(&ring, cqe);

        } else if (req->event_type == EVENT_TYPE_WRITE) {
            wqueue--;
            offset += cqe->res;
            //LOG_DEBUG(0, "offset now: %d", offset)
            if (cqe->res != req->iov->iov_len) {
                LOG_WARN(0, "cqe->res != req->iov->iov_len:: %d != %d", cqe->res, req->iov->iov_len);   
                // short write, requeue with adjusted values
                req->iov->iov_base += cqe->res;
                req->iov->iov_len -= cqe->res;
                add_write_request(stream, &ring, req->iov->iov_base, req->iov->iov_len, offset);
                wqueue++;
            } else {
                //handle_write_event(req, stream);
                io_uring_cqe_seen(&ring, cqe);
                add_read_request(stream, &ring);
                rqueue++;
            }
        }
        /* the read request was handled, add a new one to keep queue filled */
/*         add_read_request(stream, &ring);
        rqueue++;*/    
    } 
    return 0;
}

void ureceiver_free(struct uReceiver* self) {
    if (!self) return;
    tmr_free(self->tmr);
    
    for (int i = 0; i < self->num_streams; i++) ustream_free(self->streams[i]);
    for (int i = 0; i < self->num_streams; i++) io_uring_queue_exit(&self->rings[i]);
    
    free(self->streams);
    free(self->rings);
    free(self);
}

int add_read_request(struct uStream* stream, struct io_uring* ring) {

    //LOG_DEBUG(0, "stream pointer: 0x%08x, ring pointer 0x%08x", stream, ring);

    struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
    struct request *req = malloc(sizeof(*req) + sizeof(struct iovec));
    req->iov[0].iov_base = malloc(READ_SZ);
    req->iov[0].iov_len = READ_SZ;
    req->event_type = EVENT_TYPE_READ;
    req->client_socket = stream->socket_handle;
    memset(req->iov[0].iov_base, 0, READ_SZ);
    /* Linux kernel 5.5 has support for readv, but not for recv() or read() */
    io_uring_prep_readv(sqe, req->client_socket, &req->iov[0], 1, 0);
    io_uring_sqe_set_data(sqe, req);
    io_uring_submit(ring);

    return 0;
}


int add_write_request(struct uStream *stream, struct io_uring* ring, void* iov_base, int bytes, int offset){

    struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
    struct request *req = malloc(sizeof(*req) + sizeof(struct iovec));

    // LOG_INFO(0, "write request for %d bytes", bytes);
    req->iov[0].iov_base = iov_base;// malloc(bytes);
    req->iov[0].iov_len = bytes;
    req->event_type = EVENT_TYPE_WRITE ;
    req->client_socket = stream->file_descriptor;
    // memset(req->iov[0].iov_base, 0, bytes);
    //memcpy(req->iov[0].iov_base, iov_base, bytes);


    io_uring_prep_writev(sqe, req->client_socket, &req->iov[0], 1, offset);
    io_uring_sqe_set_data(sqe, req);
    io_uring_submit(ring);

    return 0;
}

int handle_write_event(struct request *req, struct uStream* stream) {
    /* probably a NOP, everything is already done in the io_uring queue */
    return 0;

}


int handle_packet(struct request *req, struct uStream* stream) {
#if 0
    printf("Printing content buffer, length = %d.\n", req->iov[0].iov_len);

    for (size_t i = 0; i < req->iov[0].iov_len; i++) {
        char* c = (char*) (req->iov[0].iov_base + i);
        printf(c);
    }
    printf("\ndone\n");
#endif

    int offset = 0;
    //while ((req->iov[0].iov_len - offset) >= 8) {
    while (offset <= 8) {

        int bytes_decoded = ustream_decode(stream, (unsigned char*) req->iov[0].iov_base + offset, 0);
        //offset += bytes_decoded;
        offset = bytes_decoded;
        if ( bytes_decoded > 8 ) printf("stream %d, message length: %ld, bytes decoded: %d, read queue depth: %u, write queue depth: %u\n", stream->stream_id, req->iov[0].iov_len, bytes_decoded, rqueue, wqueue);
        
    }

    return offset;
}
