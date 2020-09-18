"""
Workflow to test real-time processing.
"""

import sys
import signal
import logging

import ska_sdp_workflow

LOG = logging.getLogger('test_realtime')
LOG.setLevel(logging.DEBUG)


def main(argv):
    # Get processing block ID from first argument
    pb_id = argv[0]
    LOG.info('PB id: %s', pb_id)

    # Workflow library
    workflow = ska_sdp_workflow.Workflow()

    # Claim processing block
    LOG.info("Claim processing block")
    sbi_id = workflow.claim_processing_block(pb_id)

    # Resource Request
    LOG.info("Resource Request")
    workflow.resource_request(pb_id)

    # Process started
    LOG.info("Process started")
    workflow.process_started(pb_id)

    # ... Do some processing here ...

    LOG.info("Monitoring SBI")
    workflow.monitor_sbi(sbi_id, pb_id)


def terminate(signal, frame):
    """Terminate the program."""
    LOG.info('Asked to terminate')
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, terminate)
    main(sys.argv[1:])