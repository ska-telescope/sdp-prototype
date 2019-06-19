# coding: utf-8
"""Tests for the TestDeviceServer."""
# pylint: disable=redefined-outer-name,invalid-name
import pytest

from tango.test_utils import DeviceTestContext

from ..release import __version__

from ..TestDevice import TestDevice


@pytest.fixture(scope="module")
def test_device_context():
    """Create a test device context for the TestDeviceServer."""
    device_name = "orca_sdp/elt/test_device_00"
    context = DeviceTestContext(TestDevice,
                                device_name=device_name,
                                properties=dict(version=__version__))
    context.start()
    yield context
    context.stop()


def test_has_version_attribute(test_device_context):
    """Verify that the device has a version attribute."""
    device = test_device_context.device
    assert device.name() == 'orca_sdp/elt/test_device_00'

    # Check that the device has a version attribute
    assert 'up_time' in device.get_attribute_list()
