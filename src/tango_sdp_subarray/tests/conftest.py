# coding: utf-8
"""Pytest plugins."""

import logging
import threading
from unittest.mock import Mock

import pytest
from tango.test_context import DeviceTestContext

import ska_sdp_config
from SDPSubarray import SDPSubarray, workflows, release, feature_toggle


logging.basicConfig(level=logging.DEBUG)

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


workflows.Workflows.get_receive_addresses = Mock(return_value=RECEIVE_ADDRESSES)


@pytest.fixture(scope='session', autouse=True)
def tango_context():
    """Fixture that creates SDPSubarray DeviceTestContext object."""
    # pylint: disable=redefined-outer-name

    # Set default feature toggle values for the test.
    # Note: these are ignored if the env variables are already set. ie:
    #       TOGGLE_CONFIG_DB
    # Note: if these, or the env variables are not set, use the
    #       SDPSubarray device defaults.
    feature_toggle.set_feature_toggle_default('config_db', False)

    device_name = 'mid_sdp/elt/subarray_1'
    properties = dict(Version=release.VERSION)
    tango_context = DeviceTestContext(SDPSubarray,
                                      device_name=device_name,
                                      properties=properties)
    print()
    print('Starting context...')
    tango_context.start()
    yield tango_context
    print('Stopping context...')
    # Looks like tango bug on Windows.
    try:
        tango_context.stop()
    except PermissionError as tango_error:
        print(str(tango_error))


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


@pytest.fixture(scope='session')
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
