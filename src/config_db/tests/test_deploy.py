"""High-level API tests for deployments."""

import os
import time
import yaml

import pytest
import kubernetes
from ska_sdp_config import config, entity

# pylint: disable=missing-docstring,redefined-outer-name

PREFIX = "/__test_deploy"

# pylint: disable=W0212
@pytest.fixture(scope="session")
def cfg():
    host = os.getenv('SDP_TEST_HOST', '127.0.0.1')
    with config.Config(global_prefix=PREFIX, host=host) as cfg:
        cfg._backend.delete(PREFIX, must_exist=False, recursive=True)
        yield cfg
        cfg._backend.delete(PREFIX, must_exist=False, recursive=True)


def test_deploy_name():

    # Simple check that validation is there
    with pytest.raises(ValueError, match="deployment type"):
        entity.Deployment('asd', 'asdasd', {})
    with pytest.raises(ValueError, match="Deployment ID"):
        entity.Deployment('asd_', 'helm', {})
    entity.Deployment('asd', 'helm', {})


def test_deploy_process(cfg):

    # Make deployment
    deploy = entity.Deployment('deploy-test', 'process-direct', {
        'args': ['echo Hello World!'], 'shell': True
    })
    for txn in cfg.txn():
        txn.create_deployment(deploy)
        assert txn.get_deployment(deploy.deploy_id).to_dict() == \
            deploy.to_dict()
    time.sleep(0.1)
    assert cfg.get_deployment_logs(deploy) == [b'Hello World!\n']
    for txn in cfg.txn():
        assert txn.get_deployment(deploy.deploy_id).to_dict() == \
            deploy.to_dict()
        txn.delete_deployment(deploy)


def test_deploy_process_log_limit(cfg):

    # Make deployment
    deploy = entity.Deployment('deploy-test-loglimit', 'process-direct', {
        'args': ['for i in $(seq 0 999); do echo $i; done'],
        'shell': True
    })

    for txn in cfg.txn():
        txn.create_deployment(deploy)
    time.sleep(0.1)
    # Test that we can can obtain last 100 lines of log
    assert cfg.get_deployment_logs(deploy, 100) == [
        '{}\n'.format(i).encode() for i in range(900, 1000)
    ]
    for txn in cfg.txn():
        txn.delete_deployment(deploy)


def test_deploy_kill(cfg):

    # Make deployment
    for wait_time in [0, 1]:
        deploy = entity.Deployment('deploy-test-loglimit', 'process-direct', {
            'args': ['echo Enter; sleep {}; echo Exit'.format(wait_time)],
            'shell': True
        })
        for txn in cfg.txn():
            txn.create_deployment(deploy)
        time.sleep(0.01)
        for txn in cfg.txn():
            txn.delete_deployment(deploy)

        # Note that we are relying on the logs to be available even
        # after the deployment was removed...
        if wait_time > 0:
            assert cfg.get_deployment_logs(deploy, 100) == [b'Enter\n']
        else:
            assert cfg.get_deployment_logs(deploy, 100) == \
                [b'Enter\n', b'Exit\n']


def _have_kubernetes():

    # Try in-cluster configuration
    try:
        kubernetes.config.load_incluster_config()
        return True
    except kubernetes.config.ConfigException:
        pass

    # Try kube.conf
    try:
        kubernetes.config.load_kube_config()
        return True
    except kubernetes.config.ConfigException:
        pass
    except TypeError:
        # Happens when there is no configuration at all for some reason
        pass
    return False


@pytest.mark.skipif(not _have_kubernetes(), reason="need Kubernetes")
def test_deploy_kube(cfg):

    hello_world_yaml = """
apiVersion: v1
kind: Pod
metadata:
  name: test--deploy-kube
  namespace: default
spec:
  containers:
  - image: hello-world
    name: hello-world
"""
    deployment = entity.Deployment('deploy-test-kube', 'kubernetes-direct',
                                   yaml.safe_load(hello_world_yaml))

    # Make deployment
    try:
        for txn in cfg.txn():
            txn.create_deployment(deployment)
    except kubernetes.utils.FailToCreateError as exc:
        if exc.api_exceptions[0].reason != 'Conflict':
            raise
        # Already exists, likely from a previous failed test. It will
        # have been added to the configuration at this point, so we
        # can just continue as normal.

    # Wait up to 30 seconds for the pod to materialise
    logs = []
    for _ in range(30):
        time.sleep(1)
        try:
            logs = cfg.get_deployment_logs(deployment)
            break
        except kubernetes.client.rest.ApiException as api_exc:
            if "waiting to start" in api_exc.body:
                continue  # Wait
            raise
    assert "Hello from Docker!" in logs

    # Delete deployment
    for txn in cfg.txn():
        txn.delete_deployment(deployment)


if __name__ == '__main__':
    pytest.main()
