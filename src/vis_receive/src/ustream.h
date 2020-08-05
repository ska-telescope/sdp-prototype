#ifndef RECV_USTREAM_H_
#define RECV_USTREAM_H_

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif


struct Timer;
struct uReceiver;

struct uStream
{
    unsigned char* socket_buffer; 
    int file_descriptor;           // for output to file 
    struct uReceiver* receiver;
    struct Timer *tmr_memcpy;
    size_t dump_byte_counter, recv_byte_counter, vis_data_heap_offset;
    int buffer_len, done, heap_count, socket_handle, stream_id;
    unsigned short int port;
    int write_to_file;
};

struct uStream* ustream_create(unsigned short int port, int stream_id,
        struct uReceiver* receiver, int write_to_file);

int ustream_decode(struct uStream* stream, const unsigned char* buf, int depth);

void ustream_free(struct uStream* self);

#ifdef __cplusplus
}
#endif

#endif /* include guard */

