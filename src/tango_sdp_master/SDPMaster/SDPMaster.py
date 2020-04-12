# -*- coding: utf-8 -*-
"""Tango SDP Master device module."""
# pylint: disable=invalid-name
# pylint: disable=import-error
# pylint: disable=no-name-in-module
# pylint: disable=wrong-import-position

import os
import sys
import signal
import logging
from enum import IntEnum, unique

from tango import (AttrWriteType, ConnectionFailed, Database, DbDevInfo,
                   DebugIt)
from tango.server import attribute, command, run

from ska.base import SKAMaster
from ska.base.control_model import HealthState

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from release import VERSION

LOG = logging.getLogger()


@unique
class OperatingState(IntEnum):
    """Operating state."""

    INIT = 0
    ON = 1
    DISABLE = 2
    STANDBY = 3
    ALARM = 4
    FAULT = 5
    OFF = 6
    UNKNOWN = 7


@unique
class FeatureToggle(IntEnum):
    """Feature Toggles."""

    AUTO_REGISTER = 1  #: Enable / Disable tango db auto-registration


class SDPMaster(SKAMaster):
    """SDP Master device class."""

    # pylint: disable=attribute-defined-outside-init

    # PROTECTED REGION ID(SDPMaster.class_variable) ENABLED START #
    # PROTECTED REGION END #    //  SDPMaster.class_variable

    # -----------------
    # Device Properties
    # -----------------

    # ----------
    # Attributes
    # ----------

    operatingState = attribute(
        label='Operating state',
        dtype=OperatingState,
        access=AttrWriteType.READ,
        doc='Operating state'
    )

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        """Initialise the device."""
        SKAMaster.init_device(self)
        # PROTECTED REGION ID(SDPMaster.init_device) ENABLED START #
        self._operating_state = OperatingState.INIT
        self.logger.info('Starting initialising SDPMaster: %s',
                         self.get_name())

        # Initialise Attributes
        self._version_id = VERSION
        self._health_state = HealthState.OK

        self.logger.info('Finished initialising SDPMaster: %s',
                         self.get_name())
        self._operating_state = OperatingState.ON
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

    def read_operatingState(self):
        """Read the SDP Operating State."""
        # PROTECTED REGION ID(SDPMaster.OperatingState_read) ENABLED START #
        return self._operating_state
        # PROTECTED REGION END #    //  SDPMaster.OperatingState_read

    # --------
    # Commands
    # --------

    @command()
    @DebugIt()
    def On(self):
        """SDP if fully operational and will accept commands."""
        # PROTECTED REGION ID(SDPMaster.on) ENABLED START #
        self._operating_state = OperatingState.ON
        # PROTECTED REGION END #    //  SDPMaster.on

    @command()
    @DebugIt()
    def Disable(self):
        """SDP is in a drain state with respect to processing.."""
        # PROTECTED REGION ID(SDPMaster.disable) ENABLED START #
        self._operating_state = OperatingState.DISABLE
        # PROTECTED REGION END #    //  SDPMaster.disable

    @command()
    @DebugIt()
    def Standby(self):
        """SDP is in low-power mode."""
        # PROTECTED REGION ID(SDPMaster.standby) ENABLED START #
        self._operating_state = OperatingState.STANDBY
        # PROTECTED REGION END #    //  SDPMaster.standby

    @command()
    @DebugIt()
    def Off(self):
        """Only SDP Master device running but rest powered off."""
        # PROTECTED REGION ID(SDPMaster.off) ENABLED START #
        self._operating_state = OperatingState.OFF
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


def main(args=None, **kwargs):
    """Run server."""
    # Set default values for feature toggles.
    SDPMaster.set_feature_toggle_default(FeatureToggle.AUTO_REGISTER, True)

    # If the feature is enabled, attempt to auto-register the device
    # with the tango db.
    if SDPMaster.is_feature_active(FeatureToggle.AUTO_REGISTER):
        if len(sys.argv) > 1:
            # delete_device_server("*")
            register(sys.argv[1], 'mid_sdp/elt/master')

    return run((SDPMaster,), args=args, **kwargs)


def terminate(_sig, _frame):
    """Terminate the program."""
    LOG.info("Asked to terminate")
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, terminate)
    main()
