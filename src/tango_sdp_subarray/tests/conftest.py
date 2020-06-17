# coding: utf-8
"""Pytest plugins."""

# from unittest.mock import MagicMock

import pytest
from tango.test_context import DeviceTestContext

from SDPSubarray import SDPSubarray
from SDPSubarray.release import VERSION


@pytest.fixture(scope='session', autouse=True)
def tango_context():
    """Fixture that creates SDPSubarray DeviceTestContext object."""
    # pylint: disable=redefined-outer-name

    # Set default feature toggle values for the test.
    # Note: these are ignored if the env variables are already set. ie:
    #       TOGGLE_CONFIG_DB
    # Note: if these, or the env variables are not set, use the
    #       SDPSubarray device defaults.
    SDPSubarray.set_feature_toggle_default('config_db', True)

    device_name = 'mid_sdp/elt/subarray_1'
    properties = dict(Version=VERSION)
    tango_context = DeviceTestContext(SDPSubarray,
                                      device_name=device_name,
                                      properties=properties)
    print()
    print('Starting context...')
    tango_context.start()
    # SDPSubarray.get_name = MagicMock(
    #     side_effect=tango_context.get_device_access)
    yield tango_context
    print('Stopping context...')
    tango_context.stop()
