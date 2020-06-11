import logging
from pathlib import Path
from processing_controller import processing_controller

LOG = logging.getLogger(__name__)
FILE = Path(processing_controller.__file__)
PRJ_ROOT = str(FILE.parent)
SDP_ROOT = str(FILE.parent.parent)
SRC_ROOT = str(FILE.parent.parent.parent)
SCHEMA = PRJ_ROOT+"/schema/workflows.json"
WORKFLOW = SRC_ROOT+"/workflows/workflows.json"
WORK_URL = Path(WORKFLOW).as_uri()

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
    wf.update_file(WORKFLOW)
    assert wf.version['date-time'].startswith('20')
