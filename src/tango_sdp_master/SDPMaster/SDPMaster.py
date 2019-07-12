# -*- coding: utf-8 -*-

"""Tango SDP Master device module."""
# pylint: disable=invalid-name, import-error, no-name-in-module

# PyTango imports
from PyTango import DebugIt
from PyTango.server import run
from PyTango.server import Device, DeviceMeta
from PyTango.server import attribute, command
from PyTango import DevState
from PyTango import AttrWriteType

from register import is_registered, register_master


__all__ = ["SDPMaster", "main"]


class SDPMaster(Device):
    """SDP Master device class."""

    # pylint: disable=attribute-defined-outside-init

    __metaclass__ = DeviceMeta
    # PROTECTED REGION ID(SDPMaster.class_variable) ENABLED START #
    # PROTECTED REGION END #    //  SDPMaster.class_variable

    # -----------------
    # Device Properties
    # -----------------

    # ----------
    # Attributes
    # ----------

    OperatingState = attribute(
        dtype='DevEnum',
        enum_labels=["INIT", "ON", "DISABLE", "STANDBY", "ALARM", "FAULT",
                     "OFF", "UNKNOWN", ],
        access=AttrWriteType.READ
    )

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        """Initialise the device."""
        Device.init_device(self)
        # PROTECTED REGION ID(SDPMaster.init_device) ENABLED START #
        # Initialise Attributes
        self._operating_state = 0
        self.set_state(DevState.ON)

        # PROTECTED REGION END #    //  SDPMaster.init_device

    def always_executed_hook(self):
        """Run for on each call."""
        # PROTECTED REGION ID(SDPMaster.always_executed_hook) ENABLED START #
        # PROTECTED REGION END #    //  SDPMaster.always_executed_hook

    def delete_device(self):
        """Device destructor."""
        # PROTECTED REGION ID(SDPMaster.delete_device) ENABLED START #
        # PROTECTED REGION END #    //  SDPMaster.delete_device

    # ------------------
    # Attributes methods
    # ------------------

    def read_OperatingState(self):
        """Read the SDP Operating State."""
        # PROTECTED REGION ID(SDPMaster.OperatingState_read) ENABLED START #
        return self._operating_state
        # PROTECTED REGION END #    //  SDPMaster.OperatingState_read

    # --------
    # Commands
    # --------

    @command(
    )
    @DebugIt()
    def on(self):
        """SDP if fully operational and will accept commands."""
        # PROTECTED REGION ID(SDPMaster.on) ENABLED START #
        self._operating_state = 1
        # PROTECTED REGION END #    //  SDPMaster.on

    @command(
    )
    @DebugIt()
    def disable(self):
        """SDP is in a drain state with respect to processing.."""
        # PROTECTED REGION ID(SDPMaster.disable) ENABLED START #
        self._operating_state = 2
        # PROTECTED REGION END #    //  SDPMaster.disable

    @command(
    )
    @DebugIt()
    def standby(self):
        """SDP is in low-power mode."""
        # PROTECTED REGION ID(SDPMaster.standby) ENABLED START #
        self._operating_state = 3
        # PROTECTED REGION END #    //  SDPMaster.standby

    @command(
    )
    @DebugIt()
    def off(self):
        """Only SDP Master device running but rest powered off."""
        # PROTECTED REGION ID(SDPMaster.off) ENABLED START #
        self._operating_state = 6
        # PROTECTED REGION END #    //  SDPMaster.off

# ----------
# Run server
# ----------


def main(args=None, **kwargs):
    """Run server."""
    # PROTECTED REGION ID(SDPMaster.main) ENABLED START #
    server_name = 'SDPMaster/1'
    class_name = 'SDPMaster'
    if not is_registered(server_name):
        print('Registering devices:')
        register_master(server_name, class_name)
    return run((SDPMaster,), args=args, **kwargs)
    # PROTECTED REGION END #    //  SDPMaster.main


if __name__ == '__main__':
    main()
