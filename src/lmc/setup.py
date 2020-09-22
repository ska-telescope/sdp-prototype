#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PIP setup script for the SKA SDP LMC package."""
# pylint: disable=exec-used

import os

from setuptools import setup

RELEASE_INFO = {}
RELEASE_PATH = os.path.join('ska_sdp_lmc', 'release.py')
exec(open(RELEASE_PATH).read(), RELEASE_INFO)

with open('README.md', 'r') as file:
    LONG_DESCRIPTION = file.read()

setup(
    name=RELEASE_INFO['NAME'],
    version=RELEASE_INFO['VERSION'],
    description='SKA SDP Local Monitoring and Control (Tango devices)',
    author=RELEASE_INFO['AUTHOR'],
    license=RELEASE_INFO['LICENSE'],
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://gitlab.com/ska-telescope/sdp-prototype/src/'
        'lmc',
    packages=[
        'ska_sdp_lmc'
    ],
    package_data={
        'ska_sdp_lmc': ['schema/*.json']
    },
    install_requires=[
        'pytango',
        'jsonschema',
        'ska-sdp-config>=0.0.11',
        'ska-logging>=0.3'
    ],
    entry_points={
        'console_scripts': ['SDPMaster = ska_sdp_lmc.master:main',
                            'SDPSubarray = ska_sdp_lmc.subarray:main']
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
