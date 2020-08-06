# coding: utf-8
"""SDP Subarray device tests."""
# pylint: disable=invalid-name
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=fixme

import json
from os.path import dirname, join

import tango

from ska_telmodel.sdp.schema import validate_sdp_receive_addresses

import pytest
from pytest_bdd import (given, parsers, scenarios, then, when)

from ska_sdp_lmc import (AdminMode, HealthState, ObsState, SDPSubarray)

try:
    import ska_sdp_config
except ImportError:
    ska_sdp_config = None


# -----------------------------------------------------------------------------
# Scenarios : Specify what we want the software to do
# -----------------------------------------------------------------------------

# Load scenarios from the specified feature file.
scenarios('features/subarray.feature')


# -----------------------------------------------------------------------------
# Given Steps : Used to describe the initial context of the system.
# -----------------------------------------------------------------------------


@given(parsers.parse('I have an {admin_mode_value:S} SDPSubarray device'))
def subarray_device(devices, admin_mode_value: str):
    """Get the SDPSubarray device proxy.

    :param devices: the devices in a MultiDeviceTestContext
    :param admin_mode_value: adminMode value to set

    """
    device = devices.get_device('test_sdp/elt/subarray_1')

    # Initialise SDPSubarray device
    device.adminMode = AdminMode[admin_mode_value]

    # Reset state to OFF and obsState to EMPTY
    if device.state().name == 'OFF' and device.obsState.name == 'EMPTY':
        pass
    else:
        call_command(device, 'Off')
    assert device.state() == tango.DevState.OFF
    assert device.obsState == ObsState.EMPTY

    # Clear the config DB
    if ska_sdp_config is not None \
            and SDPSubarray.is_feature_active('config_db'):
        config_db_client = ska_sdp_config.Config()
        config_db_client._backend.delete("/pb", must_exist=False,
                                         recursive=True)
        config_db_client._backend.delete("/sb", must_exist=False,
                                         recursive=True)

    return device


# -----------------------------------------------------------------------------
# When Steps : Describe an event or action
# -----------------------------------------------------------------------------

@when('the device is initialised')
def init_device(subarray_device):
    """Initialise the subarray device.

    :param subarray_device: an SDPSubarray device

    """
    subarray_device.Init()


@when(parsers.parse('the state is {state:S}'))
def set_subarray_device_state(subarray_device, state: str):
    """Set the device state to the specified value.

    :param subarray_device: an SDPSubarray device.
    :param state: an SDPSubarray state string.

    """
    if state == 'OFF':
        pass
    elif state == 'ON':
        call_command(subarray_device, 'On')

    assert subarray_device.state() == tango.DevState.names[state]


@when(parsers.parse('obsState is {initial_obs_state:S}'))
@when('obsState is <initial_obs_state>')
def set_subarray_device_obstate(subarray_device, initial_obs_state: str):
    """Set the obsState to the specified value.

    :param subarray_device: an SDPSubarray device
    :param initial_obs_state: an SDPSubarray ObsState enum string

    If the device state is OFF, this function turns in ON.

    """
    # If the state is OFF, call the On command
    if subarray_device.state() == tango.DevState.OFF:
        call_command(subarray_device, 'On')

    # Set obsState by calling commands
    if initial_obs_state == 'EMPTY':
        pass
    elif initial_obs_state == 'IDLE':
        call_command(subarray_device, 'AssignResources')
    elif initial_obs_state == 'READY':
        call_command(subarray_device, 'AssignResources')
        call_command(subarray_device, 'Configure')
    elif initial_obs_state == 'SCANNING':
        call_command(subarray_device, 'AssignResources')
        call_command(subarray_device, 'Configure')
        call_command(subarray_device, 'Scan')
    elif initial_obs_state == 'ABORTED':
        call_command(subarray_device, 'AssignResources')
        call_command(subarray_device, 'Abort')
    elif initial_obs_state == 'FAULT':
        # Note this configures an SBI
        call_command(subarray_device, 'AssignResources')
        call_command_with_invalid_json(subarray_device, 'Configure')
    else:
        msg = 'obsState {} is not settable with commands'
        raise ValueError(msg.format(initial_obs_state))

    # Check obsState
    assert subarray_device.ObsState == ObsState[initial_obs_state]


@when(parsers.parse('I call {command:S}'))
@when('I call <command>')
def call_command(subarray_device, command):
    """Call an SDPSubarray command.

     :param subarray_device: an SDPSubarray device
     :param command: the name of the command

     """
    print('command = ', command)
    command_list = subarray_device.get_command_list()
    assert command in command_list
    command_config = subarray_device.get_command_config(command)
    # Get command function
    command_func = getattr(subarray_device, command)

    if command_config.in_type == tango.DevVoid:
        command_func()
    elif command_config.in_type == tango.DevString:
        # Read the configuration string for the command
        config_file = 'command_{}.json'.format(command)
        path = join(dirname(__file__), 'data', config_file)
        try:
            with open(path, 'r') as file:
                config_str = file.read()
        except FileNotFoundError:
            msg = 'Cannot read configuration string for {} command'
            raise ValueError(msg.format(command))
        # Call the command
        command_func(config_str)
    else:
        msg = 'Test cannot handle argument of type {}'
        raise ValueError(msg.format(command_config.in_type))


@when(parsers.parse('I call {command:S} with an invalid JSON configuration'))
@when('I call <command> with an invalid JSON configuration')
def call_command_with_invalid_json(subarray_device, command):
    """Call an SDPSubarray command with invalid JSON.

    :param subarray_device: an SDPSubarray device
    :param command: the name of the command

    """
    command_list = subarray_device.get_command_list()
    assert command in command_list
    # Get the command function
    command_func = getattr(subarray_device, command)

    config_file = 'command_{}_invalid.json'.format(command)
    path = join(dirname(__file__), 'data', config_file)
    try:
        with open(path, 'r') as file:
            config_str = file.read()
    except FileNotFoundError:
        config_str = '{}'
    print(config_str)

    with pytest.raises(tango.DevFailed):
        command_func(config_str)

# -----------------------------------------------------------------------------
# Then Steps : Describe an expected outcome or result
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
    assert subarray_device.adminMode == AdminMode[expected], \
        "actual != expected"


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
def command_raises_dev_failed_error(subarray_device, command):
    """Check that calling command raises a tango.DevFailed error.

    :param subarray_device: An SDPSubarray device.
    :param command: the name of the command.
    """
    print('command = ', command)
    command_list = subarray_device.get_command_list()
    assert command in command_list
    command_config = subarray_device.get_command_config(command)
    # Get the command function
    command_func = getattr(subarray_device, command)

    with pytest.raises(tango.DevFailed):
        if command_config.in_type == tango.DevVoid:
            command_func()
        elif command_config.in_type == tango.DevString:
            command_func('{}')
        else:
            msg = 'Test cannot handle command input of type {}'
            raise ValueError(msg.format(command_config.in_type))


@then('the processing blocks should be in the config DB')
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


@then('the receiveAddresses attribute should return the expected value')
def receive_addresses_attribute_ok(subarray_device):
    """Check that the receiveAddresses attribute works as expected.

    :param subarray_device: An SDPSubarray device.
    """
    receive_addresses = subarray_device.receiveAddresses
    receive_addresses = json.loads(receive_addresses)

    if ska_sdp_config is not None \
            and SDPSubarray.is_feature_active('config_db'):
        validate_sdp_receive_addresses(3, receive_addresses, 2)


@then('the receiveAddresses attribute should return an empty JSON object')
def receive_addresses_empty(subarray_device):
    """Check that receiveAddresses attribute returns an empty JSON object.

    :param subarray_device: An SDPSubarray device.
    """
    receive_addresses = subarray_device.receiveAddresses
    assert receive_addresses == 'null'
