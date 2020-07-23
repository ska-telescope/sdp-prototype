import os
from unittest.mock import patch, mock_open

import helm_deploy as deploy
from ska_sdp_config import Config, Deployment


deploy.HELM = '/bin/helm'
deploy.GIT = '/bin/git'


@patch('subprocess.run')
def test_invoke(mock_run):
    deploy.invoke('ls')
    mock_run.assert_called_once()


@patch('subprocess.run')
def test_delete(mock_run):
    deploy.delete_helm('test', '0')
    mock_run.assert_called_once()


@patch('subprocess.run')
def test_create(mock_run):
    config = Config(backend='memory')

    for txn in config.txn():
        txn.create_deployment(
            Deployment('test', 'helm', {'chart': 'test', 'values': {'test': 'test'}})
        )

    for txn in config.txn():
        deployment = txn.get_deployment('test')
        deploy.create_helm(txn, 'test', deployment)

    mock_run.assert_called_once()

