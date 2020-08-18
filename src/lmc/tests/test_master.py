"""SDP Master device tests."""

# pylint: disable=redefined-outer-name
# pylint: disable=duplicate-code

import pytest
from pytest_bdd import (given, parsers, scenarios, then, when)

import tango

from ska_sdp_lmc import HealthState


# -------------------------------
# Get scenarios from feature file
# -------------------------------

scenarios('features/master.feature')


# -----------
# Given steps
# -----------

@given('I have an SDPMaster device')
def master_device(devices):
    """Get the SDPMaster device proxy.

    :param devices: the devices in a MultiDeviceTestContext

    """
    device = devices.get_device('test_sdp/elt/master')
    return device


# ----------
# When steps
# ----------

@when('the device is initialised')
def initialise_device(master_device):
    """Initialise the device.

    :param master_device: SDPMaster device

    """
    master_device.Init()


@when(parsers.parse('the state is {initial_state:S}'))
@when('the state is <initial_state>')
def set_device_state(master_device, initial_state):
    """Set the device state.

    :param master_device: SDPMaster device
    :param state_value: desired device state

    """
    current_state = master_device.state().name

    if initial_state == 'OFF' and current_state != 'OFF':
        command(master_device, 'Off')
    elif initial_state == 'STANDBY' and current_state != 'STANDBY':
        command(master_device, 'Standby')
    elif initial_state == 'DISABLE' and current_state != 'DISABLE':
        command(master_device, 'Disable')
    elif initial_state == 'ON' and current_state != 'ON':
        command(master_device, 'On')

    assert master_device.state() == tango.DevState.names[initial_state]


@when(parsers.parse('I call {command:S}'))
@when('I call <command>')
def command(master_device, command):
    """Call the device commands.

    :param master_device: SDPMaster device
    :param command: name of command to call

    """
    # Check command is present
    command_list = master_device.get_command_list()
    assert command in command_list
    # Get command function
    command_func = getattr(master_device, command)
    # Call the command
    command_func()


# ----------
# Then steps
# ----------

@then(parsers.parse('the state should be {final_state:S}'))
@then('the state should be <final_state>')
def check_device_state(master_device, final_state):
    """Check the device state.

    :param master_device: SDPMaster device
    :param final_state: expected state value

    """
    assert master_device.state() == tango.DevState.names[final_state]


@then(parsers.parse('healthState should be {health_state_value:S}'))
def check_health_state(master_device, health_state_value):
    """Check healthState.

    :param master_device: SDPMaster device
    :param health_state_value: expected healthState value

    """
    assert master_device.healthState == HealthState[health_state_value]


@then(parsers.parse('calling {command:S} should raise tango.DevFailed'))
@then('calling <command> should raise tango.DevFailed')
def command_raises_dev_failed_error(master_device, command):
    """Check that calling command raises a tango.DevFailed error.

    :param master_device: An SDPMaster device.
    :param command: the name of the command.
    """
    # Check command is present
    command_list = master_device.get_command_list()
    assert command in command_list
    # Get command function
    command_func = getattr(master_device, command)
    with pytest.raises(tango.DevFailed):
        # Call the command
        command_func()
