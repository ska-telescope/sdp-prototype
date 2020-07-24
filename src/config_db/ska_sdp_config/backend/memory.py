"""
Memory backend for SKA SDP configuration DB.

The main purpose of this is for use in testing.
In principle it should behave in the same way as the etcd backend.
No attempt has been made to make it thread-safe, so it probably isn't.
"""
from typing import List, Callable

from .common import (
    _depth, _tag_depth,
    _untag_depth, _check_path,
    ConfigCollision, ConfigVanished
)


def _op(path: str, value: str,
        to_check: Callable[[str], None], to_do: Callable[[str, str], None]):
    _check_path(path)
    tag = _tag_depth(path)
    to_check(tag)
    to_do(tag, value)


class MemoryBackend:
    """In-memory backend implementation, principally for testing."""

    # Class variable to store data
    _data = {}

    def __init__(self):
        """Construct a memory backend."""
        pass

    def lease(self, *args, **kwargs) -> 'Lease':
        """
        Generate a dummy lease object.

        This currently has no additional methods.
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: dummy lease object
        """
        class Lease:
            """Dummy lease class."""
        return Lease()

    def txn(self, *args, **kwargs) -> 'MemoryTransaction':
        """
        Create an in-memory "transaction".

        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: transaction object
        """
        return MemoryTransaction(self)

    def get(self, path: str) -> str:
        """
        Get the value at the given path.

        :param path: to lookup
        :return: the value
        """
        return self._data.get(_tag_depth(path), None)

    def _put(self, path: str, value: str) -> None:
        self._data[path] = value

    def _check_exists(self, path: str) -> None:
        if path not in self._data.keys():
            raise ConfigVanished(path, "{} not in dictionary".format(path))

    def _check_not_exists(self, path: str) -> None:
        if path in self._data.keys():
            raise ConfigCollision(path,
                                  "path {} already in dictionary".format(path))

    def create(self, path: str, value: str, *args, **kwargs) -> None:
        """
        Create an entry at the given path.

        :param path: to create an entry
        :param value: of the entry
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: nothing
        """
        _op(path, value, self._check_not_exists, self._put)

    def update(self, path: str, value: str, *args, **kwargs) -> None:
        """
        Update an entry at the given path.

        :param path: to create an entry
        :param value: of the entry
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: nothing
        """
        _op(path, value, self._check_exists, self._put)

    def delete(self, path, *args, **kwargs) -> None:
        """
        Delete an entry at the given path.

        :param path: to create an entry
        :param value: of the entry
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: nothing
        """
        _op(path, None, self._check_exists, lambda t, _: self._data.pop(t))

    def list_keys(self, path: str) -> List[str]:
        """
        Get a list of the keys at the given path.

        In common with the etcd backend, the structure is
        "flat" rather than a real hierarchy, even though it looks like one.
        :param path:
        :return: list of keys
        """
        # Match only at this depth level. Special case for top level.
        if path == '/':
            new_path = path
            depth = 1
        else:
            new_path = path.rstrip('/')
            depth = _depth(new_path) + 1
        tag = _tag_depth(new_path, depth=depth)
        return sorted([_untag_depth(k)
                       for k in self._data if k.startswith(tag)])

    def close(self) -> None:
        """
        Close the resource.

        This does nothing.
        :return: nothing
        """


class MemoryTransaction:
    """
    Transaction wrapper around the backend implementation.

    Transactions always succeed if they are valid, so there is no need
    to loop; however the iterator is supported for compatibility with
    the etcd backend.
    """

    def __init__(self, backend: MemoryBackend):
        """
        Construct an in-memory transaction.

        :param backend: to wrap
        """
        self.backend = backend

    def __iter__(self):
        """
        Iterate over just this object.

        :return: this object
        """
        yield self

    def commit(self) -> None:
        """
        Commit the transaction.

        This does nothing.
        :return: nothing
        """

    def get(self, path: str) -> str:
        """
        Get the value at the given path.

        :param path: to lookup
        :return: the value
        """
        return self.backend.get(path)

    def create(self, path: str, value: str, *args, **kwargs) -> None:
        """
        Create an entry at the given path.

        :param path: to create an entry
        :param value: of the entry
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: nothing
        """
        self.backend.create(path, value)

    def update(self, path: str, value: str, *args, **kwargs) -> None:
        """
        Update an entry at the given path.

        :param path: to create an entry
        :param value: of the entry
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: nothing
        """
        self.backend.update(path, value)

    def delete(self, path, *args, **kwargs):
        """
        Delete an entry at the given path.

        :param path: to create an entry
        :param value: of the entry
        :param args: arbitrary, not used
        :param kwargs: arbitrary, not used
        :return: nothing
        """
        self.backend.delete(path)

    def list_keys(self, path: str) -> List[str]:
        """
        Get a list of the keys at the given path.

        In common with the etcd backend, the structure is
        "flat" rather than a real hierarchy, even though it looks like one.
        :param path:
        :return: list of keys
        """
        return self.backend.list_keys(path)

    def loop(self, *args, **kwargs) -> None:
        """
        Loop the transaction.

        This does nothing.
        :return: nothing
        """
