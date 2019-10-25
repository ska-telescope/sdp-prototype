"""
SDP Processing Controller

Deploys workflows specified by processing blocks in the configuration
database.
"""

import os
import signal
import logging
import ska_sdp_config

# Dictionary defining mapping from workflow IDs to Python scripts.
# The workflow scripts are in the workflows container.

WORKFLOWS_REALTIME = {
    'testdeploy': 'testdeploy',
    'testdask': 'testdask',
    'vis_receive': 'vis_receive',
    'testdlg': 'daliuge.main'
}

WORKFLOWS_BATCH = {}

logging.basicConfig()
LOG = logging.getLogger('main')
LOG.setLevel(logging.INFO)


def main():
    """Main loop."""

    # Connect to configuration database.
    client = ska_sdp_config.Config()

    LOG.info("Waiting for processing block...")
    for txn in client.txn():
        target_pb_blocks = txn.list_processing_blocks()
        for pb_id in target_pb_blocks:
            if txn.get_processing_block_owner(pb_id) is not None:
                # Processing block is claimed, so continue to the next one.
                continue
            pb = txn.get_processing_block(pb_id)
            wf_type = pb.workflow['type']
            wf_id = pb.workflow['id']
            LOG.info("Found unclaimed PB {} with workflow of type {} and id {}"
                     "".format(pb_id, wf_type, wf_id))
            if wf_type == "realtime":
                if wf_id in WORKFLOWS_REALTIME:
                    LOG.info("Deploying realtime workflow with id {}".format(wf_id))
                    wf_script = WORKFLOWS_REALTIME[wf_id]
                    deploy_id = pb_id + "-workflow-" + wf_id
                    # Values to pass to workflow Helm chart.
                    values = {
                        'sdp_config_host': os.getenv('SDP_CONFIG_HOST', '127.0.0.1'),
                        'wf_script': wf_script,
                        'pb_id': pb_id
                    }
                    deploy = ska_sdp_config.Deployment(
                        deploy_id, 'helm', {
                            'chart': 'workflow',
                            'values': values
                        })
                    txn.create_deployment(deploy)
                else:
                    # Unknown realtime workflow ID.
                    LOG.error("Unknown realtime workflow id: {}".format(wf_id))
            elif wf_type == "batch":
                LOG.warning("Batch workflows are not handled at present")
            else:
                LOG.error("Unknown workflow type: {}".format(wf_type))
        LOG.info("Continue waiting...")
        txn.loop(wait=True)


def terminate(signal, frame):
    """Terminate the program."""
    LOG.info("Asked to terminate")
    # Note that this will likely send SIGKILL to children processes -
    # not exactly how this is supposed to work. But all of this is
    # temporary anyway.
    exit(0)


if __name__ == "__main__":

    # Register SIGTERM handler
    signal.signal(signal.SIGTERM, terminate)

    # Call main
    main()
