"""
Example real-time SDP workflow.

Just waits for matching configuration to appear in the configuration,
and holds it until it gets removed.
"""

# pylint: disable=C0103

import logging
import ska_sdp_config

logging.basicConfig()
log = logging.getLogger('main')
log.setLevel(logging.INFO)

# Instantiate configuration
client = ska_sdp_config.Config()

# Find processing block configuration
workflow = {
    'id': 'example',
    'version': '0.0.1',
    'type': 'realtime'
}
for txn in client.txn():
    pb = txn.take_processing_block_by_workflow(workflow, client.client_lease)
    if pb is not None:
        continue
    txn.loop(wait=True)

# Show
log.info("Claimed processing block %s", pb)
pb_id = pb.pb_id

# Wait for something to happen
for txn in client.txn():
    if not txn.is_processing_block_owner(pb_id):
        log.warning("Lost processing block ownership")
        exit(0)

    # Get current processing block info (for realtime processing
    # blocks scan data might get updated)
    pb = txn.get_processing_block(pb_id)
    if pb is None:
        log.warning("Processing block got deleted")
        exit(1)

    # Nothing to do, just wait
    txn.loop(wait=True)
