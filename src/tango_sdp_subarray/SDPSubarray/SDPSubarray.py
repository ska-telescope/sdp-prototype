# -*- coding: utf-8 -*-
"""Tango SDPSubarray device module."""
# pylint: disable=invalid-name

import sys
import json
from enum import IntEnum
from inspect import currentframe, getframeinfo
from os.path import dirname, join
import logging

from ska_sdp_config import config, entity, backend

from jsonschema import validate
from tango import AttrWriteType, DebugIt, DevState, Except
from tango.server import Device, DeviceMeta, attribute, command, run
from tango import Database, DbDevInfo, ConnectionFailed

# from skabase.SKASubarray import SKASubarray


LOG = logging.getLogger('ska.sdp.subarray_ds')


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

    healthState = attribute(dtype=HealthState,
                            doc='The health state reported for this device. '
                                'It interprets the current device condition '
                                'and condition of all managed devices to set '
                                'this. Most possibly an aggregate attribute.',
                            access=AttrWriteType.READ)

    receiveAddresses = attribute(dtype=str, access=AttrWriteType.READ)

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        """Initialise the device."""
        # SKASubarray.init_device(self)
        Device.init_device(self)
        self.set_state(DevState.OFF)
        self._obs_state = ObsState.IDLE
        self._admin_mode = AdminMode.OFFLINE
        self._health_state = HealthState.OK

    def always_executed_hook(self):
        """Run for on each call."""

    def delete_device(self):
        """Device destructor."""

    # ------------------
    # Attributes methods
    # ------------------

    def write_obsState(self, obs_state):
        """Set the obsState attribute.

        :param obs_state: An observation state enum value.
        """
        self._obs_state = obs_state

    def read_obsState(self):
        """Get the obsState attribute.

        :returns: The current obsState attribute value.
        """
        return self._obs_state

    def write_adminMode(self, admin_mode):
        """Set the adminMode attribute.

        :param admin_mode: An admin mode enum value.
        """
        self._admin_mode = admin_mode

    def read_adminMode(self):
        """Get the adminMode attribute.

        :return: The current adminMode attribute value.
        """
        return self._admin_mode

    def read_receiveAddresses(self):
        """Get the list of receive addresses encoded as a JSON string.

        More details are provided on SKA confluence at the address:
        http://bit.ly/2Gad55Q

        :return: List of receive addresses
        """
        return self._receive_addresses

    def read_healthState(self):
        """Read Health State of the device.

        :return: Health State of the device
        """
        return self._health_state

    # --------
    # Commands
    # --------

    @command(dtype_in=str)
    @DebugIt()
    def AssignResources(self, config=''):
        """Assign Resources assigned to the subarray device.

        This is currently a noop for SDP!

        Following the description of the SKA subarray device model,
        resources can only be assigned to the subarray device when the
        obsState attribute is IDLE. Once resources are assigned to the
        subarray device, the device state transitions to ON.

        :param config: Resource specification (currently ignored)
        """
        # pylint: disable=unused-argument
        if self._obs_state != ObsState.IDLE:
            frame_info = getframeinfo(currentframe())
            Except.throw_exception('Command: AssignReources failed',
                                   'AssignResources requires obsState == IDLE',
                                   '{}:{}'.format(frame_info.filename,
                                                  frame_info.lineno))
        self.set_state(DevState.ON)

    @command(dtype_in=str)
    @DebugIt()
    def ReleaseResources(self, config=''):
        """Release resources assigned to the subarray device.

        This is currently a noop for SDP!

        Following the description of the SKA subarray device model,
        when all resources are released the device state should transition to
        OFF. Releasing resources is only allowed when the obsState is IDLE.

        :param config: Resource specification (currently ignored).
        """
        # pylint: disable=unused-argument
        if self._obs_state != ObsState.IDLE:
            frame_info = getframeinfo(currentframe())
            Except.throw_exception('Command: ReleaseResources failed',
                                   'ReleaseResources requires '
                                   'obsState == IDLE',
                                   '{}:{}'.format(frame_info.filename,
                                                  frame_info.lineno))

        self.set_state(DevState.OFF)

    @command(dtype_in=str)
    @DebugIt()
    def Configure(self, pb_config, schema_path=None):
        """Configure the device to execute a real-time Processing Block (PB).

        Provides PB configuration and parameters needed to execute the first
        scan in the form of a JSON string.

        :param pb_config: JSON string wth Processing Block configuration.
        :param schema_path: Path to the PB config schema (optional).
        """
        # pylint: disable=unused-argument
        self._obs_state = ObsState.CONFIGURING
        # time.sleep(1)

        # Validate the SBI config schema
        if schema_path is None:
            schema_path = join(dirname(__file__), 'schema',
                               'configure_pb.json')

        with open(schema_path, 'r') as file:
            schema = json.loads(file.read())

        pb_config = json.loads(pb_config)
        validate(pb_config, schema)

        for txn in config.Config().txn():
            confdata = pb_config['configure']
            workflow = confdata['workflow']
            pb_id = txn.new_processing_block_id(confdata['id'])
            pb = entity.ProcessingBlock(pb_id, None, workflow, confdata['parameters'])
            txn.create_processing_block(pb)

        self._obs_state = ObsState.READY

    @command(dtype_in=str)
    @DebugIt()
    def ConfigureScan(self, scan_config, schema_path=None):
        """Configure the subarray device to execute a scan.

        This allows scan specific, late-binding information to be provided
        to the configured PB workflow.

        :param scan_config: JSON Scan configuration.
        :param schema_path: Path to the Scan config schema (optional).
        """
        # pylint: disable=unused-argument
        self._obs_state = ObsState.CONFIGURING
        # # time.sleep(0.5)

        # # Validate the SBI config schema
        if schema_path is None:
            schema_path = join(dirname(__file__), 'schema',
                               'configure_scan.json')
        with open(schema_path, 'r') as file:
            schema = json.loads(file.read())
        pb_config = json.loads(scan_config)
        validate(pb_config, schema)

        for txn in config.Config().txn():
            workflow = pb_config['workflow']
            pb_id = txn.new_processing_block_id(workflow['id'])
            pb = entity.ProcessingBlock(pb_id, None, workflow, pb_config['parameters'])
            txn.create_processing_block(pb)

        self._obs_state = ObsState.READY

    @command
    @DebugIt()
    def StartScan(self):
        """Command issued when a scan is started."""
        self._obs_state = ObsState.SCANNING

    @command
    @DebugIt()
    def EndScan(self):
        """Command issued when the scan is ended."""
        self._obs_state = ObsState.READY

    @command
    @DebugIt()
    def EndSB(self):
        """Command issued to end the scheduling block."""
        self._obs_state = ObsState.IDLE

    def _scan_complete(self):
        """Update the obsState to READY when a scan is complete.

        Internal state transition.
        """
        self._obs_state = ObsState.READY


def delete_device_server(instance_name="*"):
    """Delete (unregister) SDPSubarray device server instance(s).

    :param instance_name: Optional, name of the device server instance to
                          remove. If not specified all service instances will
                          be removed.
    """
    try:
        tango_db = Database()
        class_name = 'SDPSubarray'
        server_name = '{}/{}'.format(class_name, instance_name)
        for server_name in list(tango_db.get_server_list(server_name)):
            LOG.info('Removing device server: %s', server_name)
            tango_db.delete_server(server_name)
    except ConnectionFailed:
        pass


def register(instance_name, *device_names):
    """Register device with a SDPSubarray device server instance.

    If the device is already registered, do nothing.

    :param instance_name: Instance name SDPSubarray device server
    :param device_names: Subarray device names to register
    """
    try:
        tango_db = Database()
        class_name = 'SDPSubarray'
        server_name = '{}/{}'.format(class_name, instance_name)
        devices = list(tango_db.get_device_name(server_name, class_name))
        device_info = DbDevInfo()
        # pylint: disable=protected-access
        device_info._class = class_name
        device_info.server = server_name
        for device_name in device_names:
            device_info.name = device_name
            if device_name in devices:
                LOG.debug("Device '%s' already registered", device_name)
                continue
            LOG.info('Registering device: %s (server: %s, class: %s)',
                     device_info.name, server_name, class_name)
            tango_db.add_device(device_info)
    except ConnectionFailed:
        pass


def init_logger(level='DEBUG', name='ska.sdp'):
    """Initialise stdout logger for the ska.sdp logger.

    :param level: Logging level, default: 'DEBUG'
    :param name: Logger name to initialise. default: 'ska.sdp'.
    """
    log = logging.getLogger(name)
    log.propagate = False
    # make sure there are no duplicate handlers.
    for handler in log.handlers:
        log.removeHandler(handler)
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-6s | %(message)s')
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(level)


def main(args=None, **kwargs):
    """Run server."""
    log_level = 'INFO'
    if len(sys.argv) > 2 and '-v' in sys.argv[2]:
        log_level = 'DEBUG'
    init_logger(log_level)
    if len(sys.argv) > 1:
        # delete_device_server("*")
        devices = ['mid_sdp/elt/subarray_{:d}'.format(i+1) for i in range(1)]
        register(sys.argv[1], *devices)
    return run((SDPSubarray,), args=args, **kwargs)


if __name__ == '__main__':
    main()
