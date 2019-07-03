# coding: utf-8

import pytest

from tango.test_context import DeviceTestContext
from SDPSubarray import SDPSubarray


@pytest.fixture(scope='session', autouse=True)
def tango_context(request):
    """Create a test device context for the SDPSubarray device."""
    device = SDPSubarray
    device_name = 'mid_sdp/elt/subarray_00'
    properties = {'CapabilityTypes': '',
                  'CentralLoggingTarget': '',
                  'ElementLoggingTarget': '',
                  'GroupDefinitions': '',
                  'SkaLevel': '4',
                  'StorageLoggingTarget': 'localhost',
                  'SubID': ''
                  }
    context = DeviceTestContext(device, device_name=device_name,
                                properties=properties)

    context.start()
    yield context
    context.stop()

    # def fin():
    #     print("teardown!")
    #     context.stop()
    # request.addfinalizer(fin)
    # context.start()
    # return context
