# -*- coding: utf-8 -*-
"""Tango SDPSubarray device module."""

# pylint: disable=invalid-name

from os.path import dirname, join

from enum import IntEnum
from inspect import currentframe, getframeinfo

import json
from jsonschema import validate

from tango import AttrWriteType, DebugIt, DevState, Except
from tango.server import Device, DeviceMeta, attribute, command, run
from .register import registered_subarray_devices, register_subarray_devices
# from skabase.SKASubarray import SKASubarray


# https://pytango.readthedocs.io/en/stable/data_types.html#devenum-pythonic-usage
class AdminMode(IntEnum):
    """AdminMode enum."""

    OFFLINE = 0
    ONLINE = 1
    MAINTENANCE = 2
    NOT_FITTED = 3
    RESERVED = 4


class HealthState(IntEnum):
    """HealthState enum."""

    OK = 0
    DEGRADED = 1
    FAILED = 2
    UNKNOWN = 3


class ObsState(IntEnum):
    """ObsState enum."""

    IDLE = 0  #: Idle state
    CONFIGURING = 1  #: Configuring state
    READY = 2  #: Ready state
    SCANNING = 3  #: Scanning state
    PAUSED = 4  #: Paused state
    ABORTED = 5  #: Aborted state
    FAULT = 6  #: Fault state


# class SDPSubarray(SKASubarray):
class SDPSubarray(Device):
    """SDP Subarray device class.

    .. note::
        This should eventually inherit from SKASubarray but these need
        some work before doing so would add any value to this device.
    """

    # pylint: disable=attribute-defined-outside-init

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
        """Initialise the device."""
        # SKASubarray.init_device(self)
        Device.init_device(self)
        self.set_state(DevState.OFF)
        self.obs_state = ObsState.IDLE
        self.admin_mode = AdminMode.OFFLINE

    def always_executed_hook(self):
        """Run for on each call."""

    def delete_device(self):
        """Device destructor."""

    # ------------------
    # Attributes methods
    # ------------------

    def write_obsState(self, obs_state: ObsState):
        """Set the obsState attribute.

        :param obs_state: An observation state enum value.
        """
        self.obs_state = obs_state

    def read_obsState(self) -> ObsState:
        """Get the obsState attribute.

        :returns: The current obsState attribute value.
        """
        return self.obs_state

    def write_adminMode(self, admin_mode: AdminMode):
        """Set the adminMode attribute.

        :param admin_mode: An admin mode enum value.
        """
        self.admin_mode = admin_mode

    def read_adminMode(self) -> AdminMode:
        """Get the adminMode attribute.

        :return: The current adminMode attribute value.
        """
        return self.admin_mode

    def read_receiveAddresses(self) -> str:
        """Get the list of receive addresses encoded as a JSON string.

        More details are provided on SKA confluence at the address:
        http://bit.ly/2Gad55Q

        :return: List of receive addresses

        :Example:

        .. code-block:: javascript

            {
                "<phase_bin>": {
                    "<channel_id>": ["<ip>", <port>],
                    "<channel_id>": ["<ip>", <port>],
                    ...
                }
            }

        """
        return self.receive_addresses

    # --------
    # Commands
    # --------

    @command(dtype_in=str)
    @DebugIt()
    def AssignResources(self, config: str = ''):
        """Assign Resources assigned to the subarray device.

        This is currently a noop for SDP!

        Following the description of the SKA subarray device model,
        resources can only be assigned to the subarray device when the
        obsState attribute is IDLE. Once resources are assigned to the
        subarray device, the device state transitions to ON.

        :param config: Resource specification (currently ignored)
        """
        # pylint: disable=unused-argument
        if self.obs_state != ObsState.IDLE:
            frame_info = getframeinfo(currentframe())
            Except.throw_exception('Command: AssignReources failed',
                                   'AssignResources requires obsState == IDLE',
                                   '{}:{}'.format(frame_info.filename,
                                                  frame_info.lineno))
        self.set_state(DevState.ON)

    @command(dtype_in=str)
    @DebugIt()
    def ReleaseResources(self, config: str = ''):
        """Release resources assigned to the subarray device.

        This is currently a noop for SDP!

        Following the description of the SKA subarray device model,
        when all resources are released the device state should transition to
        OFF. Releasing resources is only allowed when the obsState is IDLE.

        :param config: Resource specification (currently ignored).
        """
        # pylint: disable=unused-argument
        if self.obs_state != ObsState.IDLE:
            frame_info = getframeinfo(currentframe())
            Except.throw_exception('Command: ReleaseResources failed',
                                   'ReleaseResources requires '
                                   'obsState == IDLE',
                                   '{}:{}'.format(frame_info.filename,
                                                  frame_info.lineno))

        self.set_state(DevState.OFF)

    @command(dtype_in=str)
    @DebugIt()
    def Configure(self, pb_config: str, schema_path: str = None):
        """Configure the device to execute a real-time Processing Block (PB).

        Provides PB configuration and parameters needed to execute the first
        scan in the form of a JSON string.

        :param pb_config: JSON Processing Block configuration.
        :param schema_path: Path to the PB config schema (optional).
        """
        # pylint: disable=unused-argument
        self.obs_state = ObsState.CONFIGURING
        # time.sleep(1)

        # Validate the SBI config schema
        if schema_path is None:
            schema_path = join(dirname(__file__), 'schema',
                               'configure_pb.json')

        with open(schema_path, 'r') as file:
            schema = json.loads(file.read())

        pb_config = json.loads(pb_config)
        validate(pb_config, schema)
        self.obs_state = ObsState.READY

    @command(dtype_in=str)
    @DebugIt()
    def ConfigureScan(self, scan_config: str, schema_path: str = None):
        """Configure the subarray device to execute a scan.

        This allows scan specific, late-binding information to be provided
        to the configured PB workflow.

        :param scan_config: JSON Scan configuration.
        :param schema_path: Path to the Scan config schema (optional).
        """
        # pylint: disable=unused-argument
        self.obs_state = ObsState.CONFIGURING
        # # time.sleep(0.5)

        # # Validate the SBI config schema
        if schema_path is None:
            schema_path = join(dirname(__file__), 'schema',
                               'configure_scan.json')
        with open(schema_path, 'r') as file:
            schema = json.loads(file.read())
        pb_config = json.loads(scan_config)
        validate(pb_config, schema)
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
        """Update the obsState to READY when a scan is complete.

        Internal state transition.
        """
        self.obs_state = ObsState.READY


def main(args=None, **kwargs):
    """Run server."""
    server_name = 'SDPSubarray/1'
    class_name = 'SDPSubarray'
    devices = registered_subarray_devices(server_name, class_name)
    if not len(devices):
        print('Registering devices:')
        register_subarray_devices(server_name, class_name, 16)
    return run((SDPSubarray,), args=args, **kwargs)


if __name__ == '__main__':
    main()
