"""Pytest fixtures."""

# pylint: disable=redefined-outer-name

import logging
import pytest

from tango.test_context import MultiDeviceTestContext

from ska_sdp_lmc import SDPMaster, SDPSubarray, subarray

logging.basicConfig(level=logging.DEBUG)

# Turn off the SDP config DB in the subarray by default. This will be
# overridden if the TOGGLE_CONFIG_DB environment variable is set to 1.
subarray.FEATURE_CONFIG_DB.set_default(False)
subarray.FEATURE_EVENT_LOOP.set_default(False)
# subarray_config.SubarrayConfig.get_receive_addresses =\
#     Mock(return_value=RECEIVE_ADDRESSES)

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
