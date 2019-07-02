# -*- coding: utf-8 -*-
"""Tests for the SDPSubarray device.

docker run --rm -it -v $(pwd):/app/:rw --entrypoint=python skaorca/pytango_ska_dev -m pytest --gherkin-terminal-reporter -s -vv tests/test_SDPSubarray.py
"""


def test_subarray_has_assign_resources_command(tango_context):
    """."""
    device = tango_context.device
    # device = tango.DeviceProxy('mid_sdp/elt/subarray_0')
    assert 'AssignResources' in device.get_command_list()
