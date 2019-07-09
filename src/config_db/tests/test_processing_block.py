
from ska_sdp_config import config

import pytest

prefix = "/__test_pb"

@pytest.fixture(scope="session")
def cfg():
    cfg = config.Config(global_prefix=prefix)
    cfg._backend.delete(prefix, must_exist=False, recursive=True)
    return cfg

def test_create_pb(cfg):

    workflow = {
        'name': 'test_rt_workflow',
        'version': '0.0.1',
        'type': 'realtime'
    }

    # Create 3 processing blocks
    pb1 = cfg.create_pb(workflow)
    pb2 = cfg.create_pb(workflow)
    pb3 = cfg.create_pb(workflow)

    # Must have unique IDs
    assert(len(set([pb1.pb_id, pb2.pb_id, pb3.pb_id])) == 3)
