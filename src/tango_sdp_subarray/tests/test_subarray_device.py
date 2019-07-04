# coding: utf-8
"""SDP Subarray device feature tests."""

from random import randint
from pytest_bdd import (
    given,
    scenario,
    parsers,
    then,
    when
)
import pytest

import tango
from tango import DevState
from SDPSubarray import ObsState, AdminMode

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


# scenarios('../features/1_XR-7.feature')


@scenario('./1_XR-7.feature', 'Device Startup')
def test_startup():
    pass


@scenario('./1_XR-7.feature', 'Assign Resources successfully')
def test_assign_resources_successfully():
    pass


@scenario('./1_XR-7.feature', 'Assign Resources fails when ObsState != IDLE')
def test_assign_resources_invalid_obs_state():
    pass


@scenario('./1_XR-7.feature', 'Release Resources successfully')
def test_release_resources_successfully():
    pass


@scenario('./1_XR-7.feature', 'Configure command successfully')
def test_configure_successfully():
    pass


# ------
# Given
# ------


@given('I have a SDPSubarray device')
def device(tango_context):
    """A SDPSubarray device object"""
    device = tango_context.device
    return device


# ------
# When
# ------


@when('The device is initialised')
def init_device(device):
    """Initialise the subarray device."""
    device.Init()


@when(parsers.parse('I set adminMode to {commanded_state}'))
def set_admin_mode(device, commanded_state):
    """Set the adminMode."""
    device.adminMode = AdminMode[commanded_state]


@when('I call AssignResources')
def command_assign_resources(device):
    """Call the AssignResources command."""
    assert 'AssignResources' in device.get_command_list()
    command_info = device.get_command_config('AssignResources')
    assert command_info.in_type == tango.DevString
    assert command_info.out_type == tango.DevVoid
    device.AssignResources('NOOP')


@when('I call ReleaseResources')
def command_release_resources(device):
    assert 'ReleaseResources' in device.get_command_list()
    device.ReleaseResources('NOOP')


@when('The obsState != IDLE')
def obs_state_not_idle(device):
    """Set the obsState to a random state that is *not* IDLE"""
    device.obsState = randint(1, 6)  # ObsState.IDLE == 0


@when(parsers.parse('obsState == {commanded_state}'))
def set_obs_state(device, commanded_state):
    """Set the obsState attribute to the {commanded state}."""
    device.obsState = ObsState[commanded_state]


@when('I call Configure')
def command_configure(device):
    """Call the Configure command."""
    device.Configure('')

# ------
# Then
# ------


@then(parsers.parse('State == {expected_state}'))
def device_state_equals(device, expected_state):
    """Check the Subarray device device state."""
    assert device.state() == DevState.names[expected_state]


@then(parsers.parse('obsState == {expected_state}'))
def obs_state_equals(device, expected_state):
    """Check the Subarray device obsState"""
    assert device.obsState == ObsState[expected_state]


@then(parsers.parse('adminMode == {expected_state}'))
def admin_mode_equals(device, expected_state):
    """Check the Subarray device adminMode"""
    assert device.adminMode == AdminMode[expected_state]


@then(parsers.parse('adminMode either ONLINE or MAINTENANCE'))
def admin_mode_online_or_maintenance(device):
    """Check the Subarray device adminMode"""
    assert device.adminMode in (AdminMode.ONLINE, AdminMode.MAINTENANCE)


@then('Calling AssignResources raises tango.DevFailed')
def dev_failed_error_raised(device):
    """Check that calling AssignResources raises a tango.DevFailed error."""
    with pytest.raises(tango.DevFailed):
        device.AssignResources('NOOP')



