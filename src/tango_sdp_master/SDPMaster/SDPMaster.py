# -*- coding: utf-8 -*-
"""Tango SDP Master device module."""
# pylint: disable=invalid-name, import-error, no-name-in-module

import os
import logging
import sys
from enum import IntEnum, unique
import signal

from tango import (AttrWriteType, ConnectionFailed,
                   Database, DbDevInfo, DebugIt, DevState)
from tango.server import Device, DeviceMeta, attribute, command, run

# The version number import is commented out because it seems there is no way
# of making it work in the CI tests (where the device server class is
# imported) and also when the device server is run inside the container.
#
# from SDPMaster.release import VERSION as SERVER_VERSION

LOG = logging.getLogger('ska.sdp.master_ds')


@unique
class HealthState(IntEnum):
    """HealthState enum."""

    OK = 0
    DEGRADED = 1
    FAILED = 2
    UNKNOWN = 3


@unique
class FeatureToggle(IntEnum):
    """Feature Toggles."""

    AUTO_REGISTER = 1  #: Enable / Disable tango db auto-registration


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

    # serverVersion = attribute(
    #     label='Server Version',
    #     dtype=str,
    #     access=AttrWriteType.READ,
    #     doc='The version of the SDP Master device'
    # )

    OperatingState = attribute(
        dtype='DevEnum',
        enum_labels=["INIT", "ON", "DISABLE", "STANDBY", "ALARM", "FAULT",
                     "OFF", "UNKNOWN", ],
        access=AttrWriteType.READ
    )

    healthState = attribute(dtype=HealthState,
                            doc='The health state reported for this device. '
                                'It interprets the current device condition '
                                'and condition of all managed devices to set '
                                'this. Most possibly an aggregate attribute.',
                            access=AttrWriteType.READ)

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
        self._health_state = HealthState.OK
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

    # pylint: disable=R0201
    # def read_serverVersion(self):
    #     """Get the SDPMaster device server version attribute.
    #
    #     :returns: The Device Server version.
    #     """
    #     return SERVER_VERSION

    def read_OperatingState(self):
        """Read the SDP Operating State."""
        # PROTECTED REGION ID(SDPMaster.OperatingState_read) ENABLED START #
        return self._operating_state
        # PROTECTED REGION END #    //  SDPMaster.OperatingState_read

    def read_healthState(self):
        """Read Health State of the device.

        :return: Health State of the device
        """
        return self._health_state

    # --------
    # Commands
    # --------

    @command()
    @DebugIt()
    def on(self):
        """SDP if fully operational and will accept commands."""
        # PROTECTED REGION ID(SDPMaster.on) ENABLED START #
        self._operating_state = 1
        # PROTECTED REGION END #    //  SDPMaster.on

    @command()
    @DebugIt()
    def disable(self):
        """SDP is in a drain state with respect to processing.."""
        # PROTECTED REGION ID(SDPMaster.disable) ENABLED START #
        self._operating_state = 2
        # PROTECTED REGION END #    //  SDPMaster.disable

    @command()
    @DebugIt()
    def standby(self):
        """SDP is in low-power mode."""
        # PROTECTED REGION ID(SDPMaster.standby) ENABLED START #
        self._operating_state = 3
        # PROTECTED REGION END #    //  SDPMaster.standby

    @command()
    @DebugIt()
    def off(self):
        """Only SDP Master device running but rest powered off."""
        # PROTECTED REGION ID(SDPMaster.off) ENABLED START #
        self._operating_state = 6
        # PROTECTED REGION END #    //  SDPMaster.off

    # ---------------
    # Public methods
    # ---------------

    @staticmethod
    def set_feature_toggle_default(feature_name, default):
        """Set the default value of a feature toggle.

        :param feature_name: Name of the feature
        :param default: Default for the feature toggle (if it is not set)

        """
        env_var = SDPMaster._get_feature_toggle_env_var(feature_name)
        if not os.environ.get(env_var):
            LOG.debug('Setting default for toggle: %s = %s', env_var, default)
            os.environ[env_var] = str(int(default))

    @staticmethod
    def is_feature_active(feature_name):
        """Check if feature is active.

        :param feature_name: Name of the feature.
        :returns: True if the feature toggle is enabled.

        """
        env_var = SDPMaster._get_feature_toggle_env_var(feature_name)
        env_var_value = os.environ.get(env_var)
        return env_var_value == '1'

    # -------------------------------------
    # Private methods
    # -------------------------------------

    @staticmethod
    def _get_feature_toggle_env_var(feature_name):
        """Get the env var associated with the feature toggle.

        :param feature_name: Name of the feature.
        :returns: environment variable name for feature toggle.

        """
        if isinstance(feature_name, FeatureToggle):
            feature_name = feature_name.name
        env_var = str('toggle_' + feature_name).upper()
        allowed = ['TOGGLE_' + toggle.name for toggle in FeatureToggle]
        if env_var not in allowed:
            message = 'Unknown feature toggle: {} (allowed: {})'\
                .format(env_var, allowed)
            LOG.error(message)
            raise ValueError(message)
        return env_var


def delete_device_server(instance_name: str = "*"):
    """Delete (unregister) SDPMaster device server instance(s).

    :param instance_name: Optional, name of the device server instance to
                          remove. If not specified all service instances will
                          be removed.
    """
    try:
        tango_db = Database()
        class_name = 'SDPMaster'
        server_name = '{}/{}'.format(class_name, instance_name)
        for server_name in list(tango_db.get_server_list(server_name)):
            LOG.info('Removing device server: %s', server_name)
            tango_db.delete_server(server_name)
    except ConnectionFailed:
        pass


def register(instance_name: str, device_name: str):
    """Register device with a SDP Master device server instance.

    If the device is already registered, do nothing.

    :param instance_name: Instance name SDPMaster device server
    :param device_name: Master device name to register
    """
    try:
        tango_db = Database()
        class_name = 'SDPMaster'
        server_name = '{}/{}'.format(class_name, instance_name)
        devices = list(tango_db.get_device_name(server_name, class_name))
        device_info = DbDevInfo()
        # pylint: disable=protected-access
        device_info._class = class_name
        device_info.server = server_name
        device_info.name = device_name
        if device_name in devices:
            LOG.debug("Device '%s' already registered", device_name)
            return
        LOG.info('Registering device: %s (server: %s, class: %s)',
                 device_info.name, server_name, class_name)
        tango_db.add_device(device_info)
    except ConnectionFailed:
        pass


def init_logger(level: str = 'DEBUG', name: str = 'ska.sdp'):
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


# ----------
# Run server
# ----------


def main(args=None, **kwargs):
    """Run server."""
    # PROTECTED REGION ID(SDPMaster.main) ENABLED START #
    # Set default values for feature toggles.
    SDPMaster.set_feature_toggle_default(FeatureToggle.AUTO_REGISTER, True)

    log_level = 'INFO'
    if len(sys.argv) > 2 and '-v' in sys.argv[2]:
        log_level = 'DEBUG'
    init_logger(log_level)

    # If the feature is enabled, attempt to auto-register the device
    # with the tango db.
    if SDPMaster.is_feature_active(FeatureToggle.AUTO_REGISTER):
        if len(sys.argv) > 1:
            # delete_device_server("*")
            register(sys.argv[1], 'mid_sdp/elt/master')

    return run((SDPMaster,), args=args, **kwargs)
    # PROTECTED REGION END #    //  SDPMaster.main


def terminate(_sig, _frame):
    """Terminate the program."""
    LOG.info("Asked to terminate")
    exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, terminate)
    main()
