"""
Workflow switcher

Launches workflows from processing blocks in the configuration database.
"""

# pylint: disable=C0103

import subprocess
import logging
import ska_sdp_config

# Dictionary defining mapping from workflow IDs to Python scripts.

workflows_realtime = {
    'testdeploy': 'testdeploy.py',
    'testdask': 'testdask.py',
    'vis_receive': 'test_vis_receive.py'
}

def main():
    """Main loop."""

    logging.basicConfig()
    log = logging.getLogger('main')
    log.setLevel(logging.INFO)

    # Connect to configuration database.
    client = ska_sdp_config.Config()

    log.info("Waiting for processing block...")
    for txn in client.txn():
        target_pb_blocks = txn.list_processing_blocks()
        for pb_id in target_pb_blocks:
            if txn.get_processing_block_owner(pb_id) is not None:
                # Processing block is claimed, so continue to the next one.
                continue
            pb = txn.get_processing_block(pb_id)
            wf_type = pb.workflow['type']
            wf_id = pb.workflow['id']
            log.info("Found unclaimed PB with workflow of type {0} and id {1}".format(wf_type, wf_id))
            if wf_type == "realtime":
                if wf_id in workflows_realtime:
                    # Spawn Python process with workflow script.
                    log.info("Launching realtime workflow with id {0}".format(wf_id))
                    wf_script = workflows_realtime[wf_id]
                    # TODO: store return value and check for errors.
                    subprocess.Popen(["python3", wf_script, pb_id])
                else:
                    # Unknown realtime workflow ID.
                    log.error("Unknown realtime workflow id: {0}".format(wf_id))
            elif wf_type == "batch":
                log.warning("Batch workflows are not handled at present")
            else:
                log.error("Unknown workflow type: {0}".format(wf_type))
        log.info("Continue waiting...")
        txn.loop(wait=True)

if __name__ == "__main__":
    main()
