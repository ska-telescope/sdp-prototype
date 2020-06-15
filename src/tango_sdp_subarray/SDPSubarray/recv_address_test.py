import json
import random


def channel_list(channel_link_map):
    """
    Generate flat list of channels from the channel link map.

    :param channel_link_map: channel link map.
    :returns: list of channels.
    """
    channels = []
    i = 0
    for channel in channel_link_map['channels']:
        i = i+1
        channel = dict(
            numchan=channel['count'],
            startchan=channel['start'],
            scan_type=channel_link_map.get('id'),
            host=i
        )
        channels.append(channel)

    return channels


def minimal_receive_addresses(channels):
    """
    Provide a minimal version of the receive addresses.

    :param channels: list of channels
    :returns: receive addresses
    """

    host_list = []
    port_list = []
    receive_addresses = {}
    for chan in channels:
        host_list.append([chan['startchan'], '192.168.0.{}'.format(chan['host'])])
        port_list.append([chan['startchan'], 9000, 1])
    receive_addresses[chan['scan_type']] = dict(host=host_list, port=port_list)

    return receive_addresses


def generate_receive_addresses(scan_types):
    """
    Generate receive addresses based on channel link map.

    This function generates a minimal fake response.
    :param scan_types: scan types from SB
    :return: receive addresses
    """

    receive_addresses_list = []
    for channel_link_map in scan_types:
        channels = channel_list(channel_link_map)
        receive_addresses_list.append(minimal_receive_addresses(channels))
    return receive_addresses_list


# Main function
with open('test_schema.json', 'r') as myfile:
    data=myfile.read()

obj = json.loads(data)
scan_types = obj['scan_types']
receive_addresses = generate_receive_addresses(scan_types)
# #
print(receive_addresses)

