"""Device attributes."""

import enum


@enum.unique
class AdminMode(enum.IntEnum):
    """AdminMode enum."""

    OFFLINE = 0
    ONLINE = 1
    MAINTENANCE = 2
    NOT_FITTED = 3
    RESERVED = 4


@enum.unique
class HealthState(enum.IntEnum):
    """HealthState enum."""

    OK = 0
    DEGRADED = 1
    FAILED = 2
    UNKNOWN = 3


@enum.unique
class ObsState(enum.IntEnum):
    """ObsState enum."""

    EMPTY = 0
    RESOURCING = 1
    IDLE = 2
    CONFIGURING = 3
    READY = 4
    SCANNING = 5
    ABORTING = 6
    ABORTED = 7
    RESETTING = 8
    FAULT = 9
    RESTARTING = 10
