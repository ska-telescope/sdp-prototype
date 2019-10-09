# -*- coding: utf-8 -*-
"""This script will checks and spawn the appropriate workflow dynamically."""
# pylint: disable=invalid-name
# pylint: disable=too-many-lines
# pylint: disable=fixme

import json
import logging
import sys
import time
from enum import IntEnum, unique
from inspect import currentframe, getframeinfo
from math import ceil
import os
from os.path import dirname, join

# from jsonschema import exceptions, validate
# import tango
# from tango import AttrWriteType, AttributeProxy, ConnectionFailed, Database, \
#     DbDevInfo, DevState, Except
# from tango.server import Device, DeviceMeta, attribute, command, \
#     device_property, run
#
# try:
#     from ska_sdp_config.config import Config as ConfigDbClient
#     from ska_sdp_config.entity import ProcessingBlock
# except ImportError:
#     ConfigDbClient = None
#     ProcessingBlock = None


#TODO:
# Check where is the workflow is selected and deployed,
# Replace and add this script
# Write unit test

