#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for the SDP Subarray Device package."""
# pylint: disable=invalid-name, exec-used, undefined-variable


import os
import sys
from setuptools import setup

setup_dir = os.path.dirname(os.path.abspath(__file__))

# make sure we use latest info from local code
sys.path.insert(0, setup_dir)

readme_filename = os.path.join(setup_dir, 'README.rst')
with open(readme_filename) as file:
    long_description = file.read()

release_filename = os.path.join(setup_dir, 'SDPSubarray', 'release.py')
exec(open(release_filename).read())

pack = ['SDPSubarray']

setup(name=NAME,
      version=VERSION,
      description='',
      packages=pack,
      include_package_data=True,
      test_suite="test",
      entry_points={'console_scripts': ['SDPSubarray = SDPSubarray:main']},
      author='brian.mcilwrath',
      author_email='brian.mcilwrath at stfc.ac.uk',
      license='none',
      long_description=long_description,
      url='www.tango-controls.org',
      platforms="Unix Like"
      )
