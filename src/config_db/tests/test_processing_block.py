"""High-level API tests on processing blocks."""

import os
import pytest

from ska_sdp_config import config, entity, backend

# pylint: disable=missing-docstring,redefined-outer-name

PREFIX = "/__test_pb"

WORKFLOW = {
    'name': 'test_rt_workflow',
    'version': '0.0.1',
    'type': 'realtime'
}


# pylint: disable=W0212
@pytest.fixture(scope="session")
def cfg():
    host = os.getenv('SDP_TEST_HOST', '127.0.0.1')
    with config.Config(global_prefix=PREFIX, host=host) as cfg:
        cfg._backend.delete(PREFIX, must_exist=False, recursive=True)
        yield cfg
        cfg._backend.delete(PREFIX, must_exist=False, recursive=True)


def test_create_pb(cfg):

    # Create 3 processing blocks
    for txn in cfg.txn():

        pb1_id = txn.new_processing_block_id(WORKFLOW['type'])
        pb1 = entity.ProcessingBlock(pb1_id, None, WORKFLOW)
        txn.create_processing_block(pb1)
        with pytest.raises(backend.Collision):
            txn.create_processing_block(pb1)

        pb2_id = txn.new_processing_block_id(WORKFLOW['type'])
        pb2 = entity.ProcessingBlock(pb2_id, None, WORKFLOW)
        txn.create_processing_block(pb2)

        pb_ids = txn.list_processing_blocks()
        assert(pb_ids == [pb1_id, pb2_id])

    # Make sure that it stuck
    for txn in cfg.txn():
        pb_ids = txn.list_processing_blocks()
        assert(pb_ids == [pb1_id, pb2_id])

    # Make sure we can update them
    for txn in cfg.txn():
        pb1.parameters['test'] = 'test'
        pb1.scan_parameters['12345'] = {
            'test_scan': 'asd'
        }
        txn.update_processing_block(pb1)


def test_take_pb(cfg):

    workflow2 = dict(WORKFLOW)
    workflow2['name'] += "-take"

    # Create another processing block
    for txn in cfg.txn():

        pb_id = txn.new_processing_block_id(workflow2['type'])
        pb = entity.ProcessingBlock(pb_id, None, workflow2)
        txn.create_processing_block(pb)

    with cfg.lease() as lease:

        for txn in cfg.txn():
            txn.take_processing_block(pb_id, lease)

        for txn in cfg.txn():
            assert txn.get_processing_block_owner(pb_id) == cfg.owner
            assert txn.is_processing_block_owner(pb_id)

    for txn in cfg.txn():
        assert txn.get_processing_block_owner(pb_id) is None
        assert not txn.is_processing_block_owner(pb_id)

    # Test that we can find the processing block by workflow
    with cfg.lease() as lease:
        for txn in cfg.txn():
            pb2 = txn.take_processing_block_by_workflow(workflow2, lease)
            assert pb2.pb_id == pb_id

    for txn in cfg.txn():
        assert txn.get_processing_block_owner(pb_id) is None
        assert not txn.is_processing_block_owner(pb_id)


if __name__ == '__main__':
    pytest.main()
