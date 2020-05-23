"""
Batch Imaging Workflow.
"""

import os
import sys
import logging

import ska_sdp_config
import distributed
import rascil_workflows

# Initialise logging
logging.basicConfig()
LOG = logging.getLogger('batch_imaging')
LOG.setLevel(logging.INFO)


def buffer_create(config, name, size=None):
    """Create buffer reservation.

    :param config: configuration DB handle
    :param name: name
    :param size: size, uses default in chart if None

    """
    deploy_id = name
    values = {}
    if size is not None:
        values['size'] = size
    deploy = ska_sdp_config.Deployment(
        deploy_id, 'helm', {'chart': 'buffer', 'values': values}
    )
    for txn in config.txn():
        txn.create_deployment(deploy)


def ee_dask_deploy(config, pb_id, image, n_workers=1, buffers=[]):
    """Deploy Dask execution engine.

    :param config: configuration DB handle
    :param pb_id: processing block ID
    :param image: Docker image to deploy
    :param n_workers: number of Dask workers
    :param buffers: list of buffers to mount on Dask workers
    :return: deployment ID and Dask client handle

    """
    # Make deployment
    deploy_id = 'proc-{}-dask'.format(pb_id)
    values = {'image': image, 'worker.replicas': n_workers}
    for i, b in enumerate(buffers):
        values['buffers[{}]'.format(i)] = b
    deploy = ska_sdp_config.Deployment(
        deploy_id, 'helm', {'chart': 'dask', 'values': values}
    )
    for txn in config.txn():
        txn.create_deployment(deploy)

    # Wait for scheduler to become available
    scheduler = deploy_id + '-scheduler.' + os.environ['SDP_HELM_NAMESPACE'] + ':8786'
    client = None
    while client is None:
        try:
            client = distributed.Client(scheduler, timeout=1)
        except:
            pass

    return deploy_id, client


def ee_dask_remove(config, deploy_id):
    """Remove Dask EE deployment.

    :param config: configuration DB handle
    :param deploy_id: deployment ID

    """
    for txn in config.txn():
        deploy = txn.get_deployment(deploy_id)
        txn.delete_deployment(deploy)


def main(argv):
    """Main function."""
    pb_id = argv[0]

    config = ska_sdp_config.Config()

    for txn in config.txn():
        txn.take_processing_block(pb_id, config.client_lease)
        pb = txn.get_processing_block(pb_id)
    LOG.info('Claimed processing block %s', pb_id)

    # Parse parameters: these ones are needed for deploying the Dask EE
    n_workers = pb.parameters.get('n_workers', 2)
    buffer_vis = pb.parameters.get('buffer_vis')
    if buffer_vis is None:
        buffer_vis = 'buff-{}-vis'.format(pb.id)
        pb.parameters['buffer_vis'] = buffer_vis
    buffer_img = pb.parameters.get('buffer_img')
    if buffer_img is None:
        buffer_img = 'buff-{}-img'.format(pb.id)
        pb.parameters['buffer_img'] = buffer_img

    # Set state to indicate workflow is waiting for resources
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        state['status'] = 'WAITING'
        txn.update_processing_block_state(pb_id, state)

    # Wait for resources_available to be true
    LOG.info('Waiting for resources to be available')
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        ra = state.get('resources_available')
        if ra is not None and ra:
            LOG.info('Resources are available')
            break
        txn.loop(wait=True)

    # Set state to indicate workflow is running
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        state['status'] = 'RUNNING'
        txn.update_processing_block_state(pb_id, state)

    # Create buffer reservations for visibilities and images.
    LOG.info('Creating buffer reservations')
    buffer_create(config, buffer_vis)
    buffer_create(config, buffer_img)

    # Deploy Dask EE
    LOG.info('Deploying Dask EE')
    image = 'nexus.engageska-portugal.pt/sdp-prototype/workflow-batch-imaging:{}' \
            ''.format(pb.workflow['version'])
    buffers = [buffer_vis, buffer_img]
    deploy_id, client = ee_dask_deploy(
        config, pb.id, image, n_workers=n_workers, buffers=buffers
    )

    # Run simulation and ICAL pipelines
    rascil_workflows.set_client(client)
    LOG.info('Running simulation pipeline')
    rascil_workflows.simulate(pb.parameters)
    LOG.info('Running ICAL pipeline')
    rascil_workflows.ical(pb.parameters)
    rascil_workflows.close_client()
    LOG.info('Finished processing')

    # Remove Dask EE deployment
    LOG.info('Removing Dask EE deployment')
    ee_dask_remove(config, deploy_id)

    # Set state to indicate processing is finished
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        state['status'] = 'FINISHED'
        txn.update_processing_block_state(pb_id, state)

    config.close()


if __name__ == '__main__':
    main(sys.argv[1:])
