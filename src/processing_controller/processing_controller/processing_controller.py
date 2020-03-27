import os
import time
import logging
import ska_sdp_config
from .workflows import Workflows

LOG = logging.getLogger('processing_controller')


class ProcessingController:
    """
    SDP Processing Controller
    """

    def __init__(self, schema, url, refresh):
        self._workflows = Workflows(schema)
        self._url = url
        self._refresh = refresh

    @staticmethod
    def _get_pb_id_from_deploy_id(deploy_id: str) -> str:
        """
        Get processing block ID from deployment ID.

        This assumes that all deployments associated with a processing
        block of ID `[type]-[date]-[number]` have a deployment ID of the
        form `[type]-[date]-[number]-*`.

        :param deploy_id: deployment ID
        :returns: processing block ID
        """
        return '-'.join(deploy_id.split('-')[0:3])

    @staticmethod
    def _get_pb_status(txn, pb_id: str) -> str:
        """
        Get status of processing block

        :param pb_id: processing block ID
        :returns: processing block status
        """
        state = txn.get_processing_block_state(pb_id)
        status = state.get('status')
        return status

    def _start_new_pb_workflows(self, txn):
        """
        Start the workflows for new processing blocks.

        :param txn:
        """
        pb_ids = txn.list_processing_blocks()
        deploy_ids = txn.list_deployments()

        pbs_with_deployment = list(set(map(self._get_pb_id_from_deploy_id, deploy_ids)))

        for pb_id in pb_ids:
            status = self._get_pb_status(txn, pb_id)
            if status is None and pb_id not in pbs_with_deployment:
                self._start_workflow(txn, pb_id)

    def _start_workflow(self, txn, pb_id):
        """
        Start the workflow for a processing block.

        :param txn: config DB transaction
        :param pb_id: processing block ID
        """

        LOG.info('Making deployment for processing block %s', pb_id)

        # Read the processing block and its state
        pb = txn.get_processing_block(pb_id)
        state = txn.get_processing_block_state(pb_id)

        # Get workflow type, id and version
        wf_type = pb.workflow['type']
        wf_id = pb.workflow['id']
        wf_version = pb.workflow['version']

        # Get the container image for the workflow
        if wf_type == 'realtime':
            wf_image = self._workflows.realtime(wf_id, wf_version)
        elif wf_type == 'batch':
            wf_image = self._workflows.batch(wf_id, wf_version)
        else:
            LOG.error('Unknown workflow type %s', wf_type)
            wf_image = None

        if wf_image is not None :
            # Make the deployment
            LOG.info('Deploying %s workflow %s, version %s', wf_type, wf_id,
                    wf_version)
            deploy_id = '{}-workflow'.format(pb_id)
            values = {}
            for v in ['SDP_CONFIG_HOST', 'SDP_HELM_NAMESPACE']:
                values['env.' + v] = os.environ[v]
            values['wf_image'] = wf_image
            values['pb_id'] = pb_id
            chart = {
                'chart': 'workflow',
                'values': values
            }
            deploy = ska_sdp_config.Deployment(deploy_id, 'helm', chart)
            txn.create_deployment(deploy)
            # Set status to STARTING, and resources_available to False
            state['status'] = 'STARTING'
            state['resources_available'] = False
        else:
            # Invalid workflow, so set status to FAILED
            state['status'] = 'FAILED'

        # Update the processing block state.
        txn.update_processing_block_state(pb_id, state)

    def _release_pbs_with_finished_dependencies(self, txn):
        """
        Release processing blocks whose dependencies are all finished.

        :param txn: config DB transaction
        """
        pb_ids = txn.list_processing_blocks()

        for pb_id in pb_ids:
            state = txn.get_processing_block_state(pb_id)
            status = state.get('status')
            ra = state.get('resources_available')
            if status == 'WAITING' and not ra:
                # Check status of dependencies.
                pb = txn.get_processing_block(pb_id)
                dependencies = pb.dependencies
                dep_ids = [dep['pbId'] for dep in dependencies]
                dep_finished = map(lambda x: self._get_pb_status(txn, x) == 'FINISHED', dep_ids)
                all_finished = all(dep_finished)
                if all_finished:
                    LOG.info('Releasing processing block %s', pb_id)
                    state['resources_available'] = True
                    txn.update_processing_block_state(pb_id, state)

    def _delete_deployments_without_pb(self, txn):
        """
        Delete processing deployments not associated with a processing block.

        :param txn: config DB transaction
        """
        pb_ids = txn.list_processing_blocks()
        deploy_ids = txn.list_deployments()

        for deploy_id in deploy_ids:
            pb_id = self._get_pb_id_from_deploy_id(deploy_id)
            if pb_id not in pb_ids:
                LOG.info('Deleting deployment %s', deploy_id)
                deploy = txn.get_deployment(deploy_id)
                txn.delete_deployment(deploy)

    def main(self):
        """
        Main loop.
        """
        # Initialise workflow definitions
        LOG.info('Initialising workflow definitions')
        self._workflows.update_url(self._url)
        next_workflows_refresh = time.time() + self._refresh

        # Connect to config DB
        LOG.info('Connecting to config DB')
        config = ska_sdp_config.Config()

        LOG.info('Starting main loop')
        for txn in config.txn():

            # Update workflow definitions if it is time to do so
            if time.time() >= next_workflows_refresh:
                LOG.info('Updating workflow definitions')
                self._workflows.update_url(self._url)
                next_workflows_refresh = time.time() + self._refresh

            # Perform actions.
            self._start_new_pb_workflows(txn)
            self._release_pbs_with_finished_dependencies(txn)
            self._delete_deployments_without_pb(txn)

            LOG.debug('Waiting...')
            txn.loop(wait=True, timeout=next_workflows_refresh - time.time())
