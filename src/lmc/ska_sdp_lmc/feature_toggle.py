"""Feature toggle."""

import os


class FeatureToggle:
    """Feature toggle class."""

    def __init__(self, name: str, default: bool):
        """Initialise feature toggle.

        :param name: Name of feature.
        :param default: Default value for toggle.

        """
        self._name = name
        self._default = default

    def set_default(self, default: bool) -> None:
        """Set feature default toggle value.

        :param default: Default value for toggle.

        """
        self._default = default

    def is_active(self) -> bool:
        """Check if feature is active.

        :returns: Toggle value.

        """
        env_var = str('toggle_' + self._name).upper()
        if env_var in os.environ:
            value = os.environ.get(env_var) == '1'
        else:
            value = self._default
        return value
