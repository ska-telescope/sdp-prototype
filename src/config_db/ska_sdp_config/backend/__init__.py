"""Backends for SKA SDP configuration DB."""

from .common import ConfigCollision, ConfigVanished
from .etcd3 import Etcd3Backend
from .memory import MemoryBackend
