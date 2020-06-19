# coding: utf-8
"""Pytest plugins."""

# from unittest.mock import MagicMock

import pytest
from tango.test_context import DeviceTestContext
import threading

import ska_sdp_config
from SDPSubarray import SDPSubarray
from SDPSubarray.release import VERSION


@pytest.fixture(scope='session', autouse=True)
def tango_context():
    """Fixture that creates SDPSubarray DeviceTestContext object."""
    # pylint: disable=redefined-outer-name

    # Set default feature toggle values for the test.
    # Note: these are ignored if the env variables are already set. ie:
    #       TOGGLE_CONFIG_DB
    # Note: if these, or the env variables are not set, use the
    #       SDPSubarray device defaults.
    SDPSubarray.set_feature_toggle_default('config_db', True)

    device_name = 'mid_sdp/elt/subarray_1'
    properties = dict(Version=VERSION)
    tango_context = DeviceTestContext(SDPSubarray,
                                      device_name=device_name,
                                      properties=properties)
    print()
    print('Starting context...')
    tango_context.start()
    # SDPSubarray.get_name = MagicMock(
    #     side_effect=tango_context.get_device_access)
    yield tango_context
    print('Stopping context...')
    tango_context.stop()


# def mock_processing_controller():
#     state = {
#             'status': 'STARTING',
#             'resources_available': True
#         }
#
#     # Get connection to config DB
#     config = ska_sdp_config.Config()
#     for txn in config.txn():
#         pb_ids = txn.list_processing_blocks()
#         print(pb_ids)
#         if not pb_ids:
#             print("LOOPINGGGGGGG")
#             txn.loop(wait=True)
#             # return None
#
#     for txn in config.txn():
#         for pb_id in pb_ids:
#           pb = txn.get_processing_block(pb_id)
#           if pb.workflow['id'] == 'test_receive_addresses':
#               print('IN HERE')
#               print(pb_id)
#               # Set status to STARTING, and resources_available to True
#               # Create the processing block state.
#               txn.create_processing_block_state(pb_id, state)


#
# @pytest.fixture(autouse=True)
# def mock_receive_addresses():
#     # pb_id = mock_processing_controller()
#     # if pb_id is None:
#     #     return None
#
#     state = {
#         'status': 'STARTING',
#         'resources_available': True
#     }
#     # Get connection to config DB
#     config = ska_sdp_config.Config()
#     for txn in config.txn():
#         pb_ids = txn.list_processing_blocks()
#         print(pb_ids)
#         if not pb_ids:
#             print("LOOPINGGGGGGG")
#             txn.loop(wait=True)
#
#     for txn in config.txn():
#         for pb_id in pb_ids:
#           pb = txn.get_processing_block(pb_id)
#           if pb.workflow['id'] == 'test_receive_addresses':
#               print('IN HERE')
#               print(pb_id)
#               # Set status to STARTING, and resources_available to True
#               # Create the processing block state.
#               txn.create_processing_block_state(pb_id, state)
#
#               config = ska_sdp_config.Config()
#
#               sb_id = pb.sbi_id
#               print('SB id: %s', sb_id)
#
#               # Set status to WAITING
#               print('Setting status to WAITING')
#               state = txn.get_processing_block_state(pb_id)
#               print(state)
#               state['status'] = 'WAITING'
#               txn.update_processing_block_state(pb_id, state)
#
#               # Set status to RUNNING
#               print('Setting status to RUNNING')
#
#               state = txn.get_processing_block_state(pb_id)
#               state['status'] = 'RUNNING'
#               txn.update_processing_block_state(pb_id, state)
#
#               # Generated receive addresses
#               receive_addresses = ast.literal_eval("{'science_A': {'host': [[0, '192.168.0.1'], " \
#                                 "[2000, '192.168.0.1']], 'port': [[0, 9000, 1], [2000, 9000, 1]]}, " \
#                                 "'calibration_B': {'host': [[0, '192.168.0.1'], [2000, '192.168.0.1']], " \
#                                 "'port': [[0, 9000, 1], [2000, 9000, 1]]}}")
#
#               # Update receive addresses in processing block state
#               print("Updating receive addresses in processing block state")
#               state = txn.get_processing_block_state(pb_id)
#               state['receive_addresses'] = receive_addresses
#               txn.update_processing_block_state(pb_id, state)
#
#               # Adding pb_id in pb_receive_address in SB
#               print("Adding PB ID to pb_receive_addresses in SB")
#               sb = txn.get_scheduling_block(sb_id)
#               sb['pb_receive_addresses'] = pb_id
#               txn.update_scheduling_block(sb_id, sb)
#
