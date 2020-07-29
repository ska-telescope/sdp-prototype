"""Utilities."""

import sys


def terminate(signame, frame):
    """Signal handler to exit gracefully."""
    # pylint: disable=unused-argument
    sys.exit()
