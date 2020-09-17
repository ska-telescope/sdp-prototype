"""
Example CBF-SDP receive workflow
Adapted from the vis_receive workflow
This just deploys the simple-pair chart
"""

# pylint: disable=C0103

import sys
import logging
import ska_sdp_config

# Initialise logging and configuration
logging.basicConfig()
log = logging.getLogger('cbf_sdp')
log.setLevel(logging.INFO)
config = ska_sdp_config.Config()


def main(argv):
    pb_id = argv[0]
    for txn in config.txn():
        txn.take_processing_block(pb_id, config.client_lease)
        pb = txn.get_processing_block(pb_id)

    # Show
    log.info("Claimed processing block %s", pb)

    # Deploy Vis Receive with 1 worker.
    log.info("Deploying CBF-SDP Receive Workflow...")
    deploy_id = 'proc-{}-cbf-sdp-emulator'.format(pb.id)
    deploy = ska_sdp_config.Deployment(
        deploy_id, "helm", {
            'chart': 'cbf-sdp-emulator',  # Helm chart deploy from the repo
        })
    for txn in config.txn():
        txn.create_deployment(deploy)
    try:

        # Just idle until processing block or disappears
        log.info("Done, now idling...")
        for txn in config.txn():
            if not txn.is_processing_block_owner(pb.id):
                break
            txn.loop(True)

    finally:

        # Clean up vis receive deployment.
        for txn in config.txn():
            txn.delete_deployment(deploy)

        config.close()


if __name__ == "__main__":
    main(sys.argv[1:])
