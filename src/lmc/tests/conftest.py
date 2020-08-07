"""Pytest fixtures."""

# pylint: disable=redefined-outer-name

import threading
import ska_sdp_config

import pytest
from tango.test_context import MultiDeviceTestContext

from ska_sdp_lmc import SDPMaster, SDPSubarray

# Turn off the SDP config DB in the subarray by default. This will be
# overridden if the TOGGLE_CONFIG_DB environment variable is set to 1.

SDPSubarray.set_feature_default('config_db', False)

# List of devices for the test session

device_info = [
    {
        'class': SDPMaster,
        'devices': [
            {'name': 'test_sdp/elt/master'}
        ]
    },
    {
        'class': SDPSubarray,
        'devices': [
            {'name': 'test_sdp/elt/subarray_1'}
        ]
    }
]


@pytest.fixture(scope='session')
def devices():
    """Start the devices in a MultiDeviceTestContext."""
    context = MultiDeviceTestContext(device_info)
    context.start()
    yield context
    context.stop()


RECEIVE_WORKFLOWS = ['test_receive_addresses']
RECEIVE_ADDRESSES = {
    'science_A': {
        'host': [[0, '192.168.0.1'], [2000, '192.168.0.1']],
        'port': [[0, 9000, 1], [2000, 9000, 1]]
    },
    'calibration_B': {
        'host': [[0, '192.168.0.1'], [2000, '192.168.0.1']],
        'port': [[0, 9000, 1], [2000, 9000, 1]]
    }
}


def mock_pc_and_rw_loop(end, timeout=5):
    """Execute main loop for mocking PC and and receive workflow.

    :param end: event used to signal loop to exit
    :param timeout: timeout on loop

    """
    # pylint: disable=invalid-name
    config = ska_sdp_config.Config()
    for txn in config.txn():
        if end.is_set():
            break
        pb_list = txn.list_processing_blocks()
        for pb_id in pb_list:
            pb_state = txn.get_processing_block_state(pb_id)
            if pb_state is None:
                pb_state = {'status': 'RUNNING'}
                pb = txn.get_processing_block(pb_id)
                if pb.workflow['id'] in RECEIVE_WORKFLOWS:
                    sb = txn.get_scheduling_block(pb.sbi_id)
                    sb['pb_receive_addresses'] = pb_id
                    txn.update_scheduling_block(pb.sbi_id, sb)
                    # This uses the hard-coded values, it should really set
                    # them based on the scan types in the SBI, like this:
                    # pb_state['receive_addresses'] = parse(sb['scan_types'])
                    pb_state['receive_addresses'] = RECEIVE_ADDRESSES
                txn.create_processing_block_state(pb_id, pb_state)
        txn.loop(wait=True, timeout=timeout)


# @pytest.fixture(scope='session')
def mock_pc_and_rw():
    """Fixture to mock processing controller and receive workflow.

    This starts the main loop in a thread.

    """
    end = threading.Event()
    thread = threading.Thread(target=mock_pc_and_rw_loop, args=(end,))
    thread.start()
    yield
    end.set()
    thread.join()
