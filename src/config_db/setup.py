"""PIP set-up for SKA SDP configuration database package."""

from setuptools import setup

with open('README.md', 'r') as file:
    LONG_DESCRIPTION = file.read()
REPOS_URL = 'http://github.com/ska-telescope/sdp-prototype'

setup(
    name='ska-sdp-config',
    version='0.0.2',
    description='SKA SDP Configuration Database',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Benjamin Mort, Nijn Thykkathu, Peter Wortmann',
    url=REPOS_URL+'/tree/master/src/config_db',
    install_requires=[
        'etcd3-py', 'docopt-ng'
    ],
    classifiers=[
        'Topic :: Database :: Front-Ends',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: System :: Distributed Computing',
    ],
    license='License :: OSI Approved :: BSD License',
    packages=['ska_sdp_config', 'ska_sdp_config/entity'],
    test_suite='tests',
    tests_require=['pytest'],
    scripts=['scripts/sdpcfg']
)
