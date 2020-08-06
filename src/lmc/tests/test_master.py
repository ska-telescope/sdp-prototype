"""SDP Master device tests."""

# pylint: disable=redefined-outer-name
# pylint: disable=duplicate-code

from pytest_bdd import (given, parsers, scenarios, then, when)

from tango import DevState

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


@when(parsers.parse('the state is {state_value}'))
@when('the state is <state_value>')
def set_device_state(master_device, state_value):
    """Set the device state.

    :param master_device: SDPMaster device
    :param state_value: desired device state

    """
    current_state = master_device.state().name

    if state_value == 'OFF' and current_state != 'OFF':
        master_device.Off()
    elif state_value == 'STANDBY' and current_state != 'STANDBY':
        master_device.Standby()
    elif state_value == 'DISABLE' and current_state != 'DISABLE':
        master_device.Disable()
    elif state_value == 'ON' and current_state != 'ON':
        master_device.On()

    assert master_device.state() == DevState.names[state_value]


@when(parsers.parse('I call {command_name}'))
def command(master_device, command_name):
    """Call the device commands.

    :param master_device: SDPMaster device
    :param command_name: name of command to call

    """
    if command_name == 'Off':
        master_device.Off()
    elif command_name == 'Standby':
        master_device.Standby()
    elif command_name == 'Disable':
        master_device.Disable()
    elif command_name == 'On':
        master_device.On()


# ----------
# Then steps
# ----------

@then(parsers.parse('the state should be {state_value}'))
def check_device_state(master_device, state_value):
    """Check the device state.

    :param master_device: SDPMaster device
    :param state_value: expected state value

    """
    assert master_device.state() == DevState.names[state_value]


@then(parsers.parse('healthState should be {health_state_value}'))
def check_health_state(master_device, health_state_value):
    """Check healthState.

    :param master_device: SDPMaster device
    :param health_state_value: expected healthState value

    """
    assert master_device.healthState == HealthState[health_state_value]
