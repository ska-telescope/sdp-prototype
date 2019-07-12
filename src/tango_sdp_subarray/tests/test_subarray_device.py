# coding: utf-8
"""SDP Subarray device tests."""

from random import randint
from pytest_bdd import (
    given,
    scenarios,
    parsers,
    then,
    when
)
import pytest

import tango
from tango import DevState

from SDPSubarray import SDPSubarray
from SDPSubarray import ObsState, AdminMode

# -----------------------------------------------------------------------------
# Scenarios : Specify what we want the software to do
# -----------------------------------------------------------------------------

# Load all scenarios from the specified feature file.
scenarios('./1_XR-11.feature')


# -----------------------------------------------------------------------------
# Given Steps : Used to describe the initial context of the system.
# -----------------------------------------------------------------------------


@given('I have a SDPSubarray device')
def device(tango_context):
    """Get a SDPSubarray device object

    :param tango_context: fixture providing a TangoTestContext
    """
    device = tango_context.device
    return device


# -----------------------------------------------------------------------------
# When Steps : Describe an event or action
# -----------------------------------------------------------------------------


@when('The device is initialised')
def init_device(device: SDPSubarray):
    """Initialise the subarray device.

    :param device: An SDPSubarray device.
    """
    device.Init()


@when(parsers.parse('I set adminMode to {value}'))
def set_admin_mode(device: SDPSubarray, value: str):
    """Set the adminMode to the specified value.

    :param device: An SDPSubarray device.
    :param value: Value to set the adminMode attribute to.
    """
    device.adminMode = AdminMode[value]


@when('I call AssignResources')
def command_assign_resources(device):
    """Call the AssignResources command.

    This requires that the device exists, takes a string, and does not
    return a value.

    :param device: An SDPSubarray device.
    """
    assert 'AssignResources' in device.get_command_list()
    command_info = device.get_command_config('AssignResources')
    assert command_info.in_type == tango.DevString
    assert command_info.out_type == tango.DevVoid

    # For SDP assign resources is a noop so can be called with an empty string.
    device.AssignResources('')


@when('I call ReleaseResources')
def command_release_resources(device):
    """Call the ReleaseResources command.

    :param device: An SDPSubarray device.
    """
    assert 'ReleaseResources' in device.get_command_list()
    # For SDP release resources is a noop so can be called with an empty string.
    device.ReleaseResources('')


@when('The obsState != IDLE')
def obs_state_not_idle(device):
    """Set the obsState to a random state that is *not* IDLE.

    :param device: An SDPSubarray device.
    """
    device.obsState = randint(1, 6)  # ObsState.IDLE == 0


@when(parsers.parse('obsState == {value}'))
def set_obs_state(device, value):
    """Set the obsState attribute to the {commanded state}.

    :param device: An SDPSubarray device.
    :param value: An SDPSubarray ObsState enum string.
    """
    device.obsState = ObsState[value]


@when('I call Configure')
def command_configure(device):
    """Call the Configure command.

    :param device: An SDPSubarray device.
    """
    device.Configure('')


# -----------------------------------------------------------------------------
# Then Steps : Describe an expected outcome or result
# -----------------------------------------------------------------------------


@then(parsers.parse('State == {expected}'))
def device_state_equals(device, expected):
    """Check the Subarray device device state.

    :param device: An SDPSubarray device.
    :param expected: The expected device state.
    """
    assert device.state() == DevState.names[expected]


@then(parsers.parse('obsState == {expected}'))
def obs_state_equals(device, expected):
    """Check the Subarray obsState attribute value.

    :param device: An SDPSubarray device.
    :param expected: The expected obsState.
    """
    assert device.obsState == ObsState[expected]


@then(parsers.parse('adminMode == {expected}'))
def admin_mode_equals(device, expected):
    """Check the Subarray adminMode value.

    :param device: An SDPSubarray device.
    :param expected: The expected adminMode.
    """
    assert device.adminMode == AdminMode[expected]


@then(parsers.parse('adminMode either ONLINE or MAINTENANCE'))
def admin_mode_online_or_maintenance(device):
    """Check the Subarray adminMode is ONLINE or in MAINTENANCE mode.

    :param device: An SDPSubarray device.
    """
    assert device.adminMode in (AdminMode.ONLINE, AdminMode.MAINTENANCE)


@then('Calling AssignResources raises tango.DevFailed')
def dev_failed_error_raised(device):
    """Check that calling AssignResources raises a tango.DevFailed error.

    :param device: An SDPSubarray device.
    """
    with pytest.raises(tango.DevFailed):
        device.AssignResources()



