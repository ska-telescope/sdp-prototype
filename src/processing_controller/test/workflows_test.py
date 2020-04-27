import logging
from pathlib import Path
from processing_controller import processing_controller

LOG = logging.getLogger(__name__)
PRJ_ROOT = str(Path(processing_controller.__file__).parent)
SRC_ROOT = str(Path(processing_controller.__file__).parent.parent.parent)
SDP_ROOT = str(Path(processing_controller.__file__).parent.parent)
SCHEMA = PRJ_ROOT+"/schema/workflows.json"

def test_without_json():
    wf = processing_controller.Workflows("not_there.json")
    assert wf.version == {}


def test_bad_json():
    wf = processing_controller.Workflows(PRJ_ROOT+"/workflows.py")
    assert wf.version == {}


def test_with_json():
    wf = processing_controller.Workflows(SCHEMA)
    assert wf.version == {}


def test_scan():
    wf = processing_controller.Workflows(SCHEMA)
    wf.update_file(SDP_ROOT+"/examples/scan.json")
    assert wf.version == {}


def test_workflow():
    wf = processing_controller.Workflows(SCHEMA)
    wf.update_file(SRC_ROOT+"/workflows/workflows.json")
    assert wf.version['date-time'].startswith('2019')
