# -*- coding: utf-8 -*-
"""SDPSubarray Device"""

from tango import DebugIt
from tango.server import run
from tango.server import DeviceMeta
from tango.server import command
from skabase.SKASubarray import SKASubarray


__all__ = ["SDPSubarray", "main"]


class SDPSubarray(SKASubarray):
    """SDP Subarray device class."""

    __metaclass__ = DeviceMeta

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

    def always_executed_hook(self):
        pass

    def delete_device(self):
        pass

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
        doc_out="A list of Resources added to the subarray."
    )
    @DebugIt()
    def AssignResources(self, argin):
        print("Assigning Resources")
        print(':', argin)
        # TODO(BMo) state changes ?

    @command(
        dtype_in=('str',),
        doc_in="List of resources to remove from the subarray.",
        dtype_out=('str',),
        doc_out="List of resources removed from the subarray."
    )
    @DebugIt()
    def ReleaseResources(self, argin):
        print("Releasing Resources")
        # TODO(BMo) state changes ?


def main(args=None, **kwargs):
    """Run server."""
    return run((SDPSubarray,), args=args, **kwargs)


if __name__ == '__main__':
    main()
