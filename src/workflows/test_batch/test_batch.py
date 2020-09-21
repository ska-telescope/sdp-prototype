"""
Workflow to test batch processing.
"""

import sys
import time
import signal
import logging
import ska.logging
import ska_sdp_workflow

ska.logging.configure_logging()
LOG = logging.getLogger('test_batch')
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
    LOG.info(sbi_id)

    # Get parameter and parse it
    duration = workflow.get_parameters(pb_id)

    # Resource Request
    LOG.info("Resource Request")
    workflow.resource_request(pb_id)

    LOG.info("Monitoring SBI")
    workflow.monitor_sbi_batch(pb_id, duration)


def terminate(signal, frame):
    """Terminate the program."""
    LOG.info('Asked to terminate')
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, terminate)
    main(sys.argv[1:])
