"""
Module for applying deployments.

This is temporary - clearly the configuration database back-end should
not handle creating containers and processes itself.
"""

import subprocess
import time
import threading
import queue

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
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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

    else:
        raise ValueError("Unsupported deployment type {}!".format(
            dpl.type))

def get_deployment_logs(dpl: Deployment, max_lines: int = 500):
    """
    Query logs associated with a deployment

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
    else:
        raise ValueError("Unsupported deployment type {}!".format(
            dpl.type))
    
