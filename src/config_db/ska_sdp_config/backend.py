"""
Some generic functionality for implementing backends.
"""


# Some utilities for handling tagging paths.
#
# The idea here is that etcd3 only supports straight-up prefix
# searches, but we do not want to get "/a/b/c" when listing "/a/"
# (just "/a/b"). Therefore we prepend all paths with the number of
# slashes they contain, making standard prefix search non-recursive as
# suggested by etcd's documentation. The recursive behaviour can
# always be restored by doing separate searches per recursion level.
def _tag_depth(path: str, depth=None) -> str:
    """Add depth tag to path."""
    # All paths must start at the root
    if not path or path[0] != '/':
        raise ValueError("Path must start with /!")
    if depth is None:
        depth = path.count('/')
    return "{}{}".format(depth, path).encode('utf-8')


def _untag_depth(path: str) -> str:
    """Remove depth from path."""
    # Cut from first '/'
    slash_ix = path.index('/')
    if slash_ix is None:
        return path
    return path[slash_ix:]


def _check_path(path: str) -> None:
    if path and path[-1] == '/':
        raise ValueError("Path should not have a trailing '/'!")


class ConfigCollision(RuntimeError):
    """Exception generated if key to create already exists."""

    def __init__(self, path: str, message: str):
        """Instantiate the exception."""
        self.path = path
        super().__init__(message)


class ConfigVanished(RuntimeError):
    """Exception generated if key to update that does not exist."""

    def __init__(self, path: str, message: str):
        """Instantiate the exception."""
        self.path = path
        super().__init__(message)
