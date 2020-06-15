import os
from unittest.mock import patch, mock_open

import helm_deploy as deploy
from ska_sdp_config import Config
from ska_sdp_config.entity import Deployment
from ska_sdp_config.memory_backend import MemoryBackend


deploy.HELM = '/bin/helm'
deploy.GIT = '/bin/git'


@patch('subprocess.run')
def test_invoke(mock_run):
    deploy.invoke('ls', cwd='.')
    mock_run.assert_called_once()


@patch('os.mkdir')
@patch('subprocess.run')
def test_update(mock_run, mock_mkdir):
    with patch('builtins.open', mock_open()):
        deploy.update_chart_repos()
    assert mock_run.call_count == 5
    assert not os.path.exists(deploy.chart_base_path)


@patch('subprocess.run')
def test_delete(mock_run):
    deploy.delete_helm('test', '0')
    mock_run.assert_called_once()


@patch('subprocess.run')
def test_create(mock_run):
    config = Config(backend=MemoryBackend())
    for txn in config.txn():
        txn.create_deployment(
            Deployment('test', 'helm',
                       {'values': {'test': 'test'}, 'chart': 'test'}))
    deployment = txn.get_deployment('test')
    deploy.create_helm(txn, 'test', deployment)
    mock_run.assert_called_once()

