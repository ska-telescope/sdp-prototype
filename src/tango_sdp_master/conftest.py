# coding: utf-8
"""List of fixture functions that are shared across all the skabase tests."""

import pytest

from tango.test_context import DeviceTestContext
from SDPMaster import SDPMaster


@pytest.fixture(scope='session', autouse=True)
def tango_context():
    """Create a test device context for the SDPMaster device."""
    # pylint: disable=redefined-outer-name
    device = SDPMaster
    # device_name = 'mid_sdp/elt/sdpmaster_00'
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
