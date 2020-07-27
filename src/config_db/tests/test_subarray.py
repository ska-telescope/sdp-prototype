"""High-level API tests on subarrays."""

import os
import pytest

import ska_sdp_config

# pylint: disable=missing-docstring,redefined-outer-name

PREFIX = "/__test_subarray"


# pylint: disable=W0212
@pytest.fixture(scope="session")
def cfg():
    host = os.getenv('SDP_TEST_HOST', '127.0.0.1')
    with ska_sdp_config.Config(global_prefix=PREFIX, host=host) as cfg:
        cfg._backend.delete(PREFIX, must_exist=False, recursive=True)
        yield cfg
        cfg._backend.delete(PREFIX, must_exist=False, recursive=True)


def test_subarray_list(cfg):
    subarray1_id = '01'
    subarray2_id = '02'

    # Check subarray list is empty
    for txn in cfg.txn():
        subarray_ids = txn.list_subarrays()
        assert subarray_ids == []

    # Create first subarray
    for txn in cfg.txn():
        txn.create_subarray(subarray1_id, {})

    # Check subarray list has entry
    for txn in cfg.txn():
        subarray_ids = txn.list_subarrays()
        assert subarray_ids == [subarray1_id]

    # Create second subarray
    for txn in cfg.txn():
        txn.create_subarray(subarray2_id, {})

    # Check subarray list has both entries
    for txn in cfg.txn():
        subarray_ids = txn.list_subarrays()
        assert subarray_ids == sorted([subarray1_id, subarray2_id])


def test_subarray_create_update(cfg):

    subarray_id = '03'
    state1 = {
        'sbi_id': 'sbi-test-20200727-00000',
        'state': 'ON',
        'obs_state': 'READY',
        'scan_type': 'science',
        'scan_id': None
    }
    state2 = {
        'sbi_id': 'sbi-test-20200727-00000',
        'state': 'ON',
        'obs_state': 'SCANNING',
        'scan_type': 'science',
        'scan_id': 1
    }

    # Subarray has not been created, so should return None
    for txn in cfg.txn():
        state = txn.get_subarray(subarray_id)
        assert state is None

    # Create subarray as state1
    for txn in cfg.txn():
        txn.create_subarray(subarray_id, state1)

    # Read subarray and check it is equal to state1
    for txn in cfg.txn():
        state = txn.get_subarray(subarray_id)
        assert state == state1

    # Trying to recreate should raise a collision exception
    for txn in cfg.txn():
        with pytest.raises(ska_sdp_config.ConfigCollision):
            txn.create_subarray(subarray_id, state1)

    # Update subarray to state2
    for txn in cfg.txn():
        txn.update_subarray(subarray_id, state2)

    # Read subarray and check it is equal to state2
    for txn in cfg.txn():
        state = txn.get_subarray(subarray_id)
        assert state == state2


if __name__ == '__main__':
    pytest.main()
