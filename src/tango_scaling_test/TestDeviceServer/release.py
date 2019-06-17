# -*- coding: utf-8 -*-
"""Test device version info."""
__version_info__ = (0, 1, 0, 'b1')
__version__ = '.'.join(map(str, __version_info__[0:3]))
if len(__version_info__) == 4:
    __version__ += __version_info__[3]
