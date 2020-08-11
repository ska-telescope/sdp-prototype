"""Handling of feature toggles."""

import copy
import logging
import os
from typing import Sequence


class FeatureToggles:
    """Defines a set of feature toggles."""

    def __init__(self, feature_names: Sequence[str]):
        """
        Construct feature toggles.

        :param feature_names: sequence containing feature names
        """
        self.features = copy.copy(feature_names)

    def _get_env_var(self, feature_name: str):
        """Get the env var associated with the feature toggle.

        :param feature_name: Name of the feature.
        :returns: environment variable name for feature toggle.

        """
        env_var = str('toggle_' + feature_name).upper()
        allowed = ['TOGGLE_' + toggle.upper() for toggle in self.features]
        if env_var not in allowed:
            message = 'Unknown feature toggle: {} (allowed: {})' \
                .format(env_var, allowed)
            logging.error(message)
            raise ValueError(message)
        return env_var

    def is_active(self, feature_name: str) -> bool:
        """Check if feature is active.

        :param feature_name: Name of the feature.
        :returns: True if the feature toggle is enabled.
        """
        env_var = self._get_env_var(feature_name)
        env_var_value = os.environ.get(env_var)
        return env_var_value == '1'

    def set_default(self, feature_name: str, default: bool) -> None:
        """Set the default value of a feature toggle.

        :param feature_name: Name of the feature
        :param default: Default for the feature toggle (if it is not set)
        """
        env_var = self._get_env_var(feature_name)
        if not os.environ.get(env_var):
            logging.debug('Setting default for toggle: %s = %s',
                          env_var, default)
            os.environ[env_var] = str(int(default))
