"""SDP Tango device base class module."""

import enum
import logging

from tango import AttrWriteType, ErrSeverity, Except
from tango.server import Device, attribute

from . import release

LOG = logging.getLogger('ska_sdp_lmc')


class SDPDevice(Device):
    """SDP Tango device base class."""

    # pylint: disable=attribute-defined-outside-init

    # ----------
    # Attributes
    # ----------

    version = attribute(
        label='Version',
        dtype=str,
        access=AttrWriteType.READ,
        doc='The version of the device'
    )

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        """Initialise the device."""
        super().init_device()
        self._version = release.VERSION

    # -----------------
    # Attribute methods
    # -----------------

    def read_version(self):
        """Return server version."""
        return self._version

    # ---------------
    # Private methods
    # ---------------

    @staticmethod
    def _raise_exception(reason, desc, origin, severity=ErrSeverity.ERR):
        """Raise a Tango DevFailed exception.

        :param reason: Reason for the error.
        :param desc: Error description.
        :param origin: Error origin.

        """
        LOG.error('Raising DevFailed exception...')
        LOG.error('Reason: %s', reason)
        LOG.error('Description: %s', desc)
        LOG.error('Origin: %s', origin)
        LOG.error('Severity: %s', severity)
        Except.throw_exception(reason, desc, origin, severity)

    def _raise_command_not_allowed(self, desc, origin):
        """Raise a command-not-allowed exception.

        :param desc: Error description.
        :param origin: Error origin.

        """
        self._raise_exception('API_CommandNotAllowed', desc, origin)

    def _raise_command_failed(self, desc, origin):
        """Raise a command-failed exception.

        :param desc: Error description.
        :param origin: Error origin.

        """
        self._raise_exception('API_CommandFailed', desc, origin)

    def _command_allowed(self, commname, attrname, value, allowed):
        """Check command is allowed when an attribute has its current value.

        If the command is not allowed, it raises a Tango API_CommandNotAllowed
        exception. This generic method is used by other methods to check
        specific attributes.

        :param commname: name of the command
        :param attrname: name of the attribute
        :param value: current attribute value
        :param allowed: list of allowed attribute values

        """
        if value not in allowed:
            if isinstance(value, enum.IntEnum):
                # Get name from IntEnum (otherwise it would be rendered as its
                # integer value in the message)
                value_message = value.name
            else:
                value_message = value
            message = f'Command {commname} not allowed when {attrname} is ' \
                      f'{value_message}'
            origin = f'{type(self).__name__}.is_{commname}_allowed()'
            self._raise_command_not_allowed(message, origin)

    def _command_allowed_state(self, commname, allowed):
        """Check command is allowed in the current device state.

        :param commname: name of the command
        :param allowed: list of allowed device state values

        """
        self._command_allowed(commname, 'device state', self.get_state(),
                              allowed)
