"""
Example real-time SDP workflow.

Just waits for matching configuration to appear in the configuration,
and holds it until it gets removed. Parameters will be translated into
deployments.

For example, the following parameters will result in a sleeping
process and Kubernetes pod to be created:

  sleeper:
    type: process-direct
    args:
      args:
      - sleep infinity
      shell: True
  kube:
    args:
      apiVersion: v1
      kind: Pod
      metadata:
        name: sleeper
      spec:
        containers:
        - command:
          - /bin/sh
          - -c
          - sleep infinity
          image: busybox
          name: sleeper
    type: kubernetes-direct
"""

# pylint: disable=C0103

import logging
import ska_sdp_config
import sys

logging.basicConfig()
log = logging.getLogger('testdeploy')
log.setLevel(logging.INFO)

# Instantiate configuration
client = ska_sdp_config.Config()


def make_deployment(dpl_name, dpl_args, pb_id):
    """Make a deployment given PB parameters."""
    return ska_sdp_config.Deployment(pb_id + "-" + dpl_name, **dpl_args)


def main(argv):
    pb_id = argv[0]
    for txn in client.txn():
        pb = txn.get_processing_block(pb_id)
        txn.take_processing_block(pb_id, client.client_lease)

    # Show
    log.info("Claimed processing block %s", pb)

    try:
        # Wait for something to happen
        deploys = {}
        for txn in client.txn():
            if not txn.is_processing_block_owner(pb_id):
                log.warning("Lost processing block ownership")
                break

            # Get current processing block info (for realtime processing
            # blocks scan data might get updated)
            pb = txn.get_processing_block(pb_id)
            if pb is None:
                log.warning("Processing block got deleted")
                break

            # Check for deployments we need to undo
            dirty = False
            for dpl_name, dpl_args in deploys.items():
                if dpl_args != pb.parameters.get(dpl_name):
                    deploy = make_deployment(dpl_name, dpl_args)
                    log.info("Delete deployment {}".format(dpl_name))
                    txn.delete_deployment(deploy)
                    del deploys[dpl_name]
                    dirty = True
                    break
            if dirty:
                txn.loop()
                continue

            # Create new deployments
            for dpl_name, dpl_args in pb.parameters.items():

                # Get deployments, ignoring ones that don't fit
                try:
                    deploy = make_deployment(dpl_name, dpl_args)
                except ValueError as e:
                    log.warning("Deployment {} failed validation: {}".format(
                        dpl_name, str(e)))
                    continue

                # Up-to-date?
                if deploys.get(dpl_name) == dpl_args:
                    continue

                # Deploy anew
                txn.create_deployment(deploy)
                log.info("Created deployment {}".format(dpl_name))
                deploys[dpl_name] = dpl_args
                dirty = True
                break

            # Loop around, wait if we made no change
            txn.loop(wait=not dirty)

    finally:
        for txn in client.txn():
            for dpl_name, dpl_args in deploys.items():
                txn.delete_deployment(make_deployment(dpl_name, dpl_args, pb_id))


if __name__ == "__main__":
    main(sys.argv[1:])
