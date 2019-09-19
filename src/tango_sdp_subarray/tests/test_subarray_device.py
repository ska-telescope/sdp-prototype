# coding: utf-8
"""SDP Subarray device tests."""
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=fixme

import json
from os.path import dirname, join
from unittest.mock import MagicMock

import tango
from tango import DevState

import pytest
from pytest_bdd import (given, parsers, scenarios, then, when)

from SDPSubarray import AdminMode, HealthState, ObsState, SDPSubarray, \
    init_logger

try:
    from ska_sdp_config.config import Config as ConfigDbClient
except ImportError:
    ConfigDbClient = None


try:
    from ska_sdp_config.config import Config as ConfigDbClient
except ImportError:
    ConfigDbClient = None


# -----------------------------------------------------------------------------
# Scenarios : Specify what we want the software to do
# -----------------------------------------------------------------------------

# Load all scenarios from the specified feature file.
scenarios('./1_XR-11.feature')


# Initialise logger for cases where the python logging output is useful
# to debug tests.
init_logger(level='DEBUG')


# -----------------------------------------------------------------------------
# Mock functions
# -----------------------------------------------------------------------------

def mock_read_cbf_output_link():
    """Mock replacement of SDPSubarray device _read_channel_link_map method."""
    filename = 'attr_cbfOutputLink-simple.json'
    path = join(dirname(__file__), 'data', filename)
    with open(path, 'r') as file:
        channel_link_map = file.read()
    channel_link_map_dict = json.loads(channel_link_map)
    channel_link_map_dict['scanID'] = 4
    return json.dumps(channel_link_map_dict)


# -----------------------------------------------------------------------------
# Given Steps : Used to describe the initial context of the system.
# -----------------------------------------------------------------------------


@given(parsers.parse('I have an {admin_mode_value} SDPSubarray device'))
def subarray_device(tango_context, admin_mode_value: str):
    """Get a SDPSubarray device object

    :param tango_context: fixture providing a TangoTestContext
    :param admin_mode_value: adminMode value the device is created with
    """
    # Mock the SDPSubarray._read_cbf_out_link() method so that
    # it does not need to connect to a CSP subarray device.
    SDPSubarray._read_cbf_output_link = MagicMock(
        side_effect=mock_read_cbf_output_link)
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


@when(parsers.parse('obsState is {value}'))
@when('obsState is <value>')
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
    filename = join(dirname(__file__), 'data', 'command_Configure.json')
    with open(filename, 'r') as file:
        config_json = file.read()
    config_dict = json.loads(config_json)
    config_dict['configure']['scanParameters'] = {}
    config_dict['configure']['scanParameters']["4"] = {}
    # print('-------')
    # print(json.dumps(config_dict, indent=2))
    # print('-------')
    subarray_device.Configure(json.dumps(config_dict))


@when('I call Configure with invalid JSON')
def command_configure_invalid_json(subarray_device):
    """Call the Configure command with invalid json.

    :param subarray_device: An SDPSubarray device.
    """
    with pytest.raises(tango.DevFailed):
        subarray_device.Configure('{}')

        
@when('I call ConfigureScan')
def command_configure_scan(subarray_device):
    """Call the Configure Scan command.

    :param subarray_device: An SDPSubarray device.
    # """

    scan_config_path = join(dirname(__file__), 'data',
                            'command_ConfigureScan.json')
    with open(scan_config_path, 'r') as file:
        scan_config = file.read()
    subarray_device.ConfigureScan(scan_config)


@when('I call StartScan')
def command_start_scan(subarray_device):
    """Call the Start Scan command.

    :param subarray_device: An SDPSubarray device.
    # """

    subarray_device.StartScan()


@when('I call EndScan')
def command_end_scan(subarray_device):
    """Call the End Scan command.

    :param subarray_device: An SDPSubarray device.
    # """

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


@then('adminMode should be ONLINE or MAINTENANCE')
def admin_mode_online_or_maintenance(subarray_device):
    """Check the Subarray adminMode is ONLINE or in MAINTENANCE mode.

    :param subarray_device: An SDPSubarray device.
    """
    assert subarray_device.adminMode in (AdminMode.ONLINE,
                                         AdminMode.MAINTENANCE)


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
        subarray_device.AssignResources()


@then('calling ReleaseResources raises tango.DevFailed')
def dev_failed_error_raised_by_release_resources(subarray_device):
    """Check that calling ReleaseResources raises a tango.DevFailed error.

    :param subarray_device: An SDPSubarray device.
    """
    with pytest.raises(tango.DevFailed):
        subarray_device.ReleaseResources()


@then('The configured Processing Block should be in the Config Db')
def check_config_db():
    """Check that the config db has the configured PB.

    Only run this step if the config db is enabled.
    """
    if ConfigDbClient and SDPSubarray.is_feature_active('config_db'):
        filename = join(dirname(__file__), 'data', 'command_Configure.json')
        with open(filename, 'r') as file:
            config_json = file.read()
        config_dict = json.loads(config_json)
        config_db_client = ConfigDbClient()
        for txn in config_db_client.txn():
            pb_ids = txn.list_processing_blocks()
            # print()
            # print('--------------')
            # print(pb_ids)
            # print('--------------')
            assert config_dict['configure']['id'] in pb_ids


@then('The receiveAddresses attribute returns expected values')
def receive_addresses_attribute_ok(subarray_device):
    """Check that the receiveAddresses attribute works as expected.

    :param subarray_device: An SDPSubarray device.
    """
    receive_addresses = subarray_device.receiveAddresses
    # print(json.dumps(json.loads(receive_addresses), indent=2))
    data_path = join(dirname(__file__), 'data')

    expected_output_file = ''
    if not SDPSubarray.is_feature_active('cbf_output_link'):
        expected_output_file = join(
            data_path, 'attr_receiveAddresses-cbfOutputLink-disabled.json')
    elif isinstance(SDPSubarray._read_cbf_output_link, MagicMock):
        expected_output_file = join(
            data_path, 'attr_receiveAddresses-simple.json')
    else:
        pytest.fail('Not yet able to test using a mock CSP Subarray device')

    with open(expected_output_file, 'r') as file:
        expected = json.loads(file.read())

    expected['scanId'] = 4
    receive_addresses = json.loads(receive_addresses)
    assert receive_addresses == expected


@then('The receiveAddresses attribute should return an empty JSON object')
def receive_addresses_empty(subarray_device):
    """Check that receiveAddresss attribute returns an empty JSON object.

    :param subarray_device: An SDPSubarray device.
    """
    receive_addresses = subarray_device.receiveAddresses
    assert str(receive_addresses) == 'null'
