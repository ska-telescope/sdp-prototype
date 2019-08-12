# -*- coding: utf-8 -*-
"""SDPSubarray device package."""
# pylint: disable=invalid-name

from . import release
from .SDPSubarray import (AdminMode, HealthState, ObsState, SDPSubarray, main,
                          init_logger)

__version__ = release.VERSION
__version_info__ = release.VERSION_INFO

__all__ = ["SDPSubarray", "AdminMode", "HealthState", "ObsState", "main",
           "release", "init_logger", '__version__', '__version_info__']
