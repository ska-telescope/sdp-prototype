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

import pytest
from pytest_bdd import (given, parsers, scenarios, then, when)

from SDPSubarray import (SDPSubarray, AdminMode, HealthState, ObsState)

try:
    import ska_sdp_config
except ImportError:
    ska_sdp_config = None


# -----------------------------------------------------------------------------
# Scenarios : Specify what we want the software to do
# -----------------------------------------------------------------------------

# Load all scenarios from the specified feature file.
scenarios('./1_XR-11.feature')


# -----------------------------------------------------------------------------
# Given Steps : Used to describe the initial context of the system.
# -----------------------------------------------------------------------------


@given(parsers.parse('I have an {admin_mode_value} SDPSubarray device'))
def subarray_device(tango_context, admin_mode_value: str):
    """Get a SDPSubarray device object

    :param tango_context: fixture providing a TangoTestContext
    :param admin_mode_value: adminMode value the device is created with
    """
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


@when(parsers.parse('obsState is {value}'))
@when('obsState is <value>')
def set_obs_state(subarray_device, value):
    """Set the obsState attribute to the specified value.

    :param subarray_device: An SDPSubarray device.
    :param value: An SDPSubarray ObsState enum string.
    """
    subarray_device.obsState = ObsState[value]


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


@then(parsers.parse('State should be {expected}'))
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
            'attr_receiveAddresses-cbfOutputLink-disabled.json'
        )
        with open(expected_output_file, 'r') as file:
            expected = json.loads(file.read())
        receive_addresses = json.loads(receive_addresses)
        assert receive_addresses == expected


@then('the receiveAddresses attribute should return an empty JSON object')
def receive_addresses_empty(subarray_device):
    """Check that receiveAddresses attribute returns an empty JSON object.

    :param subarray_device: An SDPSubarray device.
    """
    receive_addresses = subarray_device.receiveAddresses
    assert receive_addresses == 'null'
