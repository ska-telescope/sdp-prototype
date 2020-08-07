"""SDP Tango device base class module."""

import os
import logging

from tango import AttrWriteType, ErrSeverity, Except
from tango.server import Device, attribute

from . import release

LOG = logging.getLogger()


class SDPDevice(Device):
    """SDP Tango device base class."""

    # pylint: disable=attribute-defined-outside-init

    # Features: this is dict mapping feature name to default toggle value

    _features = {}

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

    # --------------
    # Public methods
    # --------------

    @classmethod
    def is_feature_active(cls, name: str):
        """Get the value of a feature toggle.

        :param name: Name of the feature

        """
        if name not in cls._features.keys():
            message = f'Unknown feature: {name}'
            LOG.error(message)
            raise ValueError(message)
        env_var = 'TOGGLE_' + name.upper()
        if env_var in os.environ:
            value = os.getenv(env_var) == '1'
        else:
            value = cls._features[name]
        return value

    @classmethod
    def set_feature_default(cls, name: str, value: bool):
        """Set the default value of a feature toggle.

        :param name: Name of the feature
        :param values: Default value for the feature toggle

        """
        if name not in cls._features.keys():
            message = f'Unknown feature: {name}'
            LOG.error(message)
            raise ValueError(message)
        cls._features[name] = value

    # ---------------
    # Private methods
    # ---------------

    def _raise_command_error(self, desc, origin=''):
        """Raise a command error.

        :param desc: Error message / description.
        :param origin: Error origin (optional).

        """
        self._raise_error(desc, reason='API_CommandFailed', origin=origin)

    def _raise_error(self, desc, reason='', origin=''):
        """Raise an error.

        :param desc: Error message / description.
        :param reason: Reason for the error.
        :param origin: Error origin (optional).

        """
        # pylint: disable=no-self-use
        if reason != '':
            LOG.error(reason)
        LOG.error(desc)
        if origin != '':
            LOG.error(origin)
        Except.throw_exception(reason, desc, origin, ErrSeverity.ERR)

    def _check_command(self, name,
                       state_allowed, obs_state_allowed=None,
                       admin_mode_allowed=None, admin_mode_invert=False):
        """Check if command is allowed in a particular state.

        :param name: name of the command
        :param state_allowed: list of allowed Tango device states
        :param obs_state_allowed: list of allowed observing states
        :param admin_mode_allowed: list of allowed administration modes
        :param admin_mode_invert: inverts condition on administration modes
        :returns: True if the command is allowed, otherwise raises exception

        """
        # pylint: disable=too-many-arguments

        allowed = True
        message = ''

        def compose_message(message_inp, name, state, value):
            """Compose the error message.

            :param message_inp: Error message / description.
            :param name: Name of the command.
            :param state: State or Mode.
            :param value: State value.

            """
            if message_inp == '':
                message_out = 'Command {} not allowed when {} is {}' \
                              ''.format(name, state, value)
            else:
                message_out = '{}, or when {} is {}' \
                              ''.format(message_inp, state, value)
            return message_out

        # Tango device state
        if state_allowed is not None:
            if self.get_state() not in state_allowed:
                allowed = False
                message = compose_message(message, name, 'the device',
                                          self.get_state())

        # Observing state
        if obs_state_allowed is not None:
            if self._obs_state not in obs_state_allowed:
                allowed = False
                message = compose_message(message, name, 'obsState',
                                          self._obs_state.name)

        # Administration mode
        if admin_mode_allowed is not None:
            condition = self._admin_mode not in admin_mode_allowed
            if admin_mode_invert:
                condition = not condition
            if condition:
                allowed = False
                message = compose_message(message, name, 'adminMode',
                                          self._admin_mode.name)
        # Tango device state
        if state_allowed is not None:
            if self.get_state() not in state_allowed:
                allowed = False
                message = compose_message(message, name, 'the device',
                                          self.get_state())

        return allowed, message
