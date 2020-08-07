"""Handling of feature toggles."""

from enum import IntEnum, unique
import logging
import os

import ska_sdp_config


@unique
class FeatureToggle(IntEnum):
    """Feature Toggles."""

    CONFIG_DB = 1  #: Enable / Disable the Config DB
    AUTO_REGISTER = 2  #: Enable / Disable Tango DB auto-registration


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
        message = 'Unknown feature toggle: {} (allowed: {})' \
            .format(env_var, allowed)
        logging.error(message)
        raise ValueError(message)
    return env_var


def is_feature_active(feature_name):
    """Check if feature is active.

    :param feature_name: Name of the feature.
    :returns: True if the feature toggle is enabled.
    """
    env_var = _get_feature_toggle_env_var(feature_name)
    env_var_value = os.environ.get(env_var)
    return env_var_value == '1'


def set_feature_toggle_default(feature_name, default):
    """Set the default value of a feature toggle.

    :param feature_name: Name of the feature
    :param default: Default for the feature toggle (if it is not set)
    """
    env_var = _get_feature_toggle_env_var(feature_name)
    if not os.environ.get(env_var):
        logging.debug('Setting default for toggle: %s = %s', env_var, default)
        os.environ[env_var] = str(int(default))


def new_config_db():
    """Return a config db object (factory method)."""
    backend = 'etcd3' if is_feature_active(FeatureToggle.CONFIG_DB)\
        else 'memory'
    logging.info("Using config db backend %s", backend)
    config_db = ska_sdp_config.Config(backend=backend)
    return config_db
