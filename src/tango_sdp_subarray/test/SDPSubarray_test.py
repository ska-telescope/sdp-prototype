#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the SDPSubarray device."""

import sys
import os
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(path))

import pytest
from tango.test_context import DeviceTestContext
from SDPSubarray import SDPSubarray


@pytest.fixture(scope="module")
def tango_context():
    """Create a test device context for the SDPSubarray device."""
    device = SDPSubarray
    device_name = 'mid_sdp/elt/subarray_00'
    properties = {'CapabilityTypes': '',
                  'CentralLoggingTarget': '',
                  'ElementLoggingTarget': '',
                  'GroupDefinitions': '',
                  'SkaLevel': '4',
                  'StorageLoggingTarget': 'localhost',
                  'SubID': '',
                  }
    context = DeviceTestContext(device,
                                device_name=device_name,
                                properties=properties)
    context.start()
    yield context
    context.stop()


def test_subarray_has_assign_resources_command(tango_context):
    """."""
    device = tango_context.device
    assert 'AssignResources' in device.get_command_list()
