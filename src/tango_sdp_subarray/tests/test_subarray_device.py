# coding: utf-8
"""SDP Subarray device tests."""
# pylint: disable=invalid-name
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=fixme

import json
import threading
import time
import ast
from os.path import dirname, join

import tango
from tango import DevState
from multiprocessing import Process

import pytest
from pytest_bdd import (given, parsers, scenarios, then, when)

from ska_telmodel.sdp.schema import validate_sdp_receive_addresses

from SDPSubarray import (AdminMode, HealthState, ObsState, SDPSubarray)

try:
    import ska_sdp_config
except ImportError:
    ska_sdp_config = None

# -----------------------------------------------------------------------------
# Scenarios : Specify what we want the software to do
# -----------------------------------------------------------------------------

# Load all scenarios from the specified feature file.
scenarios('./1_VTS-223.feature')


# -----------------------------------------------------------------------------
# Given Steps : Used to describe the initial context of the system.
# -----------------------------------------------------------------------------


@given(parsers.parse('I have an {admin_mode_value} SDPSubarray device'))
def subarray_device(tango_context, admin_mode_value: str):
    """Get a SDPSubarray device object

    :param tango_context: fixture providing a TangoTestContext
    :param admin_mode_value: adminMode value the device is created with
    """

    # Clear the Database
    if ska_sdp_config is not None \
            and SDPSubarray.is_feature_active('config_db'):
        config_db_client = ska_sdp_config.Config()
        config_db_client._backend.delete("/pb", must_exist=False, recursive=True)
        config_db_client._backend.delete("/sb", must_exist=False, recursive=True)

    # Initialise SDPSubarray device
    tango_context.device.Init()
    tango_context.device.adminMode = AdminMode[admin_mode_value]
    return tango_context.device


# -----------------------------------------------------------------------------
# When Steps : Describe an event or action
# -----------------------------------------------------------------------------

@when('the device is initialised')
def init_device(subarray_device):
    """Initialise the subarray device.

    :param subarray_device: An SDPSubarray device.
    """
    subarray_device.Init()


@when(parsers.parse(
    'the device is {state_value} and obsState is {obs_state_value}'
))
@when('the device is <state_value> and obsState is <obs_state_value>')
def set_subarray_device_state_obstate(subarray_device, state_value: str,
                                      obs_state_value):
    """Set the device state and obsState attribute to the specified value.

    :param subarray_device: fixture providing a TangoTestContext
    :param state_value: An SDPSubarray state string.
    :param obs_state_value: An SDPSubarray ObsState enum string.
    """

    subarray_device.Init()
    if state_value == 'OFF' and obs_state_value == 'IDLE':
        pass
    elif state_value == 'ON' and obs_state_value == 'IDLE':
        command_assign_resources(subarray_device)
    elif state_value == 'ON' and obs_state_value == 'READY':
        command_assign_resources(subarray_device)
        command_configure(subarray_device)
    elif state_value == 'ON' and obs_state_value == 'SCANNING':
        command_assign_resources(subarray_device)
        command_configure(subarray_device)
        command_scan(subarray_device)
    else:
        raise ValueError(
            'Combination of device state {} and obsState {} not settable'
            ''.format(state_value, obs_state_value)
        )

    # Check state and obs_state values.
    assert subarray_device.state() == DevState.names[state_value]
    assert subarray_device.ObsState == ObsState[obs_state_value]


def mock_receive_addresses():
    state = {
        'status': 'STARTING',
        'resources_available': True
    }
    # Get connection to config DB
    config = ska_sdp_config.Config()
    for txn in config.txn():
        pb_ids = txn.list_processing_blocks()
        print(pb_ids)
        if not pb_ids:
            print("LOOPINGGGGGGG")
            txn.loop(wait=True)

    for txn in config.txn():
        for pb_id in pb_ids:
          pb = txn.get_processing_block(pb_id)
          if pb.workflow['id'] == 'test_receive_addresses':
              print('IN HERE')
              print(pb_id)
              # Set status to STARTING, and resources_available to True
              # Create the processing block state.
              txn.create_processing_block_state(pb_id, state)

              config = ska_sdp_config.Config()

              sb_id = pb.sbi_id
              print('SB id: %s', sb_id)

              # Set status to WAITING
              print('Setting status to WAITING')
              state = txn.get_processing_block_state(pb_id)
              print(state)
              state['status'] = 'WAITING'
              txn.update_processing_block_state(pb_id, state)

              # Set status to RUNNING
              print('Setting status to RUNNING')

              state = txn.get_processing_block_state(pb_id)
              state['status'] = 'RUNNING'
              txn.update_processing_block_state(pb_id, state)

              # Generated receive addresses
              receive_addresses = ast.literal_eval("{'science_A': {'host': [[0, '192.168.0.1'], " \
                                "[2000, '192.168.0.1']], 'port': [[0, 9000, 1], [2000, 9000, 1]]}, " \
                                "'calibration_B': {'host': [[0, '192.168.0.1'], [2000, '192.168.0.1']], " \
                                "'port': [[0, 9000, 1], [2000, 9000, 1]]}}")

              # Update receive addresses in processing block state
              print("Updating receive addresses in processing block state")
              state = txn.get_processing_block_state(pb_id)
              state['receive_addresses'] = receive_addresses
              txn.update_processing_block_state(pb_id, state)

              # Adding pb_id in pb_receive_address in SB
              print("Adding PB ID to pb_receive_addresses in SB")
              sb = txn.get_scheduling_block(sb_id)
              sb['pb_receive_addresses'] = pb_id
              txn.update_scheduling_block(sb_id, sb)

@when('I call AssignResources')
def command_assign_resources(subarray_device):
    """Call the AssignResources command.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'AssignResources' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('AssignResources')
    assert command_info.in_type == tango.DevString
    assert command_info.out_type == tango.DevVoid

    config_file = 'command_AssignResources.json'
    path = join(dirname(__file__), 'data', config_file)
    with open(path, 'r') as file:
        config_str = file.read()


    # Multiprocessing Attempt
    # p1 = Process(target=subarray_device.AssignResources(config_str))
    # # p2 = Process(target=mock_receive_addresses())
    # p1.start()
    # # p2.start()
    # # p2.start()

    # mock_receive_addresses()
    thread1 = threading.Thread(target=subarray_device.AssignResources(config_str))
    thread1.daemon = True
    thread1.start()
    thread = threading.Thread(target=mock_receive_addresses())
    thread.daemon = True
    thread.start()


    # print(threading.active_count())


@when('I call AssignResources with invalid JSON')
def command_assign_resources_invalid_json(subarray_device):
    """Call the AssignResources command with invalid JSON.

    :param subarray_device: An SDPSubarray device.
    """
    config_file = 'invalid_AssignResources.json'
    path = join(dirname(__file__), 'data', config_file)
    with open(path, 'r') as file:
        config_str = file.read()

    with pytest.raises(tango.DevFailed):
        subarray_device.AssignResources(config_str)


@when('I call ReleaseResources')
def command_release_resources(subarray_device):
    """Call the ReleaseResources command.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'ReleaseResources' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('ReleaseResources')
    assert command_info.in_type == tango.DevVoid
    assert command_info.out_type == tango.DevVoid

    subarray_device.ReleaseResources()


@when('I call Configure')
def command_configure(subarray_device):
    """Call the Configure command.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'Configure' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('Configure')
    assert command_info.in_type == tango.DevString
    assert command_info.out_type == tango.DevVoid

    config_file = 'command_Configure.json'
    path = join(dirname(__file__), 'data', config_file)
    with open(path, 'r') as file:
        config_str = file.read()

    subarray_device.Configure(config_str)


@when('I call Configure with invalid JSON')
def command_configure_invalid_json(subarray_device):
    """Call the Configure command with invalid JSON.

    :param subarray_device: An SDPSubarray device.
    """
    config_file = 'invalid_Configure.json'
    path = join(dirname(__file__), 'data', config_file)
    with open(path, 'r') as file:
        config_str = file.read()

    with pytest.raises(tango.DevFailed):
        subarray_device.Configure(config_str)


@when('I call Reset')
def command_reset(subarray_device):
    """Call the Reset command.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'Reset' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('Reset')
    assert command_info.in_type == tango.DevVoid
    assert command_info.out_type == tango.DevVoid

    subarray_device.Reset()


@when('I call Scan')
def command_scan(subarray_device):
    """Call the Scan command.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'Scan' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('Scan')
    assert command_info.in_type == tango.DevString
    assert command_info.out_type == tango.DevVoid

    config_file = 'command_Scan.json'
    path = join(dirname(__file__), 'data', config_file)
    with open(path, 'r') as file:
        config_str = file.read()

    subarray_device.Scan(config_str)


@when('I call Scan with invalid JSON')
def command_scan_invalid_json(subarray_device):
    """Call the Scan command with invalid JSON.

    :param subarray_device: An SDPSubarray device.
    """

    with pytest.raises(tango.DevFailed):
        subarray_device.Scan('{}')


@when('I call EndScan')
def command_end_scan(subarray_device):
    """Call the EndScan command.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'EndScan' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('EndScan')
    assert command_info.in_type == tango.DevVoid
    assert command_info.out_type == tango.DevVoid

    subarray_device.EndScan()


# -----------------------------------------------------------------------------
# Then Steps : Describe an expected outcome or result
# -----------------------------------------------------------------------------


@then(parsers.parse('the device should be {expected}'))
def device_state_equals(subarray_device, expected):
    """Check the Subarray device device state.

    :param subarray_device: An SDPSubarray device.
    :param expected: The expected device state.
    """
    assert subarray_device.state() == DevState.names[expected]


@then(parsers.parse('obsState should be {expected}'))
def obs_state_equals(subarray_device, expected):
    """Check the Subarray obsState attribute value.

    :param subarray_device: An SDPSubarray device.
    :param expected: The expected obsState.
    """
    assert subarray_device.obsState == ObsState[expected]


@then(parsers.parse('adminMode should be {expected}'))
def admin_mode_equals(subarray_device, expected):
    """Check the Subarray adminMode value.

    :param subarray_device: An SDPSubarray device.
    :param expected: The expected adminMode.
    """
    assert subarray_device.adminMode == AdminMode[expected], \
        "actual != expected"


@then(parsers.parse('healthState should be {expected}'))
def health_state_equals(subarray_device, expected):
    """Check the Subarray healthState value.

    :param subarray_device: An SDPSubarray device.
    :param expected: The expected heathState.
    """
    assert subarray_device.healthState == HealthState[expected]
    if expected == 'OK':
        assert subarray_device.healthState == 0


@then('calling AssignResources raises tango.DevFailed')
def dev_failed_error_raised_by_assign_resources(subarray_device):
    """Check that calling AssignResources raises a tango.DevFailed error.

    :param subarray_device: An SDPSubarray device.
    """

    with pytest.raises(tango.DevFailed):
        subarray_device.AssignResources('{}')


@then('calling ReleaseResources raises tango.DevFailed')
def dev_failed_error_raised_by_release_resources(subarray_device):
    """Check that calling ReleaseResources raises a tango.DevFailed error.

    :param subarray_device: An SDPSubarray device.
    """

    with pytest.raises(tango.DevFailed):
        subarray_device.ReleaseResources()


@then('calling Configure raises tango.DevFailed')
def dev_failed_error_raised_by_configure(subarray_device):
    """Check that calling Configure raises a tango.DevFailed error.

    :param subarray_device: An SDPSubarray device.
    """

    with pytest.raises(tango.DevFailed):
        subarray_device.Configure('{}')


@then('calling Reset raises tango.DevFailed')
def dev_failed_error_raised_by_reset(subarray_device):
    """Check that calling Reset raises a tango.DevFailed error.

    :param subarray_device: An SDPSubarray device.
    """
    with pytest.raises(tango.DevFailed):
        subarray_device.Reset()


@then('calling Scan raises tango.DevFailed')
def dev_failed_error_raised_by_scan(subarray_device):
    """Check that calling Scan raises a tango.DevFailed error.

    :param subarray_device: An SDPSubarray device.
    """
    with pytest.raises(tango.DevFailed):
        subarray_device.Scan('{}')


@then('calling EndScan raises tango.DevFailed')
def dev_failed_error_raised_by_end_scan(subarray_device):
    """Check that calling EndScan raises a tango.DevFailed error.

    :param subarray_device: An SDPSubarray device.
    """
    with pytest.raises(tango.DevFailed):
        subarray_device.EndScan()


@then('the configured Processing Blocks should be in the Config DB')
def check_config_db():
    """Check that the config DB has the configured PBs.

    Only run this step if the config DB is enabled.
    """
    if ska_sdp_config is not None \
            and SDPSubarray.is_feature_active('config_db'):
        filename = join(dirname(__file__), 'data',
                        'command_AssignResources.json')
        with open(filename, 'r') as file:
            config = json.load(file)
        config_db_client = ska_sdp_config.Config()
        for txn in config_db_client.txn():
            pb_ids = txn.list_processing_blocks()
        for pb in config['processing_blocks']:
            assert pb['id'] in pb_ids


# TODO: Need to update this - Nijin
@then('the receiveAddresses attribute should return the expected value')
def receive_addresses_attribute_ok(subarray_device):
    """Check that the receiveAddresses attribute works as expected.

    :param subarray_device: An SDPSubarray device.
    """
    receive_addresses = subarray_device.receiveAddresses
    # print(json.dumps(json.loads(receive_addresses), indent=2))
    data_path = join(dirname(__file__), 'data')

    if ska_sdp_config is not None \
            and SDPSubarray.is_feature_active('config_db'):
        expected_output_file = join(
            data_path,
            'receive_addresses_output.json'
            )
    # if ska_sdp_config is not None \
    #         and SDPSubarray.is_feature_active('config_db'):
    #     expected_output_file = join(
    #         data_path,
    #         'attr_receiveAddresses-cbfOutputLink-disabled.json'
    #         )

        # Instead of opening file use telescope-model package
        with open(expected_output_file, 'r') as file:
            expected = json.loads(file.read())
        receive_addresses = json.loads(receive_addresses)
        assert receive_addresses == expected

        validate_sdp_receive_addresses(3, json.loads(receive_addresses), 2)




@then('the receiveAddresses attribute should return an empty JSON object')
def receive_addresses_empty(subarray_device):
    """Check that receiveAddresses attribute returns an empty JSON object.

    :param subarray_device: An SDPSubarray device.
    """
    receive_addresses = subarray_device.receiveAddresses
    assert receive_addresses == 'null'
