# coding: utf-8

import pytest

from tango.test_context import DeviceTestContext
from SDPSubarray import SDPSubarray


@pytest.fixture(scope='session', autouse=True)
def tango_context(request):
    """Create a test device context for the SDPSubarray device."""
    device = SDPSubarray
    device_name = 'mid_sdp/elt/subarray_00'
    # properties = {'CapabilityTypes': '',
    #               'CentralLoggingTarget': '',
    #               'ElementLoggingTarget': '',
    #               'GroupDefinitions': '',
    #               'SkaLevel': '4',
    #               'StorageLoggingTarget': 'localhost',
    #               'SubID': ''
    #               }
    # tango_context = DeviceTestContext(device, device_name=device_name,
    #                                   properties=properties)
    tango_context = DeviceTestContext(device)

    tango_context.start()
    yield tango_context
    tango_context.stop()

