# coding: utf-8
"""SDP Subarray device tests."""
# pylint: disable=redefined-outer-name

from random import randint

import json
from os.path import dirname, join

import pytest
from pytest_bdd import (given, parsers, scenarios, then, when)

import tango
from tango import DevState

from SDPSubarray import AdminMode, ObsState


# -----------------------------------------------------------------------------
# Scenarios : Specify what we want the software to do
# -----------------------------------------------------------------------------

# Load all scenarios from the specified feature file.
scenarios('./1_XR-11.feature')


# -----------------------------------------------------------------------------
# Given Steps : Used to describe the initial context of the system.
# -----------------------------------------------------------------------------


@given('I have a SDPSubarray device')
def subarray_device(tango_context):
    """Get a SDPSubarray device object

    :param tango_context: fixture providing a TangoTestContext
    """
    return tango_context.device


# -----------------------------------------------------------------------------
# When Steps : Describe an event or action
# -----------------------------------------------------------------------------


@when('The device is initialised')
def init_device(subarray_device):
    """Initialise the subarray device.

    :param subarray_device: An SDPSubarray device.
    """
    subarray_device.Init()


@when(parsers.parse('I set adminMode to {value}'))
def set_admin_mode(subarray_device, value: str):
    """Set the adminMode to the specified value.

    :param subarray_device: An SDPSubarray device.
    :param value: Value to set the adminMode attribute to.
    """
    subarray_device.adminMode = AdminMode[value]


@when('I call AssignResources')
def command_assign_resources(subarray_device):
    """Call the AssignResources command.

    This requires that the device exists, takes a string, and does not
    return a value.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'AssignResources' in subarray_device.get_command_list()
    command_info = subarray_device.get_command_config('AssignResources')
    assert command_info.in_type == tango.DevString
    assert command_info.out_type == tango.DevVoid

    # For SDP assign resources is a noop so can be called with an empty string.
    subarray_device.AssignResources('')


@when('I call ReleaseResources')
def command_release_resources(subarray_device):
    """Call the ReleaseResources command.

    :param subarray_device: An SDPSubarray device.
    """
    assert 'ReleaseResources' in subarray_device.get_command_list()
    # For SDP release resources is a noop so can be called with an empty
    # string.
    subarray_device.ReleaseResources('')


@when('The obsState != IDLE')
def obs_state_not_idle(subarray_device):
    """Set the obsState to a random state that is *not* IDLE.

    :param subarray_device: An SDPSubarray device.
    """
    subarray_device.obsState = randint(1, 6)  # ObsState.IDLE == 0


@when(parsers.parse('obsState == {value}'))
def set_obs_state(subarray_device, value):
    """Set the obsState attribute to the {commanded state}.

    :param subarray_device: An SDPSubarray device.
    :param value: An SDPSubarray ObsState enum string.
    """
    subarray_device.obsState = ObsState[value]


@when('I call Configure')
def command_configure(subarray_device):
    """Call the Configure command.

    :param subarray_device: An SDPSubarray device.
    """

    pb_config_path = join(dirname(__file__), 'data',
                          'pb_config.json')
    with open(pb_config_path, 'r') as file:
        pb_config = json.loads(file.read())
    # print(pb_config)
    subarray_device.Configure(pb_config)


@when('I call Configure Scan')
def command_configure_scan(subarray_device):
    """Call the Configure Scan command.

    :param subarray_device: An SDPSubarray device.
    """
    scan_config_path = join(dirname(__file__), 'data',
                            'scan_config.json')
    with open(scan_config_path, 'r') as file:
        scan_config = json.loads(file.read())
    subarray_device.ConfigureScan(scan_config)


# -----------------------------------------------------------------------------
# Then Steps : Describe an expected outcome or result
# -----------------------------------------------------------------------------


@then(parsers.parse('State == {expected}'))
def device_state_equals(subarray_device, expected):
    """Check the Subarray device device state.

    :param subarray_device: An SDPSubarray device.
    :param expected: The expected device state.
    """
    assert subarray_device.state() == DevState.names[expected]


@then(parsers.parse('obsState == {expected}'))
def obs_state_equals(subarray_device, expected):
    """Check the Subarray obsState attribute value.

    :param subarray_device: An SDPSubarray device.
    :param expected: The expected obsState.
    """
    assert subarray_device.obsState == ObsState[expected]


@then(parsers.parse('adminMode == {expected}'))
def admin_mode_equals(subarray_device, expected):
    """Check the Subarray adminMode value.

    :param subarray_device: An SDPSubarray device.
    :param expected: The expected adminMode.
    """
    assert subarray_device.adminMode == AdminMode[expected]


@then(parsers.parse('adminMode either ONLINE or MAINTENANCE'))
def admin_mode_online_or_maintenance(subarray_device):
    """Check the Subarray adminMode is ONLINE or in MAINTENANCE mode.

    :param subarray_device: An SDPSubarray device.
    """
    assert subarray_device.adminMode in (AdminMode.ONLINE,
                                         AdminMode.MAINTENANCE)


@then('Calling AssignResources raises tango.DevFailed')
def dev_failed_error_raised(subarray_device):
    """Check that calling AssignResources raises a tango.DevFailed error.

    :param subarray_device: An SDPSubarray device.
    """
    with pytest.raises(tango.DevFailed):
        subarray_device.AssignResources()
