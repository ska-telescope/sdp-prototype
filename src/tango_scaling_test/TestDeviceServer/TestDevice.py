# -*- coding: utf-8 -*-
"""Tango device used for scaling tests."""
# pylint: disable=invalid-name

import time

from tango.server import Device, device_property, command, attribute
from tango import DevState

from .release import __version__


class TestDevice(Device):
    """."""

    _start_time = time.time()
    version = device_property(dtype=str, default_value=__version__)

    def init_device(self):
        """."""
        Device.init_device(self)
        self.set_state(DevState.STANDBY)

    def always_executed_hook(self):
        """."""

    def delete_device(self):
        """."""

    @attribute(dtype=str)
    def identifier(self):
        """Return the device name."""
        return type(self).__name__

    @attribute(dtype=float)
    def up_time(self):
        """."""
        return time.time() - self._start_time

    # pylint: disable=no-self-use
    @command(dtype_in=str, dtype_out=str)
    def cmd_str_arg(self, value: str) -> str:
        """."""
        time.sleep(0.01)
        return value
