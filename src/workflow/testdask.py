"""
Example Dask workflow
"""

# pylint: disable=C0103

import os
import logging
import ska_sdp_config
import distributed
import sys

# Initialise logging
logging.basicConfig()
log = logging.getLogger('testdask')
log.setLevel(logging.INFO)

# Obtain connection to configuration database. This is the main way to
# both obtain information about what the workflow is supposed to do,
# and its way to request actions from the rest of the system (e.g. ask
# for deployments of additional software)
config = ska_sdp_config.Config()

# Find processing block configuration from the configuration. Normally
# this workflow should only get started once one is available, and we
# just pull the ID from an environment variable here. But because the
# infrastructure isn't there yet, for the moment workflows are started
# speculatively, and wait until they spot a matching processing block
# in the configuration.


def main(argv):
    pb_id = argv[0]

    # Note that this process "claims" the workfow with a lease. This
    # means that once a processing block has been claimed, this script
    # must check in with the configuration database every ~10 seconds
    # or will be declared dead (and presumably restarted). This
    # obviously means that no serious work should actually happen here.
    for txn in config.txn():
        txn.take_processing_block(pb_id, config.client_lease)
        pb = txn.get_processing_block(pb_id)

    # Show
    log.info("Claimed processing block %s", pb)

    # Deploy Dask with 2 workers.
    # This is done by adding the request to the configuration database,
    # where it will be picked up and executed by appropriate
    # controllers. In the full system this will involve external checks
    # for whether the workflow actually has been assigned enough resources
    # to do this - and for obtaining such assignments the workflow would
    # need to communicate with a scheduler process. But we are ignoring
    # all of that at the moment.
    log.info("Deploying Dask...")
    deploy_id = pb.pb_id + "-dask"
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
        log.info("Waiting for Dask...")
        client = None
        for _ in range(200):
            try:
                client = distributed.Client(
                    deploy_id + '-scheduler.' +
                    os.environ['SDP_HELM_NAMESPACE'] + ':8786')
            except Exception as e:
                print(e)
        if client is None:
            log.error("Could not connect to Dask!")
            exit(1)
        log.info("Connected to Dask")

        # Now we can use Dask to do some calculations. Let's use a silly
        # example from the documentation.
        def inc(x):
            return x + 1
        L = client.map(inc, range(1000))
        log.info("Dask results: {}".format(client.gather(L)))

        # Just idle until processing block or we lose ownership
        log.info("Done, now idling...")
        for txn in config.txn():
            if not txn.is_processing_block_owner(pb.pb_id):
                break
            txn.loop(True)

    finally:

        # Clean up Dask deployment. This should also become semi-optional
        # eventually, as clearly the processing controller should learn to
        # free all deploymts associated with a workflow if it terminates
        # for whatever reason.
        for txn in config.txn():
            txn.delete_deployment(deploy)

        config.close()

if __name__ == "__main__":
    main(sys.argv[1:])
