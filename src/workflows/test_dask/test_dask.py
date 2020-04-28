"""
Example Dask workflow
"""

import os
import sys
import logging
import ska_sdp_config
import distributed

# Initialise logging
logging.basicConfig()
LOG = logging.getLogger('test_dask')
LOG.setLevel(logging.INFO)


def main(argv):
    pb_id = argv[0]

    # Obtain connection to configuration database. This is the main way to
    # both obtain information about what the workflow is supposed to do,
    # and its way to request actions from the rest of the system (e.g. ask
    # for deployments of additional software)
    config = ska_sdp_config.Config()

    # Note that this process "claims" the workflow with a lease. This
    # means that once a processing block has been claimed, this script
    # must check in with the configuration database every ~10 seconds
    # or will be declared dead (and presumably restarted). This
    # obviously means that no serious work should actually happen here.
    for txn in config.txn():
        txn.take_processing_block(pb_id, config.client_lease)
        pb = txn.get_processing_block(pb_id)
    LOG.info("Claimed processing block %s", pb_id)

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

    # Deploy Dask with 2 workers.
    # This is done by adding the request to the configuration database,
    # where it will be picked up and executed by appropriate
    # controllers. In the full system this will involve external checks
    # for whether the workflow actually has been assigned enough resources
    # to do this - and for obtaining such assignments the workflow would
    # need to communicate with a scheduler process. But we are ignoring
    # all of that at the moment.
    LOG.info("Deploying Dask...")
    deploy_id = 'proc-{}-dask'.format(pb.id)
    deploy = ska_sdp_config.Deployment(
        deploy_id, "helm", {
            'chart': 'stable/dask',
            'values': {
                'jupyter.enabled': 'false',
                'worker.replicas': 2,
                # We want to access Dask in-cluster using a DNS name
                'scheduler.serviceType': 'ClusterIP'
            }})
    for txn in config.txn():
        txn.create_deployment(deploy)

    try:
        # Wait for Dask to become available. At some point there will be a
        # way to learn about availability from the configuration database
        # (clearly populated by controllers querying Helm/Kubernetes).  So
        # for the moment we'll simply query the DNS name where we know
        # that Dask must become available eventually
        LOG.info("Waiting for Dask...")
        client = None
        for _ in range(200):
            try:
                client = distributed.Client(
                    deploy_id + '-scheduler.' +
                    os.environ['SDP_HELM_NAMESPACE'] + ':8786')
            except Exception as e:
                print(e)
        if client is None:
            LOG.error("Could not connect to Dask!")
            sys.exit(1)
        LOG.info("Connected to Dask")

        # Now we can use Dask to do some calculations. Let's use a silly
        # example from the documentation.
        def inc(x):
            return x + 1
        L = client.map(inc, range(1000))
        LOG.info("Dask results: %s", client.gather(L))

    finally:
        # Clean up Dask deployment. This should also become semi-optional
        # eventually, as clearly the processing controller should learn to
        # free all deployments associated with a workflow if it terminates
        # for whatever reason.
        for txn in config.txn():
            txn.delete_deployment(deploy)

    # Set state to indicate processing is finished.
    for txn in config.txn():
        state = txn.get_processing_block_state(pb_id)
        state['status'] = 'FINISHED'
        txn.update_processing_block_state(pb_id, state)

    config.close()

if __name__ == "__main__":
    main(sys.argv[1:])
