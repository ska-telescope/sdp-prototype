#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PIP setup script for the SDP Subarray Device package."""
import os
from setuptools import setup

setup_dir = os.path.dirname(os.path.abspath(__file__))

release_filename = os.path.join(setup_dir, 'SDPSubarray', 'release.py')
exec(open(release_filename).read())

setup(
    name=NAME,
    version=VERSION,
    description='SKA SDP Subarray',
    long_description=DESCRIPTION,
    author=AUTHOR,
    url=
    'https://github.com/ska-telescope/sdp-prototype/src/tango_sdp_subarray',
    classifiers=[
          "Programming Language :: Python :: 3 :: Only",
          "Development Status :: 1 - Planning",
    ],
    license=LICENSE,
    packages=['SDPSubarray'],
    test_suite='tests',
    tests_require=['pytest'],
    zip_safe=False
)
