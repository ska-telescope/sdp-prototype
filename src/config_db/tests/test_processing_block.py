
from ska_sdp_config import config
from ska_sdp_config import entity

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
    for txn in cfg.txn():

        pb1_id = txn.new_processing_block_id(workflow['type'])
        txn.create(entity.ProcessingBlock(pb1_id, None, workflow))

        pb2_id = txn.new_processing_block_id(workflow['type'])
        txn.create(entity.ProcessingBlock(pb2_id, None, workflow))

        pb3_id = txn.new_processing_block_id(workflow['type'])
        txn.create(entity.ProcessingBlock(pb3_id, None, workflow))

        assert(len(set([pb1_id, pb2_id, pb3_id])) == 3)

if __name__ == '__main__':
    pytest.main()
