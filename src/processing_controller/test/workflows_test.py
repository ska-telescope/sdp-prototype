import logging
from processing_controller import processing_controller

LOG = logging.getLogger(__name__)
LOG.info(processing_controller.__file__)


def test_stuff():
    wf = processing_controller.Workflows("schema/workflows.json")
    print(wf.version)
    print(wf._batch)

