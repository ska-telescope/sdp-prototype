"""High-level API tests for deployments."""

import os
import pytest
import time

from ska_sdp_config import config, entity, backend

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
            assert cfg.get_deployment_logs(deploy, 100) == [ b'Enter\n' ]
        else:
            assert cfg.get_deployment_logs(deploy, 100) == [ b'Enter\n', b'Exit\n' ]
