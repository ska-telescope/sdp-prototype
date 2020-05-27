import logging

from processing_controller import processing_controller
from processing_controller.workflows import LOG
from ska_sdp_config.backend import Memory
import workflows_test

for handler in logging.root.handlers:
    logging.root.removeHandler(handler)

logging.basicConfig(level=logging.DEBUG)
LOG.setLevel(logging.DEBUG)

def test_stuff():
    controller = processing_controller.ProcessingController(workflows_test.SCHEMA,
                                                            workflows_test.WORKFLOW, 1)

    LOG.info("log level %s", LOG.getEffectiveLevel())
    # Annoyingly requests doesn't support local (file) URLs, so redirect. It is possible to
    # create an adapter for this, but that seems like overkill.
    controller._workflows.update_url = controller._workflows.update_file

    controller.main(backend=Memory())
