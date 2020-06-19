"""Pytest fixtures."""

# pylint: disable=redefined-outer-name

import pytest
from tango.test_context import DeviceTestContext


@pytest.fixture(scope='module')
def device_info(request):
    """Get device_info from test module."""
    yield getattr(request.module, 'device_info')


@pytest.fixture(scope='module')
def device(device_info):
    """Create an instance of the device in a Tango DeviceTestContext.

    This uses process=True, otherwise it is impossible to create more than one
    test context during the session.

    """
    context = DeviceTestContext(
        device_info['class'],
        device_name=device_info['name'],
        process=True
    )
    with context as device_to_test:
        yield device_to_test
