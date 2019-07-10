# coding: utf-8
"""Pytest plugins."""

import pytest
from tango.test_context import DeviceTestContext

from SDPSubarray import SDPSubarray


@pytest.fixture(scope='session', autouse=True)
def tango_context():
    """Fixture that creates SDPSubarray DeviceTestContext object."""
    # pylint: disable=redefined-outer-name
    tango_context = DeviceTestContext(SDPSubarray)
    tango_context.start()
    yield tango_context
    tango_context.stop()

