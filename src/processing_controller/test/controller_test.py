import os
import logging

from ska.logging import configure_logging
from processing_controller import processing_controller

import ska_sdp_config
import workflows_test

configure_logging()
LOG = logging.getLogger(__name__)

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
