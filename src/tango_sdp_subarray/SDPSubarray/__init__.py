# -*- coding: utf-8 -*-
"""SDPSubarray device package."""
# pylint: disable=invalid-name

from . import release
from .SDPSubarray import (AdminMode, HealthState, ObsState, SDPSubarray, main)

__all__ = ["SDPSubarray", "AdminMode", "HealthState", "ObsState", "main",
           "release"]

__version__ = release.VERSION
__version_info__ = release.VERSION_INFO
