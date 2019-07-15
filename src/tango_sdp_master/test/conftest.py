# coding: utf-8
"""
A module defining a list of fixture functions that are shared across all the skabase
tests.
"""

import pytest

from tango.test_context import DeviceTestContext
from SDPMaster import SDPMaster


@pytest.fixture(scope='session', autouse=True)
def tango_context(request):
    """Create a test device context for the SDPMaster device."""
    device = SDPMaster
    tango_context = DeviceTestContext(device)

    tango_context.start()
    yield tango_context
    tango_context.stop()
