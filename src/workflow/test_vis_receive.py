"""
Example Vis Receive workflow
"""

# pylint: disable=C0103

import logging
import ska_sdp_config
import os
import sys

# Initialise logging and configuration
logging.basicConfig()
log = logging.getLogger('vis_recv')
log.setLevel(logging.INFO)
config = ska_sdp_config.Config()


# # Find processing block configuration from the configuration.
# workflow = {
#     'id': 'vis_receive',
#     'version': '0.1.0',
#     'type': 'realtime'
# }

def main(argv):
    pb_id = argv[0]
    log.info("Inside Vis receive...")
    for txn in config.txn():
        # target_pb_blocks = txn.list_processing_blocks()
        # for pb_id in target_pb_blocks:
        pb = txn.get_processing_block(pb_id)
        if txn.get_processing_block_owner(pb_id) is None:
            # Take ownership
            txn.take_processing_block(pb_id, config.client_lease)
        # if pb is not None:
        #     continue

    # Show
    log.info("Claimed processing block %s", pb)

    # Deploy Vis Receive with 1 worker.
    log.info("Deploying Vis Receive...")
    deploy_id = pb.pb_id + "-vis-receive"
    deploy = ska_sdp_config.Deployment(
        deploy_id, "helm", {
            'chart': 'vis-receive',  # Helm chart deploy/charts/vis-receive
        })
    for txn in config.txn():
        txn.create_deployment(deploy)
    try:

        # Just idle until processing block or disappears
        log.info("Done, now idling...")
        for txn in config.txn():
            if not txn.is_processing_block_owner(pb.pb_id):
                break
            txn.loop(True)

    finally:

        # Clean up vis receive deployment.
        for txn in config.txn():
            txn.delete_deployment(deploy)

        config.close()


if __name__ == "__main__":
    main(sys.argv[1:])
