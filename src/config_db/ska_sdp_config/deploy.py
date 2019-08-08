"""
Module for applying deployments.

This is temporary - clearly the configuration database back-end should
not handle creating containers and processes itself.
"""

import subprocess
import time
import re
import tempfile
import json
import threading
import queue

import kubernetes
from .entity import Deployment

# Map of deployment ID to spawned subprocesses
_SUBPROCESS = {}
_MAX_HISTORY = 500


def apply_deployment(dpl: Deployment):
    """
    Create software processes/pods specified.

    :param dpl: Deployment details
    """
    if dpl.type == 'process-direct':

        # Spawn subprocess
        proc = subprocess.Popen(
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **dpl.args)

        # Spawn thread to watch stdout
        stdout_queue = queue.Queue(maxsize=_MAX_HISTORY)

        def stdout_thread():
            for line in proc.stdout:
                try:
                    stdout_queue.put_nowait(line)
                except queue.Full:
                    stdout_queue.get_nowait()
                    stdout_queue.put_nowait(line)

        stdout_thread = threading.Thread(target=stdout_thread)
        stdout_thread.start()

        # Remember
        _SUBPROCESS[dpl.deploy_id] = (proc, stdout_queue)

    elif dpl.type == 'kubernetes-direct':

        # Create client using either kube.conf or from environment
        # variables (which is appropriate for running in-cluster)
        try:
            kubernetes.config.load_incluster_config()
        except kubernetes.config.ConfigException:
            kubernetes.config.load_kube_config()

        # Create from dictionary
        client = kubernetes.client.ApiClient()

        # Write to file (with the next version of the Kubernetes
        # bindings we will be able to use create_from_json here)
        with tempfile.NamedTemporaryFile("w") as temp:
            json.dump(dpl.args, temp)
            temp.flush()
            kubernetes.utils.create_from_yaml(client, temp.name)
        del client

    elif dpl.type == 'helm':
        pass  # Handled by operator

    else:
        raise ValueError("Unsupported deployment type {}!".format(
            dpl.type))


def undo_deployment(dpl: Deployment):
    """
    Remove software processes/pods specified.

    :param dpl: Deployment details
    """
    if dpl.type == 'process-direct':
        if dpl.deploy_id not in _SUBPROCESS:
            raise ValueError(
                ("Deployment {} was not created by this " +
                 "process!").format(dpl.deploy_id))

        # Get subprocess, send SIGTERM
        proc = _SUBPROCESS[dpl.deploy_id][0]
        proc.poll()
        if proc.returncode is None:
            proc.terminate()

            # Wait for it to finish
            counter = 100
            while proc.returncode is None and counter > 0:
                time.sleep(0.1)
                proc.poll()
                counter -= 1
            # Eventually send SIGKILL
            if not proc.poll():
                proc.kill()

        # Wait to finish
        proc.wait()

    elif dpl.type == 'kubernetes-direct':
        data = dpl.args

        # Loosely adapted from create_from_dict
        client = kubernetes.client.ApiClient()
        if data["kind"] == "List":
            for obj in data["items"]:
                _undo_kube_deployment(client, obj)
        else:
            _undo_kube_deployment(client, data)
        del client

    elif dpl.type == 'helm':
        pass  # Handled by operator

    else:
        raise ValueError("Unsupported deployment type {}!".format(
            dpl.type))


def _undo_kube_deployment(k8s_client, yml_object):

    # ## Code determining API version + kind extracted from
    # ## kubernetes.utils.create_from_yaml.create_from_yaml_single_item

    group, _, version = yml_object["apiVersion"].partition("/")
    if version == "":
        version = group
        group = "core"
    # Take care for the case e.g. api_type is "apiextensions.k8s.io"
    # Only replace the last instance
    group = "".join(group.rsplit(".k8s.io", 1))
    # convert group name from DNS subdomain format to
    # python class name convention
    group = "".join(word.capitalize() for word in group.split('.'))
    fcn_to_call = "{0}{1}Api".format(group, version.capitalize())
    # pylint: disable=E1102
    k8s_api = getattr(kubernetes.client, fcn_to_call)(k8s_client)
    # Replace CamelCased action_type into snake_case
    kind = yml_object["kind"]
    kind = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', kind)
    kind = re.sub('([a-z0-9])([A-Z])', r'\1_\2', kind).lower()

    # ## Copied end

    metadata = yml_object['metadata']
    if hasattr(k8s_api, "delete_namespaced_{0}".format(kind)):
        return getattr(k8s_api, "delete_namespaced_{0}".format(kind))(
            metadata['name'], metadata.get('namespace'))
    return getattr(k8s_api, "delete_{0}")(metadata['name'])


def get_deployment_logs(dpl: Deployment, max_lines: int = 500):
    """
    Query logs associated with a deployment.

    :param dpl: Deployment details
    :param max_lines: Maximum number of lines to return (log tail)
    """
    if dpl.type == 'process-direct':

        if dpl.deploy_id not in _SUBPROCESS:
            raise ValueError(
                ("Deployment {} was not created by this " +
                 "process!").format(dpl.deploy_id))

        # Retrieve lines
        lines = list(_SUBPROCESS[dpl.deploy_id][1].queue)
        if len(lines) > max_lines:
            lines = lines[-max_lines:]
        return lines

    if dpl.type == 'kubernetes-direct':

        # Must be a pod deployment
        if dpl.args.get('kind') != 'Pod':
            raise ValueError("Can only retrieve logs from pod deployments!")

        # Make client
        client = kubernetes.client.ApiClient()
        api = kubernetes.client.CoreV1Api(client)

        # Ask for logs
        metadata = dpl.args['metadata']
        logs = api.read_namespaced_pod_log(
            metadata['name'], metadata.get('namespace', 'default'),
            tail_lines=max_lines)
        del client
        return logs

    raise ValueError("Unsupported deployment type {}!".format(
        dpl.type))
