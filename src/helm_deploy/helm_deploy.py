"""
Helm deployment controller.

Applies/updates/deletes Helm releases depending on information from
the SDP configuration.
"""

# pylint: disable=C0103

import os
import time
import subprocess
import signal
import shutil
import ska_sdp_config
from ska_sdp_logging import core_logging
from dotenv import load_dotenv
load_dotenv()

# Load environment
HELM = shutil.which(os.getenv('SDP_HELM', 'helm'))
HELM_TIMEOUT = int(os.getenv('SDP_HELM_TIMEOUT', str(300)))
HELM_REPO = os.getenv('SDP_HELM_REPO')
HELM_REPO_CA = os.getenv('SDP_HELM_REPO_CA')
NAMESPACE = os.getenv('SDP_HELM_NAMESPACE', 'sdp')
LOG_LEVEL = os.getenv('SDP_LOG_LEVEL', 'DEBUG')

GIT = shutil.which(os.getenv("SDP_GIT", 'git'))
CHART_REPO = os.getenv('SDP_CHART_REPO', 'https://github.com/ska-telescope/sdp-prototype.git')
CHART_REPO_REF = os.getenv('SDP_CHART_REPO_REF', 'master')
CHART_REPO_PATH = os.getenv('SDP_CHART_REPO_PATH', 'deploy/charts')
CHART_REPO_REFRESH = int(os.getenv('SDP_CHART_REFRESH', '300'))

# Initialise logger
log = core_logging.init(name='helm_deploy', level=LOG_LEVEL)

# Where we are going to check out the charts
chart_base_path = 'chart-repo'
chart_path = os.path.join(chart_base_path, CHART_REPO_PATH)


def invoke(*cmd_line, cwd):
    """Invoke a command with the given command-line arguments

    :param cwd: Directory to run command in
    :returns: Output of the command
    :raises: `subprocess.CalledProcessError` if command returns an error status
    """
    # Perform call
    log.debug(" ".join(["$"] + list(cmd_line)))
    result = subprocess.run(
        cmd_line, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=HELM_TIMEOUT,
        cwd=cwd)
    # Log results
    log.debug("Code: {}".format(result.returncode))
    out = result.stdout.decode()
    for line in out.splitlines():
        log.debug("-> " + line)
    result.check_returncode()
    return out


def helm_invoke(*args):
    """Invoke Helm with the given command-line arguments

    :returns: Output of the command
    :raises: `subprocess.CalledProcessError` if command returns an error status
    """
    return invoke(*([HELM] + list(args)), cwd=chart_path)


def update_chart_repos():
    """Update the chart repository."""
    # Does not exist? Initialise
    if not os.path.exists(chart_base_path):
        log.info("Initialising chart repos in {}".format(chart_path))
        os.mkdir(chart_base_path)
        invoke(GIT, "init", cwd=chart_base_path)
        invoke(GIT, "config", "core.sparseCheckout", "true",
               cwd=chart_base_path)
        with open(os.path.join(chart_base_path, ".git", "info",
                               "sparse-checkout"), "w") as f:
            print(CHART_REPO_PATH, file=f)
        invoke(GIT, "remote", "add", "origin", CHART_REPO,
               cwd=chart_base_path)
        invoke(GIT, "fetch", "--depth", "1", "origin", CHART_REPO_REF,
               cwd=chart_base_path)
        invoke(GIT, "checkout", CHART_REPO_REF,
               cwd=chart_base_path)
    else:
        log.info("Refreshing chart repos in {}".format(chart_path))
        invoke(GIT, "pull", "origin", CHART_REPO_REF,
               cwd=chart_base_path)


def delete_helm(txn, dpl_id):
    """Delete a Helm deployment."""

    # Try to delete
    log.info("Delete deployment {}...".format(dpl_id))

    try:
        helm_invoke('uninstall', dpl_id, '-n', NAMESPACE)
        return True
    except subprocess.CalledProcessError:
        return False # Assume it was already gone


def create_helm(txn, dpl_id, deploy):
    """Create a new Helm deployment."""

    # Attempt install
    log.info("Creating deployment {}...".format(dpl_id))

    # Build command line
    cmd = ['install', dpl_id, deploy.args.get('chart'),
           '-n', NAMESPACE]
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
                helm_invoke('uninstall', dpl_id, '-n', NAMESPACE)
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

    # Obtain charts
    update_chart_repos()
    next_chart_refresh = time.time() + CHART_REPO_REFRESH

    # Load Helm repository
    helm_invoke("repo", "add", "stable", "https://kubernetes-charts.storage.googleapis.com/")
    helm_invoke("repo", "update")

    # Show
    log.info("Loading helm deployments...")

    # Query helm for active deployments. Filter for active ones.
    deploys = helm_invoke('list', '-q', '-n', NAMESPACE).split('\n')
    deploys = set(deploys).difference(set(['']))
    log.info("Found {} existing deployments.".format(len(deploys)))

    # Wait for something to happen
    for txn in client.txn():

        # Refresh charts?
        if time.time() > next_chart_refresh:
            next_chart_refresh = time.time() + CHART_REPO_REFRESH

            try:
                helm_invoke("repo", "update")
            except subprocess.CalledProcessError as e:
                log.error("Could not refresh global chart repository!")

            try:
                update_chart_repos()
            except subprocess.CalledProcessError as e:
                log.error("Could not refresh chart repository!")

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
                if create_helm(txn, dpl_id, deploy):
                    deploys.add(dpl_id)

        # Loop around, wait if we made no change
        txn.loop(wait=True, timeout=next_chart_refresh - time.time())



def terminate(signal, frame):
    """Terminate the program."""
    log.info("Asked to terminate")
    exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, terminate)
    main()
