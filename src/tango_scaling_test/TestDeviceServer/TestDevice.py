# -*- coding: utf-8 -*-
"""Tango device used for scaling tests."""
from tango.server import Device, device_property, command, attribute
from tango import DevState

from release import __version__


class TestDevice(Device):
    """."""
