"""
SDP Processing Controller

Deploys workflows specified by processing blocks in the configuration
database.
"""

import os
import signal
import json
import time
import urllib
import jsonschema
import ska_sdp_config
from ska_sdp_logging import core_logging

LOG_LEVEL = os.getenv('SDP_LOG_LEVEL', 'DEBUG')
WORKFLOWS_URL = os.getenv('SDP_WORKFLOWS_URL',
                          'https://gitlab.com/ska-telescope/sdp-prototype/raw/master/src/workflows/workflows.json')
WORKFLOWS_REFRESH = int(os.getenv('SDP_WORKFLOWS_REFRESH', '300'))

# Location of the schema file for validating the workflow definitions.

WORKFLOWS_SCHEMA = 'workflows_schema.json'

LOG = core_logging.init(name='processing_controller', level=LOG_LEVEL)


def get_environment_variables(var: list) -> dict:
    """Get values of environment variables and store them in a suitable
    form for passing to the workflow Helm chart.
    """
    values = {}
    for v in var:
        values['env.{}'.format(v)] = os.environ[v]
    return values


def update_workflow_definition(definition_url, schema_file):
    """Update workflow definitions."""

    # Read schema file.
    with open(schema_file, 'r') as f:
        schema = json.load(f)

    # Fetch workflow definition file from URL, parse as JSON and validate
    # against the schema.
    LOG.debug('Fetching workflow definitions from %s', definition_url)
    try:
        with urllib.request.urlopen(definition_url) as f:
            definition = json.loads(f.read())
        jsonschema.validate(definition, schema)
    except urllib.error.URLError as e:
        LOG.error('Cannot fetch workflow definitions: %s', e.reason)
        return {}, {}, {}
    except json.JSONDecodeError as e:
        LOG.error('Cannot decode workflow definitions as JSON: %s', e.msg)
        return {}, {}, {}
    except jsonschema.ValidationError as e:
        LOG.error('Cannot validate workflow definitions: %s', e.message)
        return {}, {}, {}

    # Get version of workflow definition file.
    version = definition['version']

    # Parse repositories.
    repositories = {}
    for repo in definition['repositories']:
        repo_name = repo['name']
        repo_path = repo['path']
        if repo_name in repositories:
            LOG.warning("Repository {} already defined, will be overwritten".format(repo_name))
        repositories[repo_name] = repo_path

    # Parse workflow definitions.
    realtime = {}
    batch = {}
    for wf in definition['workflows']:
        wf_type = wf['type']
        wf_id = wf['id']
        wf_repo = wf['repository']
        wf_image = wf['image']
        wf_versions = wf['versions']
        if wf_repo not in repositories:
            LOG.warning("Repository {} for {} workflow {} not found, skipping".format(wf_repo, wf_type, wf_id))
            continue
        if wf_type == 'realtime':
            workflows = realtime
        elif wf_type == 'batch':
            workflows = batch
        else:
            LOG.warning("Workflow {} has unknown type {}, skipping".format(wf_id, wf_type))
            continue
        for vers in wf_versions:
            if (wf_id, vers) in workflows:
                LOG.warning("{} workflow {} version {} already defined, "
                            "will be overwritten".format(wf_type, wf_id, vers))
            workflows[(wf_id, vers)] = repositories[wf_repo] + "/" + wf_image + ":" + vers

    LOG.debug("Workflow definitions version:")
    for k, v in version.items():
        LOG.debug("{}: {}".format(k, v))
    LOG.debug("Realtime workflows:")
    for k, v in realtime.items():
        LOG.debug("{}: {}".format(k, v))
    LOG.debug("Batch workflows:")
    for k, v in batch.items():
        LOG.debug("{}: {}".format(k, v))

    return version, realtime, batch


def get_pb_id_from_deploy_id(deploy_id: str) -> str:
    """Get processing block ID from deployment ID.

    This assumes that all deployments associated with a processing
    block of ID `[type]-[date]-[number]` have a deployment ID of the
    form `[type]-[date]-[number]-*`.
    """
    return '-'.join(deploy_id.split('-')[0:3])


def main():
    """Main loop."""

    # Get environment variables to pass to workflow containers.
    values_env = get_environment_variables(['SDP_CONFIG_HOST',
                                            'SDP_HELM_NAMESPACE'])

    # Fetch workflow definitions.
    workflows_version, workflows_realtime, workflows_batch = \
        update_workflow_definition(WORKFLOWS_URL, WORKFLOWS_SCHEMA)
    next_workflows_refresh = time.time() + WORKFLOWS_REFRESH

    # Connect to configuration database.
    client = ska_sdp_config.Config()

    LOG.debug("Starting main loop...")
    for txn in client.txn():

        # Update workflow definitions if it is time to do so.

        if time.time() >= next_workflows_refresh:
            LOG.debug('Updating workflow definitions')
            workflows_version, workflows_realtime, workflows_batch = \
                update_workflow_definition(WORKFLOWS_URL, WORKFLOWS_SCHEMA)
            next_workflows_refresh = time.time() + WORKFLOWS_REFRESH

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
            LOG.info("PB {} has no deployment (workflow type = {}, ID = {}, version = {})"
                     "".format(pb_id, wf_type, wf_id, wf_version))
            if wf_type == "realtime":
                if (wf_id, wf_version) in workflows_realtime:
                    LOG.info("Deploying realtime workflow ID = {}, version = {}"
                             "".format(wf_id, wf_version))
                    wf_image = workflows_realtime[(wf_id, wf_version)]
                    deploy_id = "{}-workflow".format(pb_id)
                    # Values to pass to workflow Helm chart.
                    # Copy environment variable values and add argument values.
                    values = dict(values_env)
                    values['wf_image'] = wf_image
                    values['pb_id'] = pb_id
                    deploy = ska_sdp_config.Deployment(
                        deploy_id, 'helm', {'chart': 'workflow', 'values': values}
                    )
                    LOG.info("Creating deployment {}".format(deploy_id))
                    txn.create_deployment(deploy)
                else:
                    # Unknown realtime workflow ID and version.
                    LOG.error("Workflow ID = {} version = {} is not supported".format(wf_id, wf_version))
            elif wf_type == "batch":
                LOG.warning("Batch workflows are not supported at present")
            else:
                LOG.error("Unknown workflow type: {}".format(wf_type))

        LOG.debug("Waiting...")
        txn.loop(wait=True, timeout=next_workflows_refresh - time.time())


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
