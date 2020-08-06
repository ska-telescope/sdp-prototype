#include <fcntl.h>
#include <inttypes.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#include "log.h"
#include "ureceiver.h"
#include "ustream.h"
#include "timer.h"

typedef unsigned char uchar;

struct uStream* ustream_create(unsigned short int port, int stream_id, struct uReceiver* receiver, int write_to_file) {

    struct uStream* cls = (struct uStream*) calloc(1, sizeof(struct uStream));
    const int requested_buffer_len = 16*1024*1024;
    cls->buffer_len = requested_buffer_len;
    cls->port = port;
    cls->receiver = receiver;
    cls->stream_id = stream_id;
    cls->write_to_file = write_to_file;
    
    if ((cls->socket_handle = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
    {
        LOG_CRITICAL(0, "Cannot create socket.");
        return cls;
    }
    fcntl(cls->socket_handle, F_SETFL, O_NONBLOCK);

    /* 
       allow reuse of the socket/address combination should the application crash and not close 
       the socket properly
    */
    if (setsockopt(cls->socket_handle, SOL_SOCKET, SO_REUSEADDR, &(int){1}, sizeof(int)) < 0) { 
        perror("setsockopt SO_REUSEADDR failed with ");
        exit(1);
    }

    /* This works on my machine, but may be non-standard */
    if (setsockopt(cls->socket_handle, SOL_SOCKET, SO_REUSEPORT, &(int){1}, sizeof(int)) < 0) { 
        perror("setsockopt SO_REUSEPORT failed with ");
        exit(1);
    }

    setsockopt(cls->socket_handle, SOL_SOCKET, SO_RCVBUF, &cls->buffer_len, sizeof(int));

    uint32_t int_size = (uint32_t) sizeof(int);
    getsockopt(cls->socket_handle, SOL_SOCKET, SO_RCVBUF, &cls->buffer_len, &int_size);
    if ((cls->buffer_len / 2) < requested_buffer_len)
    {
        LOG_WARN(0,
                "Requested socket buffer of %d bytes; actual size is %d bytes",
                requested_buffer_len, cls->buffer_len / 2);
    }
    struct sockaddr_in myaddr;
    myaddr.sin_family = AF_INET;
    myaddr.sin_addr.s_addr = htonl(INADDR_ANY);
    myaddr.sin_port = htons(port);
    if (bind(cls->socket_handle, (struct sockaddr*)&myaddr, sizeof(myaddr)) < 0)
    {
        LOG_CRITICAL(0, "Bind failed.");
        perror("bind failed with error: ");
        exit(1);
        return cls;
    }
    cls->socket_buffer = (uchar*) malloc(cls->buffer_len);
    memset(cls->socket_buffer, 0, cls->buffer_len);

    if (write_to_file) {
        char* fbuf = (char*) calloc(32, sizeof(char));
        
        snprintf(fbuf, 32, "output_%d.dat", stream_id);
        cls->file_descriptor=open(fbuf, O_WRONLY | O_CREAT | O_TRUNC, S_IRWXU | S_IRWXG );

        LOG_INFO(0, "file opened with file descriptor %d", cls->file_descriptor);
    }

    return cls;
}

int ustream_decode(struct uStream* stream, const unsigned char* buf, int depth) { 
    /* Extract SPEAD packet headers. */
    const uchar magic = buf[0];
    const uchar version = buf[1];
    const uchar item_id_bits = buf[2] * 8 - 1;
    const uchar heap_address_bits = buf[3] * 8;
    const uchar num_items = buf[7];
    if (magic != 'S' || version != (uchar)4) {
        // LOG_WARN(0, "Did not find magic value in header or version != 4");   
        // printf("magic: %uc; version: %uc", magic, version);
        return 8;
    }
    /* Get pointers to items and payload start. */
    const uint64_t* items = (const uint64_t*) &buf[8];
    const uint64_t mask_addr = (1ull << heap_address_bits) - 1;
    const uint64_t mask_id   = (1ull << item_id_bits) - 1;
    const uchar* payload_start = (const uchar*) &items[num_items];

    /* Heap data. */
    int packet_has_header_data = 0;
    int packet_has_stream_control = 0;
    uint32_t timestamp_count = 0;
    uint32_t timestamp_fraction = 0;
    uint32_t channel_id = 0;
    uint32_t channel_count = 0;
    uint32_t polarisation_id = 0;
    uint64_t scan_id = 0;
    size_t packet_payload_length = 0;
    size_t heap_offset = 0;
    size_t heap_size = 0;
    size_t vis_data_start = 0;

    /* Iterate ItemPointers. */
    for (uchar i = 0; i < num_items; ++i)
    {
        const uint64_t item = be64toh(items[i]);
        /*const uint64_t immediate = item & (1ull << 63);*/
        const uint64_t item_addr = item & mask_addr;
        const uint64_t item_id   = (item >> heap_address_bits) & mask_id;
        switch (item_id)
        {
        case 0x0:
            /* NULL - ignore. */
            break;
        case 0x1:
            /* Heap counter (immediate addressing, big endian). */
            if (depth == 0) stream->heap_count = (int) item_addr - 2;
            break;
        case 0x2:
            /* Heap size (immediate addressing, big endian). */
            heap_size = item_addr;
            break;
        case 0x3:
            /* Heap offset (immediate addressing, big endian). */
            heap_offset = (size_t) item_addr;
            break;
        case 0x4:
            /* Packet payload length (immediate addressing, big endian). */
            packet_payload_length = (size_t) item_addr;
            break;
        case 0x5:
            /* Nested item descriptor (recursive call). */
            /*stream_decode(self, &payload_start[item_addr], depth + 1);*/
            break;
        case 0x6:
            /* Stream control messages (immediate addressing, big endian). */
            packet_has_stream_control = 1;
            if (item_addr == 2) stream->done = 1;
            break;
        case 0x10: /* Item descriptor name     (absolute addressing). */
        case 0x11: /* Item descriptor desc.    (absolute addressing). */
        case 0x12: /* Item descriptor shape    (absolute addressing). */
        case 0x13: /* Item descriptor type     (absolute addressing). */
        case 0x14: /* Item descriptor ID       (immediate addressing). */
        case 0x15: /* Item descriptor DataType (absolute addressing). */
            break;
        case 0x6000:
            /* Visibility timestamp count (immediate addressing). */
            stream->receiver->timestamp_count = be32toh((uint32_t) item_addr);
            packet_has_header_data = 1;
            break;
        case 0x6001:
            /* Visibility timestamp fraction (immediate addressing). */
            timestamp_fraction = be32toh((uint32_t) item_addr);
            packet_has_header_data = 1;
            break;
        case 0x6002:
            /* Visibility channel id (immediate addressing). */
            channel_id = be32toh((uint32_t) item_addr);
            packet_has_header_data = 1;
            break;
        case 0x6003:
            /* Visibility channel count (immediate addressing). */
            channel_count = be32toh((uint32_t) item_addr);
            packet_has_header_data = 1;
            break;
        case 0x6004:
            /* Visibility polarisation id (immediate addressing). */
            polarisation_id = be32toh((uint32_t) item_addr);
            packet_has_header_data = 1;
            break;
        case 0x6005:
            /* Visibility baseline count (immediate addressing). */
            stream->receiver->num_baselines = be32toh((uint32_t) item_addr);
            packet_has_header_data = 1;
            break;
        case 0x6008:
            /* Scan ID (absolute addressing). */
            scan_id = *( (uint64_t*)(payload_start + item_addr) );
            packet_has_header_data = 1;
            break;
        case 0x600A:
            /* Visibility data (absolute addressing). */
            stream->vis_data_heap_offset = (size_t) item_addr;
            vis_data_start = (size_t) item_addr;
            break;
        default:
            /*LOG_DEBUG(0, "Heap %3d  ID: %#6llx, %s: %llu", self->heap_count,
                    item_id, immediate ? "VAL" : "ptr", item_addr);*/
            break;
        }
    }
    if (0 && !packet_has_stream_control)
        LOG_DEBUG(0, "==== Packet in heap %3d "
                "(heap offset %zu/%zu, payload length %zu)", stream->heap_count,
                heap_offset, heap_size, packet_payload_length);
    if (0 && packet_has_header_data)
    {
        LOG_DEBUG(0, "     heap               : %d", stream->heap_count);
        LOG_DEBUG(0, "     timestamp_count    : %" PRIu32, timestamp_count);
        LOG_DEBUG(0, "     timestamp_fraction : %" PRIu32, timestamp_fraction);
        LOG_DEBUG(0, "     scan_id            : %" PRIu64, scan_id);
        LOG_DEBUG(0, "     num_baselines      : %d", stream->receiver->num_baselines);
    }
    if (!packet_has_stream_control && stream->vis_data_heap_offset > 0 &&
            stream->receiver->num_baselines > 0)
    {
        const double timestamp = tmr_get_timestamp();
        const size_t vis_data_length = packet_payload_length - vis_data_start;
        /*LOG_DEBUG(0, "Visibility data length: %zu bytes", vis_data_length);*/
      /*   struct Buffer* buf = receiver_buffer(
                stream->receiver, stream->heap_count, vis_data_length, timestamp);
        if (buf)
        {
            const uchar* src_addr = payload_start + vis_data_start;
            const int i_time = stream->heap_count - buf->heap_id_start;
            const int i_chan = stream->stream_id;
            uchar* dst_addr = ((uchar*) buf->vis_data) +
                    heap_offset - stream->vis_data_heap_offset + vis_data_start +
                    buf->block_size * (i_time * buf->num_channels + i_chan);
            tmr_resume(stream->tmr_memcpy);
            memcpy(dst_addr, src_addr, vis_data_length);
            tmr_pause(stream->tmr_memcpy);
            stream->recv_byte_counter += vis_data_length;
        }
        else
        { */
            stream->dump_byte_counter += vis_data_length;
        /* } */
    }
    return (8 + 8 * num_items) + (int)packet_payload_length;
}


void ustream_free(struct uStream* self){
    if (!self) return;
    close(self->socket_handle);
    free(self->socket_buffer);
    free(self);
}