# coding: utf-8
"""SDP Subarray device tests."""
# pylint: disable=invalid-name
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=fixme


import os
import json
import tango

from ska_telmodel.sdp.schema import validate_sdp_receive_addresses

import pytest
from pytest_bdd import (given, parsers, scenarios, then, when)

import ska_sdp_config
from ska_sdp_lmc import (AdminMode, HealthState, ObsState, subarray_config)

CONFIG_DB_CLIENT = subarray_config.new_config_db()
SUBARRAY_ID = '01'
RECEIVE_WORKFLOWS = ['test_receive_addresses']


# -----------------------------------------------------------------------------
# Scenarios : Specify what we want the software to do
# -----------------------------------------------------------------------------

# Load scenarios from the specified feature file.
scenarios('features/subarray.feature')


# -----------------------------------------------------------------------------
# Given steps: set the initial context of the system
# -----------------------------------------------------------------------------

@given('I have an SDPSubarray device', target_fixture='subarray_device')
def subarray_device(devices):
    """Get the SDPSubarray device proxy.

    :param devices: the devices in a MultiDeviceTestContext

    """
    device = devices.get_device('test_sdp/elt/subarray_1')

    # Wipe the config DB
    wipe_config_db()

    # Initialise the device
    device.Init()

    # Update the device attributes
    device.update_attributes()

    return device


# -----------------------------------------------------------------------------
# When steps: describe an event or action
# -----------------------------------------------------------------------------

@when('the device is initialised')
def init_device():
    """Initialise the subarray device.

    This function does nothing because the 'given' function initialises the
    device, but a dummy 'when' clause is needed for some of the tests.

    """


@when(parsers.parse('the state is {state:S}'))
def set_subarray_device_state(subarray_device, state: str):
    """Set the device state to the specified value.

    This function sets the obsState to EMPTY.

    :param subarray_device: an SDPSubarray device.
    :param state: an SDPSubarray state string.

    """
    # Set the device state in the config DB
    set_state_and_obs_state(state, 'EMPTY')

    # Update device attributes
    subarray_device.update_attributes()

    # Check that state has been set correctly
    assert subarray_device.state() == tango.DevState.names[state]


@when(parsers.parse('obsState is {initial_obs_state:S}'))
@when('obsState is <initial_obs_state>')
def set_subarray_device_obstate(subarray_device, initial_obs_state: str):
    """Set the obsState to the specified value.

    This function sets the device state to ON.

    :param subarray_device: an SDPSubarray device
    :param initial_obs_state: an SDPSubarray ObsState enum string

    """
    # Set the obsState in the config DB
    set_state_and_obs_state('ON', initial_obs_state)

    # Update the device attributes
    subarray_device.update_attributes()

    # Check obsState has been set correctly
    assert subarray_device.ObsState == ObsState[initial_obs_state]


@when(parsers.parse('I call {command:S}'))
@when('I call <command>')
def call_command(subarray_device, command):
    """Call an SDPSubarray command.

     :param subarray_device: an SDPSubarray device
     :param command: the name of the command

     """
    # Get information about the command and the command itself
    command_list = subarray_device.get_command_list()
    assert command in command_list
    command_config = subarray_device.get_command_config(command)
    command_func = getattr(subarray_device, command)

    # Call the command
    if command_config.in_type == tango.DevVoid:
        command_func()
    elif command_config.in_type == tango.DevString:

        config_str = read_command_argument(command)
        command_func(config_str)
    else:
        msg = 'Test cannot handle argument of type {}'
        raise ValueError(msg.format(command_config.in_type))

    if command == 'AssignResources':
        # Create the PB states, including the receive addresses for the receive
        # workflow, which would be done by the PC and workflows
        create_pb_states()

    # Update the device attributes
    subarray_device.update_attributes()


# -----------------------------------------------------------------------------
# Then steps: check the outcome is as expected
# -----------------------------------------------------------------------------

@then(parsers.parse('the state should be {expected:S}'))
def device_state_equals(subarray_device, expected):
    """Check the Subarray device device state.

    :param subarray_device: an SDPSubarray device.
    :param expected: the expected device state.
    """
    assert subarray_device.state() == tango.DevState.names[expected]


@then(parsers.parse('obsState should be {final_obs_state:S}'))
@then('obsState should be <final_obs_state>')
def obs_state_equals(subarray_device, final_obs_state):
    """Check the Subarray obsState attribute value.

    :param subarray_device: an SDPSubarray device.
    :param final_obs_state: the expected obsState.
    """
    assert subarray_device.obsState == ObsState[final_obs_state]


@then(parsers.parse('adminMode should be {expected:S}'))
def admin_mode_equals(subarray_device, expected):
    """Check the Subarray adminMode value.

    :param subarray_device: An SDPSubarray device.
    :param expected: The expected adminMode.
    """
    assert subarray_device.adminMode == AdminMode[expected]


@then(parsers.parse('healthState should be {expected:S}'))
def health_state_equals(subarray_device, expected):
    """Check the Subarray healthState value.

    :param subarray_device: An SDPSubarray device.
    :param expected: The expected heathState.
    """
    assert subarray_device.healthState == HealthState[expected]
    if expected == 'OK':
        assert subarray_device.healthState == 0


@then('the input type of <command> should be <input_type>')
def command_input_type_equals(subarray_device, command, input_type):
    """Check input type of a command.

    :param subarray_device: an SDPSubarray device
    :param command: the command name
    :param input_type: the expected input type

    """
    assert command in subarray_device.get_command_list()
    command_config = subarray_device.get_command_config(command)
    assert command_config.in_type == getattr(tango, input_type)


@then('the output type of <command> should be <output_type>')
def command_output_type_equals(subarray_device, command, output_type):
    """Check output type of a command.

    :param subarray_device: an SDPSubarray device.
    :param command: the command name
    :param output_type: the expected output type

    """
    assert command in subarray_device.get_command_list()
    command_config = subarray_device.get_command_config(command)
    assert command_config.out_type == getattr(tango, output_type)


@then(parsers.parse('calling {command:S} should raise tango.DevFailed'))
@then('calling <command> should raise tango.DevFailed')
def command_raises_dev_failed(subarray_device, command):
    """Check that calling command raises tango.DevFailed.

    :param subarray_device: An SDPSubarray device.
    :param command: the name of the command.

    """
    # Get information about the command and the command itself
    command_list = subarray_device.get_command_list()
    assert command in command_list
    command_config = subarray_device.get_command_config(command)
    command_func = getattr(subarray_device, command)

    # Call the command
    with pytest.raises(tango.DevFailed):
        if command_config.in_type == tango.DevVoid:
            command_func()
        elif command_config.in_type == tango.DevString:
            config_str = read_command_argument(command)
            command_func(config_str)
        else:
            msg = 'Test cannot handle command input of type {}'
            raise ValueError(msg.format(command_config.in_type))


@then(parsers.parse('calling {command:S} with an invalid JSON configuration '
                    'should raise tango.DevFailed'))
@then('calling <command> with an invalid JSON configuration should raise '
      'tango.DevFailed')
def command_with_invalid_json_raises_dev_failed(subarray_device, command):
    """Check that calling command with invalid JSON raises tango.DevFailed.

    :param subarray_device: an SDPSubarray device
    :param command: the name of the command

    """
    # Get information about the command and the command itself
    command_list = subarray_device.get_command_list()
    assert command in command_list
    command_func = getattr(subarray_device, command)

    # Read an invalid command argument
    config_str = read_command_argument(command, invalid=True)

    # Call the command
    with pytest.raises(tango.DevFailed):
        command_func(config_str)


@then('the processing blocks should be in the config DB')
def processing_blocks_in_config_db():
    """Check that the config DB has the configured PBs.

    :param subarray_device: An SDPSubarray device.

    """
    # Get the expected processing blocks from the AssignResources argument
    _, pbs = get_sbi_pbs()
    # Check they are present in the config DB
    for txn in CONFIG_DB_CLIENT.txn():
        pb_ids = txn.list_processing_blocks()
        for pb_expected in pbs:
            assert pb_expected.id in pb_ids
            pb = txn.get_processing_block(pb_expected.id)
            assert pb == pb_expected


@then('receiveAddresses should have the expected value')
def receive_addresses_expected(subarray_device):
    """Check that the receiveAddresses value is as expected.

    :param subarray_device: An SDPSubarray device.

    """
    # Get the expected receive addresses from the data file
    receive_addresses_expected = read_receive_addresses()
    receive_addresses = json.loads(subarray_device.receiveAddresses)
    assert receive_addresses == receive_addresses_expected
    validate_sdp_receive_addresses(3, receive_addresses, 2)


@then('receiveAddresses should be an empty JSON object')
def receive_addresses_empty(subarray_device):
    """Check that the receiveAddresses value is an empty JSON object.

    :param subarray_device: An SDPSubarray device.

    """
    receive_addresses = json.loads(subarray_device.receiveAddresses)
    assert receive_addresses is None


# -----------------------------------------------------------------------------
# Ancillary functions
# -----------------------------------------------------------------------------

def wipe_config_db():
    """Remove all entries in the config DB."""
    CONFIG_DB_CLIENT.backend.delete('/pb', must_exist=False, recursive=True)
    CONFIG_DB_CLIENT.backend.delete('/sb', must_exist=False, recursive=True)
    CONFIG_DB_CLIENT.backend.delete('/subarray', must_exist=False,
                                    recursive=True)


def set_state_and_obs_state(state, obs_state):
    """Set state and obsState in the config DB.

    This updates the subarray entry and creates the SBI and PBs if they are
    present in the desired obsState.

    """
    # Check state and obsState are valid values
    assert state in tango.DevState.names
    assert obs_state in ObsState.__members__

    if obs_state != 'EMPTY':
        sbi, pbs = get_sbi_pbs()
        sbi_id = sbi.get('id')
    else:
        sbi_id = None
        sbi = {}
        pbs = []

    if obs_state in ['READY', 'SCANNING']:
        scan_type = get_scan_type()
    else:
        scan_type = None

    if obs_state == 'SCANNING':
        scan_id = get_scan_id()
    else:
        scan_id = None

    subarray = {
        'state': state,
        'obs_state_target': obs_state,
        'sbi_id': sbi_id,
        'last_command': None
    }
    sbi['scan_type'] = scan_type
    sbi['scan_id'] = scan_id

    for txn in CONFIG_DB_CLIENT.txn():
        txn.update_subarray(SUBARRAY_ID, subarray)
        if sbi_id is not None:
            txn.create_scheduling_block(sbi_id, sbi)
        for pb in pbs:
            txn.create_processing_block(pb)

    create_pb_states()


def create_pb_states():
    """Create PB states in the config DB.

    This creates the PB states with status = RUNNING, and for any workflow
    matching the list of receive workflows, it adds the receive addresses.

    """
    receive_addresses = read_receive_addresses()

    for txn in CONFIG_DB_CLIENT.txn():
        pb_list = txn.list_processing_blocks()
        for pb_id in pb_list:
            pb_state = txn.get_processing_block_state(pb_id)
            if pb_state is None:
                pb_state = {'status': 'RUNNING'}
                pb = txn.get_processing_block(pb_id)
                if pb.workflow['id'] in RECEIVE_WORKFLOWS:
                    sbi = txn.get_scheduling_block(pb.sbi_id)
                    sbi['pb_receive_addresses'] = pb_id
                    txn.update_scheduling_block(pb.sbi_id, sbi)
                    pb_state['receive_addresses'] = receive_addresses
                txn.create_processing_block_state(pb_id, pb_state)


def get_sbi_pbs():
    """Get SBI and PBs from AssignResources argument."""
    config = read_command_argument('AssignResources', decode=True)

    sbi_id = config.get('id')
    sbi = {
        'id': sbi_id,
        'subarray_id': SUBARRAY_ID,
        'scan_types': config.get('scan_types'),
        'pb_realtime': [],
        'pb_batch': [],
        'pb_receive_addresses': None,
        'current_scan_type': None,
        'scan_id': None,
        'status': 'ACTIVE'
    }

    pbs = []
    for pbc in config.get('processing_blocks'):
        pb_id = pbc.get('id')
        wf_type = pbc.get('workflow').get('type')
        sbi['pb_' + wf_type].append(pb_id)
        if 'dependencies' in pbc:
            dependencies = pbc.get('dependencies')
        else:
            dependencies = []
        pb = ska_sdp_config.ProcessingBlock(
            pb_id, sbi_id, pbc.get('workflow'),
            parameters=pbc.get('parameters'),
            dependencies=dependencies
        )
        pbs.append(pb)

    return sbi, pbs


def get_scan_type():
    """Get scan type from Configure argument."""
    config = read_command_argument('Configure', decode=True)
    scan_type = config.get('scan_type')
    return scan_type


def get_scan_id():
    """Get scan ID from Scan argument."""
    config = read_command_argument('Scan', decode=True)
    scan_id = config.get('id')
    return scan_id


def read_command_argument(name, invalid=False, decode=False):
    """Read command argument from JSON file.

    :param name: name of command
    :param invalid: read the invalid version of the argument
    :param decode: decode the JSON data into Python

    """
    if invalid:
        fmt = 'command_{}_invalid.json'
    else:
        fmt = 'command_{}.json'
    return read_json_data(fmt.format(name), decode=decode)


def read_receive_addresses():
    """Read receive addresses from JSON file."""
    return read_json_data('receive_addresses.json', decode=True)


def read_json_data(filename, decode=False):
    """Read JSON file from data directory.

    :param decode: decode the JSON dat into Python

    """
    path = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(path, 'r') as file:
        data = file.read()
    if decode:
        data = json.loads(data)
    return data
