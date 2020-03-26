"""PIP set-up for SKA SDP configuration database package."""

import setuptools
import ska_sdp_config

with open('README.md', 'r') as file:
    LONG_DESCRIPTION = file.read()

setuptools.setup(
    name='ska-sdp-config',
    version=ska_sdp_config.__version__,
    description='SKA SDP Configuration Database',
    author='SKA ORCA and Sim Teams',
    license='License :: OSI Approved :: BSD License',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='http://gitlab.com/ska-telescope/sdp-prototype/src/'
        'config_db',
    install_requires=[
        'etcd3-py', 'docopt-ng', 'pyyaml'
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
