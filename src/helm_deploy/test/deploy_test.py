import os
from unittest.mock import patch, mock_open
import helm_deploy as deploy


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
    # This one would benefit from the in-memory back-end
    pass
    #deploy.delete_helm('test', '0')
    #mock_run.assert_called_once()

