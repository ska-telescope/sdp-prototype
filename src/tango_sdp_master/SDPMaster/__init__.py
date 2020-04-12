# -*- coding: utf-8 -*-
"""SDP Master device package."""
# pylint: disable=invalid-name

from . import release
from .SDPMaster import (SDPMaster, OperatingState, HealthState, main)

__version__ = release.VERSION
__version_info__ = release.VERSION_INFO

__all__ = ["SDPMaster", "OperatingState", "HealthState", "main", "release",
           "__version__", "__version_info__"]
