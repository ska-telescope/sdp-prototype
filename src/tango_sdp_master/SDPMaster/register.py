# coding: utf-8
"""Register the SDPMaster device(s) with the Tango Db."""
import argparse
from tango import Database, DbDevInfo


def delete_server(server_name):
    """Delete the specified device server."""
    tango_db = Database()
    if server_name in list(tango_db.get_server_list(server_name)):
        print('- Removing device server: {}'.format(server_name))
        tango_db.delete_server(server_name)


def register_master(server_name, class_name):
    """Register master device."""
    tango_db = Database()
    device_info = DbDevInfo()

    # pylint: disable=protected-access
    device_info._class = class_name
    device_info.server = server_name

    device_info.name = 'mid_sdp/elt/master'
    print("- Registering device: {}, class: {}, server: {}"
          .format(device_info.name, class_name, server_name))
    tango_db.add_device(device_info)


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(
        description='SDPMaster device registration')
    PARSER.add_argument('--delete', action='store_true',
                        help='Delete the device server and exit')
    ARGS = PARSER.parse_args()
    SERVER = 'SDPMaster/1'
    CLASS = 'SDPMaster'

    if ARGS.delete:
        delete_server(SERVER)
    else:
        delete_server(SERVER)
        register_master(SERVER, CLASS)
