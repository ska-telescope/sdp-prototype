# -*- coding: utf-8 -*-

"""This file is part of the SDPMaster project.

Distributed under the terms of the GPL license.
See LICENSE.txt for more info.
"""
# pylint: disable=invalid-name

from . import release
from .SDPMaster import SDPMaster, main

__version__ = release.VERSION
__version_info__ = release.VERSION_INFO
__author__ = release.AUTHOR
