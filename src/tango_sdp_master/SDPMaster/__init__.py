# -*- coding: utf-8 -*-
"""SDP Master device package."""
# pylint: disable=invalid-name

from . import release
from .SDPMaster import SDPMaster, HealthState, main

__all__ = ["SDPMaster", "HealthState", "main", "release"]

__version__ = release.VERSION
__version_info__ = release.VERSION_INFO
