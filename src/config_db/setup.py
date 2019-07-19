"""PIP set-up for SKA SDP configuration database package."""

from setuptools import setup

setup(
    name='ska-sdp-config',
    version='0.0.1',
    description='SKA SDP Configuration Database',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Benjamin Mort, Nijn Thykkathu, Peter Wortmann',
    url='https://github.com/ska-telescope/sdp-prototype/src/config_db',
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
