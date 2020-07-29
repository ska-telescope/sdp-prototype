"""SKA SDP local monitoring and control (Tango devices)."""

# pylint:disable=duplicate-code

from . import release
from .attributes import (AdminMode, HealthState, ObsState)
from .master import SDPMaster
from .subarray import SDPSubarray

__version__ = release.VERSION

__all__ = ['__version__', 'AdminMode', 'HealthState', 'ObsState',
           'SDPMaster', 'SDPSubarray']
