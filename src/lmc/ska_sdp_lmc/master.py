"""SDP Master Tango device module."""

import sys
import signal
import logging

from tango import AttrWriteType, DevState, LogLevel
from tango.server import attribute, command, run

from ska_sdp_logging import tango_logging

from .attributes import HealthState
from .base import SDPDevice
from .util import terminate

LOG = logging.getLogger('ska_sdp_lmc')


class SDPMaster(SDPDevice):
    """SDP Master device class."""

    # pylint: disable=invalid-name
    # pylint: disable=attribute-defined-outside-init

    # ----------
    # Attributes
    # ----------

    healthState = attribute(
        label='Health state',
        dtype=HealthState,
        access=AttrWriteType.READ,
        doc='The device health state.'
    )

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        """Initialise the device."""
        super().init_device()
        self.set_state(DevState.INIT)
        LOG.info('Initialising SDP Master: %s', self.get_name())
        # Initialise attributes
        self._health_state = HealthState.OK
        self.set_state(DevState.STANDBY)
        LOG.info('SDP Master initialised: %s', self.get_name())

    def always_executed_hook(self):
        """Run for on each call."""

    def delete_device(self):
        """Device destructor."""

    # -----------------
    # Attribute methods
    # -----------------

    def read_healthState(self):
        """Read Health State of the device.

        :return: Health State of the device
        """
        return self._health_state

    # --------
    # Commands
    # --------

    def is_On_allowed(self):
        """Check if the On command is allowed."""
        self._command_allowed_state(
            'On', [DevState.OFF, DevState.STANDBY, DevState.DISABLE]
        )
        return True

    @command()
    def On(self):
        """Turn the SDP on."""
        LOG.info('-------------------------------------------------------')
        LOG.info('On (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')
        self.set_state(DevState.ON)
        LOG.info('-------------------------------------------------------')
        LOG.info('On Successful!')
        LOG.info('-------------------------------------------------------')

    def is_Disable_allowed(self):
        """Check if the Disable command is allowed."""
        self._command_allowed_state(
            'Disable', [DevState.OFF, DevState.STANDBY, DevState.ON]
        )
        return True

    @command()
    def Disable(self):
        """Set the SDP to disable."""
        LOG.info('-------------------------------------------------------')
        LOG.info('Disable (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')
        self.set_state(DevState.DISABLE)
        LOG.info('-------------------------------------------------------')
        LOG.info('Disable Successful!')
        LOG.info('-------------------------------------------------------')

    def is_Standby_allowed(self):
        """Check if the Standby command is allowed."""
        self._command_allowed_state(
            'Standby', [DevState.OFF, DevState.DISABLE, DevState.ON]
        )
        return True

    @command()
    def Standby(self):
        """Set the SDP to standby."""
        LOG.info('-------------------------------------------------------')
        LOG.info('Standby (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')
        self.set_state(DevState.STANDBY)
        LOG.info('-------------------------------------------------------')
        LOG.info('Standby Successful!')
        LOG.info('-------------------------------------------------------')

    def is_Off_allowed(self):
        """Check if the Off command is allowed."""
        self._command_allowed_state(
            'Off', [DevState.STANDBY, DevState.DISABLE, DevState.ON]
        )
        return True

    @command()
    def Off(self):
        """Turn the SDP off."""
        LOG.info('-------------------------------------------------------')
        LOG.info('Off (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')
        self.set_state(DevState.OFF)
        LOG.info('-------------------------------------------------------')
        LOG.info('Off Successful!')
        LOG.info('-------------------------------------------------------')


def main(args=None, **kwargs):
    """Run server."""
    # Initialise logging
    log_level = LogLevel.LOG_INFO
    if len(sys.argv) > 2 and '-v' in sys.argv[2]:
        log_level = LogLevel.LOG_DEBUG
    tango_logging.init(name=LOG.name, device_name='SDPMaster',
                       level=log_level)

    # Register SIGTERM handler
    signal.signal(signal.SIGTERM, terminate)

    return run((SDPMaster,), args=args, **kwargs)
