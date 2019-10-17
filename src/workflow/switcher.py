"""
Helm deployment controller.

Applies/updates/deletes Helm releases depending on information from
the SDP configuration.
"""

# pylint: disable=C0103

import os
import logging
import ska_sdp_config


def main():
    """Main loop Processing block."""

    logging.basicConfig()
    log = logging.getLogger('main')
    log.setLevel(logging.INFO)

    # Instantiate configuration
    client = ska_sdp_config.Config()

    log.info("Waiting for processing block...")
    for txn in client.txn():
        target_pb_blocks = txn.list_processing_blocks()
        for pb_id in target_pb_blocks:
            pb = txn.get_processing_block(pb_id)
            if pb.workflow['type'] == "realtime":
                log.info(pb.workflow['id'])
                if pb.workflow['id'] == "vis_receive":
                    os.system("python3 {0}".format("test_vis_receive.py"))
                elif pb.workflow['id'] == "testdeploy":
                    os.system("python3 {0}".format("testdeploy.py"))

        txn.loop(wait=True)


main()
