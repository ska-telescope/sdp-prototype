# coding: utf-8
"""Pytest plugins."""

from unittest.mock import Mock

import pytest
from tango.test_context import DeviceTestContext

from SDPSubarray import SDPSubarray
from SDPSubarray.release import VERSION


@pytest.fixture(scope='session', autouse=True)
def tango_context():
    """Fixture that creates SDPSubarray DeviceTestContext object."""
    # pylint: disable=redefined-outer-name
    device_name = 'mid_sdp/elt/subarray_1'
    properties = dict(version=VERSION)
    tango_context = DeviceTestContext(SDPSubarray,
                                      device_name=device_name,
                                      properties=properties)
    tango_context.start()
    SDPSubarray.get_name = Mock(side_effect=tango_context.get_device_access)
    yield tango_context
    tango_context.stop()
