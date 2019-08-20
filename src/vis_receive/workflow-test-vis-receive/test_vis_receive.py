"""
Example Vis Receive workflow
"""

# pylint: disable=C0103

import logging
import ska_sdp_config
import distributed
import os

# Initialise logging
logging.basicConfig()
log = logging.getLogger('main')
log.setLevel(logging.INFO)

# Obtain connection to configuration database. This is the main way to
# both obtain information about what the workflow is supposed to do,
# and its way to request actions from the rest of tska_sdp_confighe system (e.g. ask
# for deployments of additional software)
config = ska_sdp_config.Config()

# Find processing block configuration from the configuration. Normally
# this workflow should only get started once one is available, and we
# just pull the ID from an environment variable here. But because the
# infrastructure isn't there yet, for the moment workflows are started
# speculatively, and wait until they spot a matching processing block
# in the configuration.
workflow = {
    'id': 'testvisreceive',
    'version': '0.0.1',
    'type': 'realtime'
}
log.info("Waiting for processing block...")
for txn in config.txn():

    # Note that this process "claims" the workfow with a lease. This
    # means that once a processing block has been claimed, this script
    # must check in with the configuration database every ~10 seconds
    # or will be declared dead (and presumably restarted). This
    # obviously means that no serious work should actually happen here.
    pb = txn.take_processing_block_by_workflow(
        workflow, config.client_lease)
    if pb is not None:
        continue
    txn.loop(wait=True)

# Show
log.info("Claimed processing block %s", pb)

# Deploy Vis Receive with 1 worker.
#
# This is done by adding the request to the configuration database,
# where it will be picked up and executed by appropriate
# controllers. In the full system this will involve external checks
# for whether the workflow actually has been assigned enough resources
# to do this - and for obtaining such assignments the workflow would
# need to communicate with a scheduler process. But we are ignoring
# all of that at the moment.
log.info("Deploying Vis Receive...")
deploy_id = pb.pb_id + "-vis-receive"
deploy = ska_sdp_config.Deployment(
    deploy_id, "helm", {
        'chart': 'skaorca/vis_receive:latest',
        'values': {
            'config-host': os.environ['SDP_CONFIG_HOST'],
            'worker.replicas': 1
            # We want to access vis_receive in-cluster using a DNS name
            # 'scheduler.serviceType': 'ClusterIP'
        }})
for txn in config.txn():
    txn.create_deployment(deploy)
try:

    # Wait for vis receive to become available. At some point there will be a
    # way to learn about availability from the configuration database
    # (clearly populated by controllers querying Helm/Kubernetes).  So
    # for the moment we'll simply query the DNS name where we know
    # that vis receive must become available eventually
    log.info("Waiting for Vis Receive...")
    client = None
    for _ in range(200):
        try:
            client = distributed.Client(deploy_id+'-scheduler.sdp-helm:8786')
        except Exception as e:
            print(e)
    if client is None:
        log.error("Could not connect to Vis Receive!")
        exit(1)
    log.info("Connected to Vis Receive")

    # # Now we can use Dask to do some calculations. Let's use a silly
    # # example from the documentation.
    # def inc(x):
    #     return x + 1
    # L = client.map(inc, range(1000))
    # log.info("Dask results: {}".format(client.gather(L)))
    #
    # # Just idle until processing block or we lose ownership
    # log.info("Done, now idling...")
    # for txn in config.txn():
    #     if not txn.is_processing_block_owner(pb.pb_id):
    #         break
    #     txn.loop(True)

finally:

    # Clean up vis receive deployment. This should also become semi-optional
    # eventually, as clearly the processing controller should learn to
    # free all deployments associated with a workflow if it terminates
    # for whatever reason.
    for txn in config.txn():
        txn.delete_deployment(deploy)

    config.close()
