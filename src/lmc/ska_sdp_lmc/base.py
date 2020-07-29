"""SDP Tango device base class module."""

# pylint: disable=duplicate-code

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
