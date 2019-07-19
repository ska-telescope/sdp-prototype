# coding: utf-8
"""Pytest plugins."""
# pylint: disable=redefined-outer-name

import pytest
from tango.test_context import DeviceTestContext

from SDPMaster import SDPMaster


@pytest.fixture(scope='session', autouse=True)
def tango_context():
    """Create a test device context for the SDPMaster device."""
    device = SDPMaster
    context = DeviceTestContext(device)
    context.start()
    yield context
    context.stop()
