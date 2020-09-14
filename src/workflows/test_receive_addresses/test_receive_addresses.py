"""
Workflow to test generation of receive addresses.

The purpose of this workflow is to test the mechanism for generating SDP
receive addresses from the channel link map contained in the SBI. The workflow
picks it up from there, uses it to generate the receive addresses for each scan
type and writes them to the processing block state. The subarray publishes this
address map on the appropriate attribute to complete the transition following
AssignResources.

This workflow does not generate any deployments.
"""

import sys
import signal
import logging
import ska.logging
import ska_sdp_config

ska.logging.configure_logging()
LOG = logging.getLogger('test_receive_addresses')
LOG.setLevel(logging.DEBUG)


def minimal_receive_addresses(channels):
    """
    Generate a minimal version of the receive addresses for a single scan type.

    :param channels: list of channels
    :returns: receive addresses

    """
    host = []
    port = []
    for i, chan in enumerate(channels):
        start = chan.get('start')
        host.append([start, '192.168.0.{}'.format(i+1)])
        port.append([start, 9000, 1])
    receive_addresses = dict(host=host, port=port)
    return receive_addresses


def generate_receive_addresses(scan_types):
    """
    Generate receive addresses for all scan types.

    This function generates a minimal fake response.

    :param scan_types: scan types from SBI
    :return: receive addresses

    """
    receive_addresses = {}
    for scan_type in scan_types:
        channels = scan_type.get('channels')
        receive_addresses[scan_type.get('id')] = minimal_receive_addresses(channels)
    return receive_addresses


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

    sbi_id = pb.sbi_id
    LOG.info('SBI id: %s', sbi_id)

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

    # Get the channel link map from SBI
    LOG.info('Retrieving channel link map from SBI')
    for txn in config.txn():
        sbi = txn.get_scheduling_block(sbi_id)
        scan_types = sbi.get('scan_types')

    # Generate receive addresses
    LOG.info('Generating receive addresses')
    receive_addresses = generate_receive_addresses(scan_types)

    # Update receive addresses in processing block state
    LOG.info('Updating receive addresses in processing block state')
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        state['receive_addresses'] = receive_addresses
        txn.update_processing_block_state(pb_id, state)

    # Write pb_id in pb_receive_addresses in SBI
    LOG.info('Writing PB ID to pb_receive_addresses in SBI')
    for txn in config.txn():
        sbi = txn.get_scheduling_block(sbi_id)
        sbi['pb_receive_addresses'] = pb_id
        txn.update_scheduling_block(sbi_id, sbi)

    # ... Do some processing here ...

    # Wait until SBI is marked as FINISHED or CANCELLED
    LOG.info('Waiting for SBI to end')
    for txn in config.txn():
        sbi = txn.get_scheduling_block(sbi_id)
        status = sbi.get('status')
        if status in ['FINISHED', 'CANCELLED']:
            LOG.info('SBI is %s', status)
            break
        txn.loop(wait=True)

    # Set state to indicate processing has ended
    LOG.info('Setting status to %s', status)
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        state['status'] = status
        txn.update_processing_block_state(pb_id, state)

    # Close connection to config DB
    LOG.info('Closing connection to config DB')
    config.close()


def terminate(signal_, frame):
    """Terminate the program."""
    # pylint: disable=unused-argument
    LOG.info('Asked to terminate')
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    main(sys.argv[1:])
