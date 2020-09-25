#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PIP setup script for the helm deploy package."""

import setuptools

with open("version.txt", "r") as fh:
    VERSION = fh.read().rstrip()
with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name='helm_deploy',
    version=VERSION,
    description='Helm deployment controller',
    author='SKA Sim Team',
    license='License :: OSI Approved :: BSD License',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://gitlab.com/ska-telescope/sdp-prototype/src/helm_deploy/',
    packages=setuptools.find_packages(),
    install_requires=[
        'python-dotenv',
        'ska-sdp-config>=0.0.9',
        'ska-logging>=0.3'
    ],
    setup_requires=['pytest-runner'],
    tests_require=[
        'pylint2junit',
        'pytest',
        'pytest-cov',
        'pytest-json-report',
        'pytest-pycodestyle',
        'pytest-pydocstyle',
        'pytest-pylint',
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
