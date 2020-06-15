"""High-level API tests on scheduling blocks."""

import os
import pytest

import ska_sdp_config

# pylint: disable=missing-docstring,redefined-outer-name

PREFIX = "/__test_sb"


# pylint: disable=W0212
@pytest.fixture(scope="session")
def cfg():
    host = os.getenv('SDP_TEST_HOST', '127.0.0.1')
    with ska_sdp_config.Config(global_prefix=PREFIX, host=host) as cfg:
        cfg._backend.delete(PREFIX, must_exist=False, recursive=True)
        yield cfg
        cfg._backend.delete(PREFIX, must_exist=False, recursive=True)


def test_sb_list(cfg):
    sb1_id = 'foo'
    sb2_id = 'bar'

    # Check scheduling block list is empty
    for txn in cfg.txn():
        sb_ids = txn.list_scheduling_blocks()
        assert sb_ids == []

    # Create first scheduling block
    for txn in cfg.txn():
        txn.create_scheduling_block(sb1_id, {})

    # Check scheduling block list has entry
    for txn in cfg.txn():
        sb_ids = txn.list_scheduling_blocks()
        assert sb_ids == [sb1_id]

    # Create second scheduling block
    for txn in cfg.txn():
        txn.create_scheduling_block(sb2_id, {})

    # Check scheduling block list has both entries
    for txn in cfg.txn():
        sb_ids = txn.list_scheduling_blocks()
        assert sb_ids == sorted([sb1_id, sb2_id])


def test_sb_create_update(cfg):

    sb_id = '20200213-0001'
    state1 = {
        'scan_id': None,
        'pb_realtime': [],
        'pb_batch': [],
        'pb_receive_addresses': None
    }
    state2 = {
        'scan_id': 1,
        'pb_realtime': ['realtime-20200213-0001', 'realtime-20200213-0002'],
        'pb_batch': ['batch-20200213-0001', 'batch-20200213-0002'],
        'pb_receive_addresses': 'realtime-20200213-0001'
    }

    # Scheduling block has not been created, so should return None
    for txn in cfg.txn():
        state = txn.get_scheduling_block(sb_id)
        assert state is None

    # Create scheduling block as state1
    for txn in cfg.txn():
        txn.create_scheduling_block(sb_id, state1)

    # Read scheduling block and check it is equal to state1
    for txn in cfg.txn():
        state = txn.get_scheduling_block(sb_id)
        assert state == state1

    # Trying to recreate should raise a collision exception
    for txn in cfg.txn():
        with pytest.raises(ska_sdp_config.ConfigCollision):
            txn.create_scheduling_block(sb_id, state1)

    # Update scheduling block to state2
    for txn in cfg.txn():
        txn.update_scheduling_block(sb_id, state2)

    # Read scheduling block and check it is equal to state2
    for txn in cfg.txn():
        state = txn.get_scheduling_block(sb_id)
        assert state == state2


if __name__ == '__main__':
    pytest.main()
