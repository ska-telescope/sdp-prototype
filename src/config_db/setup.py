"""PIP set-up for SKA SDP configuration database package."""

# pylint: disable=exec-used

import os

from setuptools import setup

RELEASE_INFO = {}
RELEASE_PATH = os.path.join('ska_sdp_config', 'release.py')
exec(open(RELEASE_PATH).read(), RELEASE_INFO)

with open('README.md', 'r') as file:
    LONG_DESCRIPTION = file.read()

setup(
    name=RELEASE_INFO['NAME'],
    version=RELEASE_INFO['VERSION'],
    description='SKA SDP Configuration Database',
    author=RELEASE_INFO['AUTHOR'],
    license=RELEASE_INFO['LICENSE'],
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='http://gitlab.com/ska-telescope/sdp-prototype/src/'
        'config_db',
    install_requires=[
        'etcd3-py', 'docopt-ng', 'kubernetes'
    ],
    classifiers=[
        'Topic :: Database :: Front-Ends',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: System :: Distributed Computing',
    ],
    packages=['ska_sdp_config', 'ska_sdp_config/entity'],
    test_suite='tests',
    tests_require=['pytest'],
    scripts=['scripts/sdpcfg']
)
