# -*- coding: utf-8 -*-
#
# This file is part of the SDPMaster project
#
#
#
# Distributed under the terms of the GPL license.
# See LICENSE.txt for more info.

""" SDP Master Tango Class

"""

# PyTango imports
import PyTango
from PyTango import DebugIt
from PyTango.server import run
from PyTango.server import Device, DeviceMeta
from PyTango.server import attribute, command
from PyTango.server import device_property
from PyTango import AttrQuality, DispLevel, DevState
from PyTango import AttrWriteType, PipeWriteType
from SKAMaster import SKAMaster
# Additional import
# PROTECTED REGION ID(SDPMaster.additionnal_import) ENABLED START #
# PROTECTED REGION END #    //  SDPMaster.additionnal_import

__all__ = ["SDPMaster", "main"]


class SDPMaster(SKAMaster):
    """
    """
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
        dtype='double',
    )



    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        SKAMaster.init_device(self)
        # PROTECTED REGION ID(SDPMaster.init_device) ENABLED START #
        # PROTECTED REGION END #    //  SDPMaster.init_device

    def always_executed_hook(self):
        # PROTECTED REGION ID(SDPMaster.always_executed_hook) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SDPMaster.always_executed_hook

    def delete_device(self):
        # PROTECTED REGION ID(SDPMaster.delete_device) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SDPMaster.delete_device

    # ------------------
    # Attributes methods
    # ------------------

    def read_OperatingState(self):
        # PROTECTED REGION ID(SDPMaster.OperatingState_read) ENABLED START #
        return 0.0
        # PROTECTED REGION END #    //  SDPMaster.OperatingState_read


    # --------
    # Commands
    # --------

    @command(
    dtype_out=('str',), 
    doc_out="[ name: EltTelState", 
    )
    @DebugIt()
    def GetVersionInfo(self):
        # PROTECTED REGION ID(SDPMaster.GetVersionInfo) ENABLED START #
        return [""]
        # PROTECTED REGION END #    //  SDPMaster.GetVersionInfo

    @command(
    )
    @DebugIt()
    def on(self):
        # PROTECTED REGION ID(SDPMaster.on) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SDPMaster.on

    @command(
    )
    @DebugIt()
    def disable(self):
        # PROTECTED REGION ID(SDPMaster.disable) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SDPMaster.disable

    @command(
    )
    @DebugIt()
    def standby(self):
        # PROTECTED REGION ID(SDPMaster.standby) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SDPMaster.standby

    @command(
    )
    @DebugIt()
    def off(self):
        # PROTECTED REGION ID(SDPMaster.off) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SDPMaster.off

# ----------
# Run server
# ----------


def main(args=None, **kwargs):
    # PROTECTED REGION ID(SDPMaster.main) ENABLED START #
    return run((SDPMaster,), args=args, **kwargs)
    # PROTECTED REGION END #    //  SDPMaster.main

if __name__ == '__main__':
    main()
