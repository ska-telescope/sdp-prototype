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
# The workflow scripts are in the workflow container.

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


def get_pb_id_from_deploy_id(deploy_id: str) -> str:
    """Get processing block ID from deployment ID.

    This assumes that all deployments associated with a processing
    block of ID `[type]-[date]-[number]` have a deployment ID of the
    form `[type]-[date]-[number]-*`.
    """
    return '-'.join(deploy_id.split('-')[0:3])


def main():
    """Main loop."""

    # Connect to configuration database.
    client = ska_sdp_config.Config()

    LOG.info("Starting main loop...")
    for txn in client.txn():

        # Get lists of processing blocks and deployments.

        current_pbs = txn.list_processing_blocks()
        current_deployments = txn.list_deployments()

        # Make list of current PBs with deployments, inferred from the deployment IDs.

        current_pbs_with_deployment = list(set(map(get_pb_id_from_deploy_id, current_deployments)))

        LOG.debug("Current PBs: {}".format(current_pbs))
        LOG.debug("Current deployments: {}".format(current_deployments))
        LOG.debug("Current PBs with deployment: {}".format(current_pbs_with_deployment))

        # Delete deployments not associated with processing blocks.

        for deploy_id in current_deployments:
            # Get ID of associated processing block by taking prefix of deployment ID.
            pb_id = get_pb_id_from_deploy_id(deploy_id)
            if pb_id not in current_pbs:
                LOG.info("Deleting deployment {}".format(deploy_id))
                deploy = txn.get_deployment(deploy_id)
                txn.delete_deployment(deploy)

        # Deploy workflow for processing blocks without deployments.

        for pb_id in current_pbs:
            if pb_id in current_pbs_with_deployment:
                continue
            pb = txn.get_processing_block(pb_id)
            wf_type = pb.workflow['type']
            wf_id = pb.workflow['id']
            wf_version = pb.workflow['version']
            LOG.info("PB {} has no deployment, workflow type: {}, ID: {}, version: {}"
                     "".format(pb_id, wf_type, wf_id, wf_version))
            if wf_type == "realtime":
                if wf_id in WORKFLOWS_REALTIME:
                    LOG.info("Deploying realtime workflow ID: {}, version: {}".format(wf_id, wf_version))
                    wf_script = WORKFLOWS_REALTIME[wf_id]
                    deploy_id = "{}-workflow-{}-{}".format(pb_id, wf_id, wf_version.replace('.', '-'))
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
                    LOG.error("Unknown realtime workflow ID: {}".format(wf_id))
            elif wf_type == "batch":
                LOG.warning("Batch workflows are not handled at present")
            else:
                LOG.error("Unknown workflow type: {}".format(wf_type))
        LOG.info("Waiting...")
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
