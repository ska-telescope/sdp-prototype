import logging
import os

from processing_controller import processing_controller
from processing_controller.workflows import LOG

import ska_sdp_config
import workflows_test

for handler in logging.root.handlers:
    logging.root.removeHandler(handler)

logging.basicConfig(level=logging.DEBUG)
LOG.setLevel(logging.DEBUG)

os.environ['SDP_CONFIG_BACKEND'] = 'memory'
os.environ['SDP_CONFIG_HOST'] = 'localhost'
os.environ['SDP_HELM_NAMESPACE'] = 'helm'


def test_stuff():
    controller = processing_controller.ProcessingController(workflows_test.SCHEMA,
                                                            workflows_test.WORKFLOWS, 1)

    # Annoyingly requests doesn't support local (file) URLs, so redirect. It is possible to
    # create an adapter for this, but that seems like overkill.
    controller._workflows.update_url = controller._workflows.update_file

    wf = {'type': 'batch', 'id':  'test_batch', 'version': '0.2.1'}
    pb = ska_sdp_config.ProcessingBlock(
        id='test',
        sbi_id='test',
        workflow=wf,
        parameters={},
        dependencies=[]
    )

    config = ska_sdp_config.Config()

    for txn in config.txn():
        txn.create_processing_block(pb)

    controller.main()

    for txn in config.txn():
        deployment_ids = txn.list_deployments()

    LOG.info(deployment_ids)
    assert 'proc-test-workflow' in deployment_ids
