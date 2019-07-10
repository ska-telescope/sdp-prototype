# -*- coding: utf-8 -*-
"""SDPSubarray device package."""
# pylint: disable=invalid-name

from . import release

from .SDPSubarray import (
    SDPSubarray,
    AdminMode,
    HealthState,
    ObsState,
    main
)

__version__ = release.VERSION
__version_info__ = release.VERSION_INFO
__author__ = release.AUTHOR
