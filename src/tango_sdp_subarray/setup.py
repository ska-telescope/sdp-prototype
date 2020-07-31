#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PIP setup script for the SDP Subarray Device package."""
# pylint: disable=exec-used

import os

from setuptools import setup

RELEASE_INFO = {}
RELEASE_PATH = os.path.join('SDPSubarray', 'release.py')
exec(open(RELEASE_PATH).read(), RELEASE_INFO)

with open('README.pypi.md', 'r') as file:
    LONG_DESCRIPTION = file.read()

setup(
    name=RELEASE_INFO['NAME'],
    version=RELEASE_INFO['VERSION'],
    description='SKA SDP Subarray device package',
    author=RELEASE_INFO['AUTHOR'],
    license=RELEASE_INFO['LICENSE'],
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://gitlab.com/ska-telescope/sdp-prototype/src/'
        'tango_sdp_subarray',
    packages=[
        'SDPSubarray'
    ],
    install_requires=[
        'pytango',
        'jsonschema',
        'ska-sdp-config>=0.0.9',
        'ska-sdp-logging>=0.0.6'
    ],
    entry_points={
        'console_scripts': ['SDPSubarray = SDPSubarray:main']
    },
    setup_requires=['pytest-runner'],
    tests_require=[
        'pylint2junit',
        'pytest',
        'pytest-bdd',
        'pytest-cov',
        'pytest-json-report',
        'pytest-pycodestyle',
        'pytest-pydocstyle',
        'pytest-pylint',
        'ska-telescope-model'
    ],
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: BSD License"
    ]
)
