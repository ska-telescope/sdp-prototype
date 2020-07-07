# coding: utf-8
"""SDP Subarray device tests."""
# pylint: disable=invalid-name
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=fixme

import json
from os.path import dirname, join

import tango
from tango import DevState

from ska_telmodel.sdp.schema import validate_sdp_receive_addresses

import pytest
from pytest_bdd import (given, parsers, scenarios, then, when)

from SDPSubarray import (AdminMode, HealthState, ObsState, SDPSubarray)

try:
    import ska_sdp_config
except ImportError:
    ska_sdp_config = None

# -----------------------------------------------------------------------------
# Scenarios : Specify what we want the software to do
# -----------------------------------------------------------------------------

# Load all scenarios from the specified feature file.
scenarios('./1_VTS-223-2.feature')


# -----------------------------------------------------------------------------
# Given Steps : Used to describe the initial context of the system.
# -----------------------------------------------------------------------------


@given(parsers.parse('I have an {admin_mode_value} SDPSubarray device'))
def subarray_device(tango_context, admin_mode_value: str):
    """Get a SDPSubarray device object

    :param tango_context: fixture providing a TangoTestContext
    :param admin_mode_value: adminMode value the device is created with
    """

    # Initialise SDPSubarray device
    device = tango_context.device
    device.adminMode = AdminMode[admin_mode_value]

    # Resetting state to OFF and obsState to EMPTY
    state_value = device.state().name
    obs_state_value = device.obsState.name

    if state_value == 'OFF' and obs_state_value == 'EMPTY':
        pass
    else:
        command_off(device)

    assert device.state() == DevState.OFF
    assert device.obsState == ObsState.EMPTY

    # Clear the Database
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

    :param subarray_device: An SDPSubarray device.
    """
    subarray_device.Init()


@when(parsers.parse('the state is {state_value}'))
@when('the state is <state_value>')
def set_subarray_device_state(subarray_device, state_value: str):
    """Set the device state to the specified value.

    :param subarray_device: An SDPSubarray device.
    :param state_value: An SDPSubarray state string.

    """
    if state_value == 'OFF':
        pass
    elif state_value == 'ON':
        command_on(subarray_device)

    assert subarray_device.state() == DevState.names[state_value]


@when(parsers.parse('obsState is {obs_state_value}'))
@when('obsState is <obs_state_value>')
def set_subarray_device_obstate(subarray_device, obs_state_value: str):
    """Set the obsState to the specified value.

    :param subarray_device: An SDPSubarray device.
    :param obs_state_value: An SDPSubarray ObsState enum string.

    If the device state is OFF, this function turns in ON.

    """
    # If the state is OFF, call the On command
    if subarray_device.state() == DevState.OFF:
        command_on(subarray_device)

    # Set obsState by calling commands
    if obs_state_value == 'EMPTY':
        pass
    elif obs_state_value == 'IDLE':
        command_assign_resources(subarray_device)
    elif obs_state_value == 'READY':
        command_assign_resources(subarray_device)
        command_configure(subarray_device)
    elif obs_state_value == 'SCANNING':
        command_assign_resources(subarray_device)
        command_configure(subarray_device)
        command_scan(subarray_device)
    elif obs_state_value == 'ABORTED':
        command_assign_resources(subarray_device)
        command_abort(subarray_device)
    elif obs_state_value == 'FAULT':
        # Note this configures an SBI
        command_assign_resources(subarray_device)
        command_configure_invalid_json(subarray_device)
    else:
        raise ValueError(
            'obsState {} not settable with commands'.format(obs_state_value)
        )

    # Check obs_state value
    assert subarray_device.ObsState == ObsState[obs_state_value]


@when('I call On')
def command_on(subarray_device):
    """Call the ReleaseResources command.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'On' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('On')
    assert command_info.in_type == tango.DevVoid
    assert command_info.out_type == tango.DevVoid

    subarray_device.On()


@when('I call Off')
def command_off(subarray_device):
    """Call the ReleaseResources command.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'Off' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('Off')
    assert command_info.in_type == tango.DevVoid
    assert command_info.out_type == tango.DevVoid

    subarray_device.Off()


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

    subarray_device.AssignResources(config_str)


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


@when('I call End')
def command_end(subarray_device):
    """Call the End command.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'End' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('End')
    assert command_info.in_type == tango.DevVoid
    assert command_info.out_type == tango.DevVoid

    subarray_device.End()


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


@when('I call Abort')
def command_abort(subarray_device):
    """Call the Abort command.

    :param subarray_device: An SDPSubarray device.
    """
    # TODO Need to think about how to set CONFIGURING AND RESETTING state
    assert 'Abort' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('Abort')
    assert command_info.in_type == tango.DevVoid
    assert command_info.out_type == tango.DevVoid

    subarray_device.Abort()


@when('I call ObsReset')
def command_obs_reset(subarray_device):
    """Call the ObsReset command.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'ObsReset' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('ObsReset')
    assert command_info.in_type == tango.DevVoid
    assert command_info.out_type == tango.DevVoid

    subarray_device.ObsReset()


@when('I call Restart')
def command_restart(subarray_device):
    """Call the Restart command.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'Restart' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('Restart')
    assert command_info.in_type == tango.DevVoid
    assert command_info.out_type == tango.DevVoid

    subarray_device.Restart()


# -----------------------------------------------------------------------------
# Then Steps : Describe an expected outcome or result
# -----------------------------------------------------------------------------


@then(parsers.parse('the state should be {expected}'))
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


@then(parsers.parse('calling {command_name} raises tango.DevFailed'))
@then('calling <command_name> raises tango.DevFailed')
def command_raises_dev_failed_error(subarray_device, command_name):
    """Check that calling command raises a tango.DevFailed error.

    :param subarray_device: An SDPSubarray device.
    :param command_name: the name of the command.
    """
    print('command_name = ', command_name)
    command_list = subarray_device.get_command_list()
    assert command_name in command_list
    command = getattr(subarray_device, command_name)
    command_info = subarray_device.get_command_config(command_name)

    with pytest.raises(tango.DevFailed):
        if command_info.in_type == tango.DevVoid:
            command()
        elif command_info.in_type == tango.DevString:
            command('{}')
        else:
            raise ValueError('Test cannot handle command input type')


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


@then('the receiveAddresses attribute should return the expected value')
def receive_addresses_attribute_ok(subarray_device):
    """Check that the receiveAddresses attribute works as expected.

    :param subarray_device: An SDPSubarray device.
    """
    receive_addresses = subarray_device.receiveAddresses
    receive_addresses = json.loads(receive_addresses)

    if ska_sdp_config is not None \
            and SDPSubarray.is_feature_active('config_db'):
        if SDPSubarray.is_feature_active('RECEIVE_ADDRESSES_HACK'):
            validate_sdp_receive_addresses(2, receive_addresses, 2)
        else:
            validate_sdp_receive_addresses(3, receive_addresses, 2)


@then('the receiveAddresses attribute should return an empty JSON object')
def receive_addresses_empty(subarray_device):
    """Check that receiveAddresses attribute returns an empty JSON object.

    :param subarray_device: An SDPSubarray device.
    """
    receive_addresses = subarray_device.receiveAddresses
    assert receive_addresses == 'null'
