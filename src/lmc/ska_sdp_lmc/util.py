"""Utilities."""

import functools
import logging
import sys
from typing import Callable


def terminate(signame, frame):
    """Signal handler to exit gracefully."""
    # pylint: disable=unused-argument
    sys.exit()


def log_command(command_function: Callable):
    """
    Decorate a command function call to add logging.

    :param command_function: to decorate
    :return: any result of function
    """
    @functools.wraps(command_function)
    def wrapper(self, *args, **kwargs):
        name = command_function.__name__
        logging.info('-------------------------------------------------------')
        logging.info('%s (%s)', name, self.get_name())
        logging.info('-------------------------------------------------------')
        ret = command_function(self, *args, **kwargs)
        logging.info('-------------------------------------------------------')
        logging.info('%s Successful', name)
        logging.info('-------------------------------------------------------')
        return ret
    return wrapper


def log_lines(string: str, header: str = '') -> None:
    """
    Log a string split into lines.

    :param string: to split
    :param header: context information to log first
    """
    logging.info(header)
    for line in string.splitlines():
        logging.info(line)
