import logging
from pathlib import Path
from processing_controller import processing_controller

LOG = logging.getLogger(__name__)
ROOT = str(Path(processing_controller.__file__).parent)


def test_without_json():
    wf = processing_controller.Workflows("not_there.json")
    assert wf.version == {}


def test_bad_json():
    wf = processing_controller.Workflows(ROOT+"/workflows.py")
    assert wf.version == {}


def test_with_json():
    wf = processing_controller.Workflows(ROOT+"/schema/workflows.json")
    assert wf.version == {}
