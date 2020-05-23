"""
Prototype Delivery Workflow.
"""

import os
import sys
import glob
import logging

import ska_sdp_config
import dask
import distributed

from google.oauth2 import service_account
from google.cloud import storage

# Initialise logging
logging.basicConfig()
LOG = logging.getLogger('delivery')
LOG.setLevel(logging.INFO)


def ee_dask_deploy(config, pb_id, image, n_workers=1, buffers=[], secrets=[]):
    """Deploy Dask execution engine.

    :param config: configuration DB handle
    :param pb_id: processing block ID
    :param image: Docker image to deploy
    :param n_workers: number of Dask workers
    :param buffers: list of buffers to mount on Dask workers
    :param secrets: list of secrets to mount on Dask workers
    :return: deployment ID and Dask client handle

    """
    # Make deployment
    deploy_id = 'proc-{}-dask'.format(pb_id)
    values = {'image': image, 'worker.replicas': n_workers}
    for i, b in enumerate(buffers):
        values['buffers[{}]'.format(i)] = b
    for i, s in enumerate(secrets):
        values['secrets[{}]'.format(i)] = s
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


def upload_directory_to_gcp(sa_file, bucket_name, src_dir, dst_dir):
    """Recursively upload contents of directory to Google Cloud Platform

    :param sa_file: service account JSON file
    :param bucket_name: name of the bucket on GCP
    :param src_dir: local source directory
    :param dst_dir: destination directory in GCP bucket
    """
    # Recursively list everything in directory
    src_list = sorted(glob.glob(src_dir + '/**', recursive=True))

    # Get connection to GCP bucket
    credentials = service_account.Credentials.from_service_account_file(sa_file)
    client = storage.Client(credentials=credentials, project=credentials.project_id)
    bucket = client.bucket(bucket_name)

    # Upload files (ignoring directories)
    for src_name in src_list:
        if not os.path.isdir(src_name):
            dst_name = dst_dir + '/' + src_name[len(src_dir)+1:]
            blob = bucket.blob(dst_name)
            blob.upload_from_filename(src_name)


def deliver(client, parameters):
    """Delivery function

    :param client: Dask distributed client
    :param parameters: parameters
    """
    sa = parameters.get('service_account')
    bucket = parameters.get('bucket')
    buffers = parameters.get('buffers', [])

    if sa is None or bucket is None:
        return

    sa_file = '/secret/{}/{}'.format(
        sa.get('secret'), sa.get('file')
    )

    tasks = []
    for b in buffers:
        src_dir = '/buffer/' + b.get('name')
        dst_dir = b.get('destination')
        tasks.append(
            dask.delayed(upload_directory_to_gcp)(
                sa_file, bucket, src_dir, dst_dir
            )
        )

    client.compute(tasks, sync=True)


def main(argv):
    """Workflow main function."""
    pb_id = argv[0]

    config = ska_sdp_config.Config()

    for txn in config.txn():
        txn.take_processing_block(pb_id, config.client_lease)
        pb = txn.get_processing_block(pb_id)
    LOG.info('Claimed processing block %s', pb_id)

    # Parse parameters
    n_workers = pb.parameters.get('n_workers', 1)
    buffers = [b.get('name') for b in pb.parameters.get('buffers', [])]
    secrets = [pb.parameters.get('service_account', {}).get('secret')]

    # Set state to indicate workflow is waiting for resources
    LOG.info('Setting status to WAITING')
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

    # Deploy Dask EE
    LOG.info('Deploying Dask EE')
    image = 'nexus.engageska-portugal.pt/sdp-prototype/workflow-delivery:{}' \
            ''.format(pb.workflow.get('version'))
    deploy_id, client = ee_dask_deploy(
        config, pb.id, image, n_workers=n_workers, buffers=buffers, secrets=secrets
    )

    # Run delivery function
    LOG.info('Starting delivery')
    deliver(client, pb.parameters)
    LOG.info('Finished delivery')

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
