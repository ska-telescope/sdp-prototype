import logging
import os

from processing_controller import processing_controller
from processing_controller.workflows import LOG
from ska_sdp_config.config import dict_to_json
from ska_sdp_config.memory_backend import MemoryBackend
import workflows_test

for handler in logging.root.handlers:
    logging.root.removeHandler(handler)

logging.basicConfig(level=logging.DEBUG)
LOG.setLevel(logging.DEBUG)

os.environ['SDP_CONFIG_HOST'] = 'localhost'
os.environ['SDP_HELM_NAMESPACE'] = 'helm'


def test_stuff():
    controller = processing_controller.ProcessingController(workflows_test.SCHEMA,
                                                            workflows_test.WORKFLOW, 1)

    LOG.info("log level %s", LOG.getEffectiveLevel())
    # Annoyingly requests doesn't support local (file) URLs, so redirect. It is possible to
    # create an adapter for this, but that seems like overkill.
    controller._workflows.update_url = controller._workflows.update_file

    wf = {"type": "batch", "id":  "test_batch", "repository": "nexus",
          "image": "workflow-test-batch", "version": "0.2.0"}
    pb = {"id": "test", "sbi_id": "test", "workflow": wf, "parameters": {}, "dependencies": []}

    backend = MemoryBackend()
    backend.create("/pb/test", dict_to_json(pb))

    controller.main(backend=backend)
    LOG.info(backend.list_keys('/deploy'))
    assert '/deploy/proc-test-workflow' in backend.list_keys('/deploy')
