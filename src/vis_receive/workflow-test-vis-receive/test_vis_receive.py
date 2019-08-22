"""
Example Vis Receive workflow
"""

# pylint: disable=C0103

import logging
import ska_sdp_config
import os

# Initialise logging and configuration
logging.basicConfig()
log = logging.getLogger('main')
log.setLevel(logging.INFO)
config = ska_sdp_config.Config()

# Find processing block configuration from the configuration.
workflow = {
    'id': 'vis_receive',
    'version': '0.1.0',
    'type': 'realtime'
}
log.info("Waiting for processing block...")
for txn in config.txn():
    pb = txn.take_processing_block_by_workflow(
        workflow, config.client_lease)
    if pb is not None:
        continue
    txn.loop(wait=True)

# Show
log.info("Claimed processing block %s", pb)

# Deploy Vis Receive with 1 worker.
log.info("Deploying Vis Receive...")
deploy_id = pb.pb_id + "-vis-receive"
deploy = ska_sdp_config.Deployment(
    deploy_id, "helm", {
        'chart': 'vis-receive', # Helm chart deploy/charts/vis-receive
    })
for txn in config.txn():
    txn.create_deployment(deploy)
try:

    # Just idle until processing block or we lose ownership
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
