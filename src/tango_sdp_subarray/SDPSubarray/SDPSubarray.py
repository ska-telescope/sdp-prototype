# -*- coding: utf-8 -*-
"""SDP Subarray device"""

from enum import IntEnum
import time
from inspect import currentframe, getframeinfo

import tango
from tango import DebugIt, DevState, AttrWriteType
from tango import Except
from tango.server import run, Device
from tango.server import DeviceMeta
from tango.server import command, attribute
from skabase.SKASubarray import SKASubarray

__all__ = ["SDPSubarray", "main", "AdminMode", "HealthState", "ObsState"]


# https://pytango.readthedocs.io/en/stable/data_types.html#devenum-pythonic-usage
class AdminMode(IntEnum):
    OFFLINE = 0
    ONLINE = 1
    MAINTENANCE = 2
    NOT_FITTED = 3
    RESERVED = 4


class HealthState(IntEnum):
    OK = 0
    DEGRADED = 1
    FAILED = 2
    UNKNOWN = 3


class ObsState(IntEnum):
    IDLE = 0
    CONFIGURING = 1
    READY = 2
    SCANNING = 3
    PAUSED = 4
    ABORTED = 5
    FAULT = 6


# class SDPSubarray(SKASubarray):
class SDPSubarray(Device):
    """SDP Subarray device class."""

    __metaclass__ = DeviceMeta

    # -----------------
    # Device Properties
    # -----------------

    # ----------
    # Attributes
    # ----------

    obsState = attribute(dtype=ObsState, access=AttrWriteType.READ_WRITE)

    adminMode = attribute(dtype=AdminMode, access=AttrWriteType.READ_WRITE)

    receiveAddresses = attribute(dtype=str, access=AttrWriteType.READ)

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        """Initialises the device."""
        # SKASubarray.init_device(self)
        Device.init_device(self)
        self.set_state(DevState.OFF)
        self.obs_state = ObsState.IDLE
        self.admin_mode = AdminMode.OFFLINE

    def always_executed_hook(self):
        pass

    def delete_device(self):
        pass

    # ------------------
    # Attributes methods
    # ------------------

    def write_obsState(self, obs_state):
        """Set obsState."""
        self.obs_state = obs_state

    def read_obsState(self):
        """Get obsState."""
        return self.obs_state

    def write_adminMode(self, admin_mode):
        """Set adminMode."""
        self.admin_mode = admin_mode

    def read_adminMode(self):
        """Get adminMode"""
        return self.admin_mode

    # --------
    # Commands
    # --------

    @command(dtype_in=str)
    @DebugIt()
    def AssignResources(self, config):
        """Assign Resources to the subarray device."""
        if self.obs_state != ObsState.IDLE:
            frame_info = getframeinfo(currentframe())
            Except.throw_exception('Command: AssignReources failed',
                                   'AssignResources requires obsState == IDLE',
                                   '{}:{}'.format(frame_info.filename,
                                                  frame_info.lineno))
        self.set_state(DevState.ON)

    @command(dtype_in=str)
    @DebugIt()
    def ReleaseResources(self, config):
        """Release resources from the subarray device."""
        self.set_state(DevState.OFF)

    @command(dtype_in=str)
    @DebugIt()
    def Configure(self, pb_config):
        """Configures the subarray device to execute a real-time PB.

         Provides PB configuration and parameters needed to execute the first
         scan.

         Args:
             config (str): PB configuration (JSON)

         """
        self.obs_state = ObsState.CONFIGURING
        # time.sleep(1)
        self.obs_state = ObsState.READY

    @command(dtype_in=str)
    @DebugIt()
    def ConfigureScan(self, scan_config):
        """Configures the subarray device to execute a scan.

        This allows scan specific, late-binding information to be provided
        to the configured PB workflow.

        """
        self.obs_state = ObsState.CONFIGURING
        # time.sleep(0.5)
        self.obs_state = ObsState.READY

    @command
    @DebugIt()
    def Scan(self):
        """Command issued when a scan is started."""
        self.obs_state = ObsState.SCANNING

    @command
    @DebugIt()
    def EndScan(self):
        """Command issued when the scan is ended."""
        self.obs_state = ObsState.READY

    @command
    @DebugIt()
    def EndSB(self):
        """Command issued to end the scheduling block."""
        self.obs_state = ObsState.IDLE

    def _scan_complete(self):
        """Updates the obsState to READY when a scan is complete.

        Internal state transition.
        """
        self.obs_state = ObsState.READY


def main(args=None, **kwargs):
    """Run server."""
    return run((SDPSubarray,), args=args, **kwargs)


if __name__ == '__main__':
    main()
