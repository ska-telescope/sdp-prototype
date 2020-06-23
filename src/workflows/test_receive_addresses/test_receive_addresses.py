"""
Workflow to test generation of receive addresses.

The purpose of this workflow is to test the mechanism for generating SDP
receive addresses from the channel link map for each scan type which is
contained in the list of scan types in the SB. The workflow picks it up
from there, uses it to generate the receive addresses for each scan type
and writes them to the processing block state. It consists of a map
of scan type to a receive address map. This address map get publishes to
the appropriate attribute once the SDP subarray finishes the transition
following AssignResources.

This workflow does not generate any deployments.
"""

import sys
import logging
import signal
import ska_sdp_config
import random

logging.basicConfig()
LOG = logging.getLogger('test_receive_addresses')
LOG.setLevel(logging.DEBUG)


def channel_list(channel_link_map):
    """
    Generate flat list of channels from the channel link map.

    :param channel_link_map: channel link map.
    :returns: list of channels.
    """
    channels = []
    i = 0
    for channel in channel_link_map['channels']:
        host_incr = i+1
        channel = dict(
            numchan=channel['count'],
            startchan=channel['start'],
            scan_type=channel_link_map.get('id'),
            host=host_incr
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

    receive_addresses_dict = {}
    for channel_link_map in scan_types:
        channels = channel_list(channel_link_map)
        receive_addresses_dict.update(minimal_receive_addresses(channels))

    return receive_addresses_dict


def main(argv):
    """Main loop."""
    # Get processing block ID from first argument
    pb_id = argv[0]

    # Get connection to config DB
    LOG.info('Opening connection to config DB')
    config = ska_sdp_config.Config()

    # Claim processing block
    for txn in config.txn():
        txn.take_processing_block(pb_id, config.client_lease)
        pb = txn.get_processing_block(pb_id)
    LOG.info('Claimed processing block %s', pb_id)

    sb_id = pb.sbi_id
    LOG.info('SB id: %s', sb_id)

    # Set status to WAITING
    LOG.info('Setting status to WAITING')
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        state['status'] = 'WAITING'
        txn.update_processing_block_state(pb_id, state)

    # Wait for resources to be available
    LOG.info('Waiting for resources to be available')
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        ra = state.get('resources_available')
        if ra is None or not ra:
            txn.loop(wait=True)

    # Set status to RUNNING
    LOG.info('Setting status to RUNNING')
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        state['status'] = 'RUNNING'
        txn.update_processing_block_state(pb_id, state)

    # Get the channel link map from SB
    LOG.info("Retrieving channel link map from SB")
    for txn in config.txn():
        sb = txn.get_scheduling_block(sb_id)
        sb_scan_types = sb.get('scan_types')

    # Generate receive addresses
    LOG.info("Generating receive addresses")
    receive_addresses = generate_receive_addresses(sb_scan_types)

    # Update receive addresses in processing block state
    LOG.info("Updating receive addresses in processing block state")
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        state['receive_addresses'] = receive_addresses
        txn.update_processing_block_state(pb_id, state)

    # Adding pb_id in pb_receive_address in SB
    LOG.info("Adding PB ID to pb_receive_addresses in SB")
    for txn in config.txn():
        sb = txn.get_scheduling_block(sb_id)
        sb['pb_receive_addresses'] = pb_id
        txn.update_scheduling_block(sb_id, sb)

    # ... Do some processing here ...

    # Wait until ReleaseResources command is received.
    LOG.info('Waiting for SB to end')
    for txn in config.txn():
        sb = txn.get_scheduling_block(sb_id)
        if sb.get('status') == 'FINISHED':
            LOG.info('SB has ended')
            break
        txn.loop(wait=True)

    # Set state to indicate processing is finished
    LOG.info('Setting status to FINISHED')
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        state['status'] = 'FINISHED'
        txn.update_processing_block_state(pb_id, state)

    # Close connection to config DB
    LOG.info('Closing connection to config DB')
    config.close()


def terminate(signal, frame):
    """Terminate the program."""
    LOG.info('Asked to terminate')
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    main(sys.argv[1:])
