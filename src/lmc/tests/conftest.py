"""Pytest fixtures."""

# pylint: disable=redefined-outer-name

import pytest

from tango.test_context import MultiDeviceTestContext

from ska_sdp_lmc import SDPMaster, SDPSubarray, subarray

# Use the config DB memory backend in the subarray. This will be overridden if
# the TOGGLE_CONFIG_DB environment variable is set to 1.
subarray.FEATURE_CONFIG_DB.set_default(False)
# Disable the event loop in the subarray. This will be overridden if the
# TOGGLE_EVENT_LOOP environment variable is set to 1.
subarray.FEATURE_EVENT_LOOP.set_default(False)

# List of devices for the test session
device_info = [
    {
        'class': SDPMaster,
        'devices': [
            {'name': 'test_sdp/elt/master'}
        ]
    },
    {
        'class': SDPSubarray,
        'devices': [
            {'name': 'test_sdp/elt/subarray_1'}
        ]
    }
]


@pytest.fixture(scope='session')
def devices():
    """Start the devices in a MultiDeviceTestContext."""
    context = MultiDeviceTestContext(device_info)
    context.start()
    yield context
    context.stop()
