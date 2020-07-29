#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PIP setup script for the SDP Logging package."""

import setuptools

with open("version.txt", "r") as fh:
    VERSION = fh.read().rstrip()
with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name='processing_controller',
    version=VERSION,
    description='SDP service responsible for the controlling the execution of processing blocks',
    author='SKA Sim Team',
    license='License :: OSI Approved :: BSD License',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://gitlab.com/ska-telescope/sdp-prototype/src/processing_controller/',
    packages=setuptools.find_packages(),
    install_requires=[
        'jsonschema',
        'requests',
        'ska-sdp-config>=0.0.9',
        'ska-sdp-logging>=0.0.6'
    ],
    setup_requires=['pytest-runner'],
    tests_require=[
        'pylint2junit',
        'pytest',
        'pytest-cov',
        'pytest-json-report',
        'pytest-pylint',
        'pytest-pycodestyle',
        'pytest-pydocstyle'
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
