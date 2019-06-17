#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Tango device server for use with scaling tests."""
import sys
import time
import argparse

import tango
from tango.server import run


from TestDevice import TestDevice


def init_callback():
    """Callback called post server initialisation."""
    global START_TIME
    db = tango.Database()
    elapsed = time.time() - START_TIME
    list_devices()
    exported_devices = list(db.get_device_exported('test/*'))
    num_devices = len(exported_devices)
    file = open('results.txt', 'a')
    file.write(',{},{}\n'.format(elapsed, elapsed / num_devices))
    print('>> Time taken to start devices: {:.4f} s ({:.4f} s/dev)'
          .format(elapsed, elapsed / num_devices))


def delete_server():
    """."""
    db = tango.Database()
    db.set_timeout_millis(50000)
    server = 'TestDeviceServer/1'

    server_list = list(db.get_server_list(server))

    if server in server_list:
        start_time = time.time()
        db.delete_server('TestDeviceServer/1')
        print('- Delete server: {:.4f} s'.format(time.time() - start_time))


def register(num_devices):
    """."""
    db = tango.Database()
    device_info = tango.DbDevInfo()

    device_info.server = 'TestDeviceServer/1'
    device_info._class = 'TestDevice'

    start_time = time.time()
    for device_id in range(num_devices):
        device_info.name = 'test/test_device/{:05d}'.format(device_id)
        db.add_device(device_info)
    elapsed = time.time() - start_time
    file = open('results.txt', 'a')
    file.write('{},{},{}'.format(num_devices, elapsed, elapsed/num_devices))
    print('- Register devices: {:.4f} s ({:.4f} s/device)'
          .format(elapsed, elapsed / num_devices))


def list_devices():
    """."""
    db = tango.Database()
    server_instance = 'TestDeviceServer/1'
    device_class = 'TestDevice'
    devices = list(db.get_device_name(server_instance, device_class))
    print('- No. registered devices: {}'.format(len(devices)))

    exported_devices = list(db.get_device_exported('test/*'))
    print('- No. running devices: {}'.format(len(exported_devices)))


def main(args=None, **kwargs):
    run([TestDevice], verbose=True, msg_stream=sys.stdout,
        post_init_callback=init_callback, raises=False,
        args=args, **kwargs)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Device registration time.')
    parser.add_argument('num_devices', metavar='N', type=int,
                        default=1, nargs='?',
                        help='Number of devices to start.')
    args = parser.parse_args()
    delete_server()
    time.sleep(0.5)

    list_devices()
    print('* Registering {} devices'.format(args.num_devices))

    register(args.num_devices)

    list_devices()

    print('* Starting server ...')
    sys.argv = ['TestDeviceServer', '1', '-v4']
    START_TIME = time.time()
    main()
