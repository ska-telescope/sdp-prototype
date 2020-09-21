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
import ska_sdp_workflow

ska.logging.configure_logging()
LOG = logging.getLogger('test_receive_addresses')
LOG.setLevel(logging.DEBUG)


def main(argv):
    """Main loop."""
    # Get processing block ID from first argument
    pb_id = argv[0]

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

    # Get scan types
    scan_types = workflow.get_scan_types(sbi_id)

    # Generate and update receive addresses
    workflow.receive_addresses(scan_types, sbi_id, pb_id)

    # ... Do some processing here ...

    LOG.info("Monitoring SBI")
    workflow.monitor_sbi(sbi_id, pb_id)


def terminate(signal_, frame):
    """Terminate the program."""
    # pylint: disable=unused-argument
    LOG.info('Asked to terminate')
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    main(sys.argv[1:])
