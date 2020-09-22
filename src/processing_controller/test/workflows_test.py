import logging
from pathlib import Path

from ska.logging import configure_logging
from processing_controller import processing_controller

configure_logging()
LOG = logging.getLogger(__name__)

PC_DIR = Path(processing_controller.__file__).parent
TEST_DIR = Path(__file__).parent
SCHEMA = PC_DIR / 'schema' / 'workflows.json'
WORKFLOWS = TEST_DIR / 'data' / 'workflows.json'


def test_with_nonexistent_file():
    wf = processing_controller.Workflows('not_there.json')
    assert wf.version == {}


def test_with_non_json():
    wf = processing_controller.Workflows(PC_DIR / 'workflows.py')
    assert wf.version == {}


def test_with_bad_json():
    wf = processing_controller.Workflows(WORKFLOWS)
    assert wf.version == {}


def test_before_update():
    wf = processing_controller.Workflows(SCHEMA)
    assert wf.version == {}


def test_workflows_version():
    wf = processing_controller.Workflows(SCHEMA)
    wf.update_file(WORKFLOWS)
    assert wf.version['date-time'].startswith('20')
