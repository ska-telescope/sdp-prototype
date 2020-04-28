"""
Example PSS Receive workflow
"""

# pylint: disable=C0103

import logging
import ska_sdp_config
import sys

# Initialise logging and configuration
logging.basicConfig()
log = logging.getLogger('pss_recv')
log.setLevel(logging.INFO)
config = ska_sdp_config.Config()


def main(argv):
    pb_id = argv[0]
    for txn in config.txn():
        txn.take_processing_block(pb_id, config.client_lease)
        pb = txn.get_processing_block(pb_id)

    # Show
    log.info("Claimed processing block %s", pb)

    # Deploy PSS Receive with 1 worker.
    log.info("Deploying PSS Receive...")
    deploy_id = 'proc-{}-pss-receive'.format(pb.id)
    deploy = ska_sdp_config.Deployment(
        deploy_id, "helm", {
            'chart': 'pss-receive',  # Helm chart deploy/charts/pss-receive
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

        # Clean up pss receive deployment.
        for txn in config.txn():
            txn.delete_deployment(deploy)

        config.close()


if __name__ == "__main__":
    main(sys.argv[1:])
