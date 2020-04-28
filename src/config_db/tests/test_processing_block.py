"""High-level API tests on processing blocks."""

import os
import pytest

from ska_sdp_config import config, entity, backend

# pylint: disable=missing-docstring,redefined-outer-name

PREFIX = "/__test_pb"

WORKFLOW = {
    'type': 'realtime',
    'id': 'test_rt_workflow',
    'version': '0.0.1'
}


# pylint: disable=W0212
@pytest.fixture(scope="session")
def cfg():
    host = os.getenv('SDP_TEST_HOST', '127.0.0.1')
    with config.Config(global_prefix=PREFIX, host=host) as cfg:
        cfg._backend.delete(PREFIX, must_exist=False, recursive=True)
        yield cfg
        cfg._backend.delete(PREFIX, must_exist=False, recursive=True)


def test_simple_pb():

    for missing in ['id', 'version', 'type']:
        with pytest.raises(ValueError, match="Workflow must"):
            workflow = dict(WORKFLOW)
            del workflow[missing]
            entity.ProcessingBlock('foo-bar', None, workflow)
    with pytest.raises(ValueError, match="Processing block ID"):
        entity.ProcessingBlock('asd_htb', None, WORKFLOW)
    with pytest.raises(ValueError, match="Processing block ID"):
        entity.ProcessingBlock('foo/bar', None, WORKFLOW)

    pb = entity.ProcessingBlock('foo-bar', None, WORKFLOW)
    # pylint: disable=W0123
    assert pb == eval('entity.' + repr(pb))


def test_create_pb(cfg):

    # Create 3 processing blocks
    for txn in cfg.txn():

        pb1_id = txn.new_processing_block_id('test')
        pb1 = entity.ProcessingBlock(pb1_id, None, WORKFLOW)
        assert txn.get_processing_block(pb1_id) is None
        txn.create_processing_block(pb1)
        with pytest.raises(backend.ConfigCollision):
            txn.create_processing_block(pb1)
        assert txn.get_processing_block(pb1_id).id == pb1_id

        pb2_id = txn.new_processing_block_id('test')
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
        pb1.dependencies.append({
            'pbId': pb2_id,
            'type': []
        })
        txn.update_processing_block(pb1)

    # Check that update worked
    for txn in cfg.txn():
        pb1x = txn.get_processing_block(pb1.id)
        assert pb1x.sbi_id is None
        assert pb1x.parameters == pb1.parameters
        assert pb1x.dependencies == pb1.dependencies


def test_take_pb(cfg):

    workflow2 = dict(WORKFLOW)
    workflow2['id'] += "-take"

    # Create another processing block
    for txn in cfg.txn():

        pb_id = txn.new_processing_block_id('test')
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


def test_pb_state(cfg):

    pb_id = 'teststate-00000000-0000'
    state1 = {
        "resources_available": True,
        "state": "RUNNING",
        "receive_addresses": {
            "1": {
                "1": ["0.0.0.0", 1024]
            }
        }
    }
    state2 = {
        "resources_available": True,
        "state": "FINISHED",
        "receive_addresses": {
            "1": {
                "1": ["0.0.0.0", 1024]
            }
        }
    }

    # Create processing block
    for txn in cfg.txn():
        pb = entity.ProcessingBlock(pb_id, None, WORKFLOW)
        txn.create_processing_block(pb)

    # Check PB state is None
    for txn in cfg.txn():
        state_out = txn.get_processing_block_state(pb_id)
        assert state_out is None

    # Create PB state as state1
    for txn in cfg.txn():
        txn.create_processing_block_state(pb_id, state1)

    # Read PB state and check it matches state1
    for txn in cfg.txn():
        state_out = txn.get_processing_block_state(pb_id)
        assert state_out == state1

    # Try to create PB state again and check it raises a collision exception
    for txn in cfg.txn():
        with pytest.raises(backend.ConfigCollision):
            txn.create_processing_block_state(pb_id, state1)

    # Update PB state to state2
    for txn in cfg.txn():
        txn.update_processing_block_state(pb_id, state2)

    # Read PB state and check it now matches state2
    for txn in cfg.txn():
        state_out = txn.get_processing_block_state(pb_id)
        assert state_out == state2


if __name__ == '__main__':
    pytest.main()
