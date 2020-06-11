import logging
from typing import List, Callable

from ska_sdp_config.backend import (
    _tag_depth, _untag_depth, _check_path, ConfigCollision, ConfigVanished)


def _op(path: str, value: str,
        to_check: Callable[[str], None], to_do: Callable[[str, str], None]):
    tag = _tag_depth(path)
    to_check(tag)
    to_do(tag, value)


class MemoryBackend:
    """
    In-memory backend implementation, principally for testing.
    """
    def __init__(self):
        self.dict = {}

    def lease(self, ttl=10) -> 'Lease':
        class Lease:
            pass
        return Lease()

    def txn(self, max_retries=64) -> 'MemoryTransaction':
        return MemoryTransaction(self)

    def get(self, path: str) -> str:
        return self.dict.get(_tag_depth(path), None)

    def _put(self, path: str, value: str) -> None:
        tag = _tag_depth(path)
        _check_path(path)
        logging.info("path {} tag {}".format(path, tag))
        self.dict[tag] = value

    def _check_exists(self, path: str) -> None:
        if path not in self.dict.keys():
            raise ConfigVanished(path, "{} not in dictionary".format(path))

    def _check_not_exists(self, path: str) -> None:
        if path in self.dict.keys():
            raise ConfigCollision(path, "path {} already in dictionary".format(path))

    def create(self, path: str, value: str, lease=None) -> None:
        _op(path, value, self._check_not_exists, self._put)

    def update(self, path: str, value: str, must_be_rev=None) -> None:
        _op(path, value, self._check_exists, self._put)

    def delete(self, path, must_exist=True) -> None:
        _op(path, None, self._check_exists, lambda t, _: self.dict.pop(t))

    def list_keys(self, path: str) -> List[str]:
        return sorted([k for k in self.dict.keys() if k.startswith(path)])

    def close(self) -> None:
        pass


class MemoryTransaction:
    def __init__(self, backend: MemoryBackend):
        self.backend = backend

    def __iter__(self):
        yield self

    def commit(self) -> None:
        pass

    def get(self, path: str) -> str:
        return self.backend.get(path)

    def create(self, path: str, value: str, lease=None) -> None:
        self.backend.create(path, value)

    def update(self, path: str, value: str, must_be_rev=None) -> None:
        self.backend.update(path, value)

    def delete(self, path, must_exist=True):
        self.backend.delete(path)

    def list_keys(self, path: str) -> List[str]:
        return self.backend.list_keys(path)

    def loop(self, *args, **kwargs) -> None:
        pass


