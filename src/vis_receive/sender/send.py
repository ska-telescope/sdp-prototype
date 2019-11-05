# -*- coding: utf-8 -*-
"""Sends test data using spead2."""

import time
import sys
import numpy

import spead2
import spead2.send

def read_coordinates(antenna_file):
    coords    = []
    with open(antenna_file) as file:
        for line in file:
            if(line[0] != '#'):
                coords.append(line.split())
    return(coords)

def main():
    """Runs the test sender."""
    num_stations = 4
    num_heaps = 1500
    num_streams = 1
    rate = 1.0e5   # Bytes/s
    target = ('127.0.0.1' if len(sys.argv) < 2 else sys.argv[1])
    target_port = int('41000' if len(sys.argv) < 3 else sys.argv[2])
    antenna_file = ('' if len(sys.argv) < 4 else sys.argv[3])

    if(len(antenna_file) > 1):
        coords = read_coordinates(antenna_file)
        num_stations = len(coords)

    num_baselines = (num_stations * (num_stations + 1)) // 2

    print(f'no. stations      : {num_stations}')
    print(f'no. baselines     : {num_baselines}')
    print(f'no. times (heaps) : {num_heaps}')
    print(f'host              : {target}')
    print(f'port              : {target_port}')

    stream_config = spead2.send.StreamConfig(
        max_packet_size=16356, rate=rate, burst_size=10, max_heaps=1)
    item_group = spead2.send.ItemGroup(flavour=spead2.Flavour(4, 64, 48, 0))

    # Add item descriptors to the heap.
    dtype = [('TCI', 'i1'), ('FD', 'u1'), ('VIS', '<c8', 4)]
    item_group.add_item(
        id=0x6000, name='visibility_timestamp_count', description='',
        shape=tuple(), format=None, dtype='<u4')
    item_group.add_item(
        id=0x6001, name='visibility_timestamp_fraction', description='',
        shape=tuple(), format=None, dtype='<u4')
    item_group.add_item(
        id=0x6002, name='visibility_channel_id', description='',
        shape=tuple(), format=None, dtype='<u4')
    item_group.add_item(
        id=0x6003, name='visibility_channel_count', description='',
        shape=tuple(), format=None, dtype='<u4')
    item_group.add_item(
        id=0x6004, name='visibility_polarisation_id', description='',
        shape=tuple(), format=None, dtype='<u4')
    item_group.add_item(
        id=0x6005, name='visibility_baseline_count', description='',
        shape=tuple(), format=None, dtype='<u4')
    item_group.add_item(
        id=0x6008, name='scan_id', description='',
        shape=tuple(), format=None, dtype='<u8')
    item_group.add_item(
        id=0x600A, name='correlator_output_data', description='',
        shape=(num_baselines,), dtype=dtype)

    # Create streams and send start-of-stream message.
    streams = []
    for i in range(num_streams):
        port = target_port + i
        print("Sending to {}:{}".format(target, port))
        stream = spead2.send.UdpStream(
            thread_pool=spead2.ThreadPool(threads=1),
            hostname=target, port=port, config=stream_config)
        stream.send_heap(item_group.get_start())
        streams.append(stream)

    vis = numpy.zeros(shape=(num_baselines,), dtype=dtype)
    vis_amps = numpy.arange(num_baselines*4, dtype='c8').reshape(
        (num_baselines, 4)) / 1000.0
    start_time = time.time()
    for stream in streams:
        # Update values in the heap.
        item_group['visibility_timestamp_count'].value = 1
        item_group['visibility_timestamp_fraction'].value = 0
        item_group['visibility_baseline_count'].value = num_baselines
        item_group['visibility_channel_id'].value = 12345
        item_group['visibility_channel_count'].value = 0
        item_group['visibility_polarisation_id'].value = 0
        item_group['scan_id'].value = 100000000
        item_group['correlator_output_data'].value = vis
        # Iterate heaps.
        for i in range(num_heaps):
            item_group['correlator_output_data'].value['VIS'] = vis_amps + i
            # Send heap.
            stream.send_heap(item_group.get_heap(descriptors='all', data='all'))

    # Print time taken.
    duration = time.time() - start_time
    data_size = num_streams * num_heaps * (vis.nbytes / 1e6)
    print("Sent %.3f MB in %.3f sec (%.3f MB/sec)" % (
        data_size, duration, (data_size/duration)))

    # Send end-of-stream message.
    for stream in streams:
        stream.send_heap(item_group.get_end())


if __name__ == '__main__':
    main()
