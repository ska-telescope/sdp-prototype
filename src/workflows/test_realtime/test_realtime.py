"""
Workflow to test real-time processing.
"""

import sys
import signal
import logging
import ska.logging
import ska_sdp_config

ska.logging.configure_logging()
LOG = logging.getLogger('test_realtime')
LOG.setLevel(logging.DEBUG)


def main(argv):
    # Get processing block ID from first argument
    pb_id = argv[0]
    LOG.info('PB id: %s', pb_id)

    # Get connection to config DB
    LOG.info('Opening connection to config DB')
    config = ska_sdp_config.Config()

    # Claim processing block
    for txn in config.txn():
        txn.take_processing_block(pb_id, config.client_lease)
        pb = txn.get_processing_block(pb_id)
    LOG.info('Claimed processing block')

    sbi_id = pb.sbi_id
    LOG.info('SBI id: %s', sbi_id)

    # Set state to indicate workflow is waiting for resources
    LOG.info('Setting status to WAITING')
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        state['status'] = 'WAITING'
        txn.update_processing_block_state(pb_id, state)

    # Wait for resources_available to be true
    LOG.info('Waiting for resources to be available')
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        ra = state.get('resources_available')
        if ra is not None and ra:
            LOG.info('Resources are available')
            break
        txn.loop(wait=True)

    # Set state to indicate processing has started
    LOG.info('Setting status to RUNNING')
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        state['status'] = 'RUNNING'
        txn.update_processing_block_state(pb_id, state)

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


def terminate(signal, frame):
    """Terminate the program."""
    LOG.info('Asked to terminate')
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, terminate)
    main(sys.argv[1:])
