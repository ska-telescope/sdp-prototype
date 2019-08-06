"""
Helm deployment controller.

Applies/updates/deletes Helm releases depending on information from
the SDP configuration.
"""

# pylint: disable=C0103

import os
import subprocess
import shutil
import logging
import ska_sdp_config
from dotenv import load_dotenv
load_dotenv()

# Load environment
HELM = shutil.which(os.getenv('SDP_HELM', 'helm'))
HELM_TIMEOUT = int(os.getenv('SDP_HELM_TIMEOUT', str(300)))
HELM_REPO = os.getenv('SDP_HELM_REPO')
HELM_REPO_CA = os.getenv('SDP_HELM_REPO_CA')
NAMESPACE = os.getenv('SDP_HELM_NAMESPACE', 'sdp-helm')
LOGGER = os.getenv('SDP_LOGGER', 'main')
LOG_LEVEL = int(os.getenv('SDP_LOG_LEVEL', str(logging.DEBUG)))

# Initialise logger
logging.basicConfig()
log = logging.getLogger(LOGGER)
log.setLevel(LOG_LEVEL)


def helm_invoke(*args):
    """Invoke Helm with the given command-line arguments

    :returns: Output of the command
    :raises: `subprocess.CalledProcessError` if command returns an error status
    """
    cmd_line = [HELM] + list(args)
    # Perform call
    log.debug(" ".join(["$"] + cmd_line))
    result = subprocess.run(
        cmd_line, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=HELM_TIMEOUT)
    # Log results
    log.debug("Code: {}".format(result.returncode))
    out = result.stdout.decode()
    log.debug("-> " + out)
    result.check_returncode()
    return out


def delete_helm(txn, dpl_id):
    """Delete a Helm deployment."""

    # Try to delete
    log.info("Delete deployment {}...".format(dpl_id))

    try:
        helm_invoke('delete', dpl_id)
        return True
    except subprocess.CalledProcessError:
        return False # Assume it was already gone


def create_helm(txn, deploy):
    """Create a new Helm deployment."""

    # Attempt install
    dpl_id = deploy.deploy_id
    log.info("Creating deployment {}...".format(dpl_id))

    # Build command line
    cmd = ['install', deploy.args.get('chart'),
           '-n', dpl_id, '--namespace', NAMESPACE]
    if HELM_REPO is not None:
        cmd.extend(['--repo', HELM_REPO])
    if HELM_REPO_CA is not None:
        cmd.extend(['--ca-file', HELM_REPO_CA])

    # Encode any parameters
    if 'values' in deploy.args and isinstance(deploy.args, dict):
        val_str = ",".join(["{}={}".format(k,v) for
                            k,v in deploy.args['values'].items()])
        cmd.extend(['--set', val_str])

    # Make the call
    try:
        helm_invoke(*cmd)
        return True

    except subprocess.CalledProcessError as e:

        # Already exists? Purge
        if "already exists" in e.stdout.decode():
            try:
                log.info("Purging deployment {}...".format(dpl_id))
                helm_invoke('delete', '--purge', dpl_id)
                txn.loop()  # Force loop, this will cause a re-attempt
            except subprocess.CalledProcessError:
                log.error("Could not purge deployment {}!".format(dpl_id))
        else:
            log.error("Could not create deployment {}!".format(dpl_id))

    return False



def main():
    """Main loop of Helm controller."""

    # Instantiate configuration
    client = ska_sdp_config.Config()

    # TODO: Service lease + leader election

    # Reload Helm repo (only once currently)
    helm_invoke("init", "--client-only")
    helm_invoke("repo", "update")

    # Show
    log.info("Loading helm deployments...")

    # Query helm for active deployments. Filter for active ones.
    deploys = helm_invoke('list', '-q', '--namespace', NAMESPACE).split('\n')
    deploys = set(deploys).difference(set(['']))
    log.info("Found {} existing deployments.".format(len(deploys)))

    # Wait for something to happen
    for txn in client.txn():

        # List deployments
        target_deploys = txn.list_deployments()

        # Check for deployments that we should delete
        for dpl_id in list(deploys):
            if dpl_id not in target_deploys:
                if delete_helm(txn, dpl_id):
                    deploys.remove(dpl_id)

        # Check for deployments we should add
        for dpl_id in target_deploys:
            if dpl_id not in deploys:

                # Get details
                try:
                    deploy = txn.get_deployment(dpl_id)
                except ValueError as e:
                    log.warning("Deployment {} failed validation: {}!".format(
                        dpl_id, str(e)))
                    continue

                # Right type?
                if deploy.type != 'helm':
                    continue

                # Create it
                if create_helm(txn, deploy):
                    deploys.add(dpl_id)

        # Loop around, wait if we made no change
        txn.loop(wait=True)


main()
