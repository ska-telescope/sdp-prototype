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
                                                            workflows_test.WORKFLOW, 1)
    controller._workflows.update_file(workflows_test.WORKFLOW)

    wf = {'type': 'batch', 'id':  'test_batch', 'version': '0.2.0'}
    pb = ska_sdp_config.ProcessingBlock(
        id='pb-sdptest-20200703-test',
        sbi_id='test',
        workflow=wf,
        parameters={},
        dependencies=[]
    )

    config = ska_sdp_config.Config()

    for txn in config.txn():
        txn.create_processing_block(pb)

    controller.run(config, False)

    for txn in config.txn():
        deployment_ids = txn.list_deployments()

    LOG.info(deployment_ids)
    assert 'proc-pb-sdptest-20200703-test-workflow' in deployment_ids
