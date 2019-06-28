# -*- coding: utf-8 -*-
#
# This file is part of the SDPSubarray project
#
#
#
# Distributed under the terms of the none license.
# See LICENSE.txt for more info.

""" SDPSubarray

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
from SKASubarray import SKASubarray
# Additional import
# PROTECTED REGION ID(SDPSubarray.additionnal_import) ENABLED START #
# PROTECTED REGION END #    //  SDPSubarray.additionnal_import

__all__ = ["SDPSubarray", "main"]


class SDPSubarray(SKASubarray):
    """
    """
    __metaclass__ = DeviceMeta
    # PROTECTED REGION ID(SDPSubarray.class_variable) ENABLED START #
    # PROTECTED REGION END #    //  SDPSubarray.class_variable

    # -----------------
    # Device Properties
    # -----------------








    # ----------
    # Attributes
    # ----------


















    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        SKASubarray.init_device(self)
        # PROTECTED REGION ID(SDPSubarray.init_device) ENABLED START #
        # PROTECTED REGION END #    //  SDPSubarray.init_device

    def always_executed_hook(self):
        # PROTECTED REGION ID(SDPSubarray.always_executed_hook) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SDPSubarray.always_executed_hook

    def delete_device(self):
        # PROTECTED REGION ID(SDPSubarray.delete_device) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SDPSubarray.delete_device

    # ------------------
    # Attributes methods
    # ------------------


    # --------
    # Commands
    # --------

    @command(
    dtype_in=('str',), 
    doc_in="List of Resources to add to subarray.", 
    dtype_out=('str',), 
    doc_out="A list of Resources added to the subarray.", 
    )
    @DebugIt()
    def AssignResources(self, argin):
        # PROTECTED REGION ID(SDPSubarray.AssignResources) ENABLED START #
        print("Assigning Resources")
 
        print(':', argin)
 
        ## TODO(BMo) state changes ?

        # PROTECTED REGION END #    //  SDPSubarray.AssignResources

    @command(
    dtype_in=('str',), 
    doc_in="List of resources to remove from the subarray.", 
    dtype_out=('str',), 
    doc_out="List of resources removed from the subarray.", 
    )
    @DebugIt()
    def ReleaseResources(self, argin):
        # PROTECTED REGION ID(SDPSubarray.ReleaseResources) ENABLED START #
        print("Releasing Reources")
        ## TODO(BMo) state changes ?

        # PROTECTED REGION END #    //  SDPSubarray.ReleaseResources

# ----------
# Run server
# ----------


def main(args=None, **kwargs):
    # PROTECTED REGION ID(SDPSubarray.main) ENABLED START #
    return run((SDPSubarray,), args=args, **kwargs)
    # PROTECTED REGION END #    //  SDPSubarray.main

if __name__ == '__main__':
    main()
