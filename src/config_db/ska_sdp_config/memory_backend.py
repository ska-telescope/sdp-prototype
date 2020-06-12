from typing import List, Callable

from ska_sdp_config.backend import (
    _depth, _tag_depth, _untag_depth, _check_path, ConfigCollision, ConfigVanished)


def _op(path: str, value: str,
        to_check: Callable[[str], None], to_do: Callable[[str, str], None]):
    _check_path(path)
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
        self.dict[path] = value

    def _check_exists(self, path: str) -> None:
        if path not in self.dict.keys():
            raise ConfigVanished(path, "{} not in dictionary".format(path))

    def _check_not_exists(self, path: str) -> None:
        if path in self.dict.keys():
            raise ConfigCollision(path, "path {} already in dictionary".format(path))

    def create(self, path: str, value: str, **kwargs) -> None:
        _op(path, value, self._check_not_exists, self._put)

    def update(self, path: str, value: str, **kwargs) -> None:
        _op(path, value, self._check_exists, self._put)

    def delete(self, path, must_exist=True) -> None:
        _op(path, None, self._check_exists, lambda t, _: self.dict.pop(t))

    def list_keys(self, path: str) -> List[str]:
        # Match only at this depth level. Special case for top level.
        if path == '/':
            p = path
            depth = 1
        else:
            p = path.rstrip('/')
            depth = _depth(p)+1
        tag = _tag_depth(p, depth=depth)
        return sorted([_untag_depth(k) for k in self.dict.keys() if k.startswith(tag)])

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

    def create(self, path: str, value: str, *args, **kwargs) -> None:
        self.backend.create(path, value)

    def update(self, path: str, value: str, *args, **kwargs) -> None:
        self.backend.update(path, value)

    def delete(self, path, *args, **kwargs):
        self.backend.delete(path)

    def list_keys(self, path: str) -> List[str]:
        return self.backend.list_keys(path)

    def loop(self, *args, **kwargs) -> None:
        pass


