"""
Example Propagation of error from workflow to PB state in ConfigDB
"""

# pylint: disable=C0103

import logging
import sys
import ska_sdp_config
import time

# Initialise logging and configuration
logging.basicConfig()
LOG = logging.getLogger('ska.sdp.teststate')
LOG.setLevel(logging.INFO)
config = ska_sdp_config.Config()


def main(argv):
    pb_id = argv[0]
    for txn in config.txn():
        txn.take_processing_block(pb_id, config.client_lease)
        pb = txn.get_processing_block(pb_id)

    # Show
    LOG.info("Claimed processing block %s", pb)

    for txn in config.txn():
        # Check current PB state
        state_out = txn.get_processing_block_state(pb_id)
        if state_out is None:
            LOG.info("state is None")

            # Create new state
            new_state = {
                "state": "executing",
                "subarray": "ON-test",
                "obsState": "SCANNING-test",
                "receiveAddresses": {
                    "1": {
                        "1": ["0.0.0.0", 1024]
                    }
                }
            }
            # Create processing block
            txn.create_processing_block_state(pb_id, new_state)
            LOG.info("Created Processing Block State")

    # Sleep for 180 seconds
    time.sleep(180)

    # Update state
    for txn in config.txn():
        update_state = {
            "state": "error",
            "subarray": "ON-test",
            "obsState": "SCANNING-test",
            "receiveAddresses": {
                "1": {
                    "1": ["0.0.0.0", 1024]
                }
            }
        }
        # Update processing block state
        txn.update_processing_block_state(pb_id, update_state)
        LOG.info("Updated Processing Block State")

        # Get processing block state
        get_state = txn.get_processing_block_state(pb_id)
        LOG.info(" Updated State %s: ", get_state)

    config.close()

    # try:
    #     kubernetes.config.load_incluster_config()
    # except kubernetes.config.ConfigException:
    #     kubernetes.config.load_kube_config()
    # # Get all pods from kubernetes
    # ret = api.list_pod_for_all_namespaces(watch=False)
    # for i in ret.items:
    #     if i.metadata.namespace == 'sdp':
    #         for event in i.status.container_statuses:
    #             LOG.info("READY - %s", event.ready)
    #             LOG.info("STATE - %s", event.state)
    #             LOG.info("restart_count - %s", event.restart_count)


if __name__ == "__main__":
    main(sys.argv[1:])
