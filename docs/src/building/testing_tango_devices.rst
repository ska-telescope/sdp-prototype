=========================
Testing SDP Tango Devices
=========================

The SDP Tango devices are SDPMaster and SDPSubarray. An brief introduction to the how the Tango
system may be installed is contained in :doc:`building_tango_devices`.

Basically these Tango devices may be built and tested locally if Tango - and its associated Database
Device Server - is installed on a computer. Otherwise Docker containers can be used to build and
test these devices. Makefile targets are provided to facilitate this.

SDP Subarray Device
===================

This section describes how the Subarray device can be tested. The master device should
be exactly equivalent.

Interactive testing
-------------------

If a full Tango system is running on a system, Tango device servers may be exercised interactively
using ``itango`` (often called ``itango3`` for Python 3).

As an example running a Tango device in one terminal window::

    $ python3 SDPSubarray 1 -v4
    1|2020-04-07T10:24:29.333Z|INFO|MainThread|init|core_logging.py#132|SDPSubarray|Logging initialised
    1|2020-04-07T10:24:29.334Z|DEBUG|MainThread|set_feature_toggle_default|SDPSubarray.py#529|SDPSubarray|Setting default for toggle: TOGGLE_CONFIG_DB = False
    1|2020-04-07T10:24:29.334Z|DEBUG|MainThread|set_feature_toggle_default|SDPSubarray.py#529|SDPSubarray|Setting default for toggle: TOGGLE_CBF_OUTPUT_LINK = False
    1|2020-04-07T10:24:29.334Z|DEBUG|MainThread|set_feature_toggle_default|SDPSubarray.py#529|SDPSubarray|Setting default for toggle: TOGGLE_AUTO_REGISTER = True
    1|2020-04-07T10:24:29.367Z|DEBUG|MainThread|register|SDPSubarray.py#1034|SDPSubarray|Device 'mid_sdp/elt/subarray_1' already registered
    1|2020-04-07T10:24:29.508Z|DEBUG|MainThread|tango_loop|server.py#1342|SDPSubarray|server loop started
    1|2020-04-07T10:24:29.576Z|INFO|MainThread|init_device|SDPSubarray.py#171|SDPSubarray|Initialising SDP Subarray: mid_sdp/elt/subarray_1
    1|2020-04-07T10:24:29.576Z|DEBUG|MainThread|_set_obs_state|SDPSubarray.py#570|SDPSubarray|Setting obsState to: <ObsState.IDLE: 0>
    1|2020-04-07T10:24:29.577Z|DEBUG|MainThread|_set_admin_mode|SDPSubarray.py#577|SDPSubarray|Setting adminMode to: <AdminMode.ONLINE: 1>
    1|2020-04-07T10:24:29.577Z|DEBUG|MainThread|_set_health_state|SDPSubarray.py#584|SDPSubarray|Setting healthState to: <HealthState.OK: 0>
    1|2020-04-07T10:24:29.577Z|WARNING|MainThread|init_device|SDPSubarray.py#192|SDPSubarray|SDP Config DB disabled by feature toggle
    1|2020-04-07T10:24:29.577Z|DEBUG|MainThread|init_device|SDPSubarray.py#197|SDPSubarray|CBF output link disabled
    1|2020-04-07T10:24:29.577Z|INFO|MainThread|init_device|SDPSubarray.py#201|SDPSubarray|SDP Subarray initialised: mid_sdp/elt/subarray_1
    Ready to accept request

From another window::

    $ itango3
    ITango 9.2.5 -- An interactive Tango client.

    Running on top of Python 3.7.5, IPython 5.8 and PyTango 9.2.5

    help      -> ITango's help system.
    object?   -> Details about 'object'. ?object also works, ?? prints more.

    IPython profile: tango

    hint: Try typing: mydev = Device("<tab>

    In [1]: d = DeviceProxy("mid_sdp/elt/subarray_1")

    In [2]: d.state()
    Out[2]: tango._tango.DevState.OFF

    In [3]: d.status()
    Out[3]: 'The device is in OFF state.'


Test Environment
----------------

The full set of tests (including linting and coverage) is run using::

    python setup.py test

and this is also the command used within the CI pipeline.

The tests are defined using the BDD test framework which give more human readable test scenarios::

    Scenario: AssignResources command successful
        Given I have an ONLINE SDPSubarray device
        When I call AssignResources
        Then State should be ON
        And obsState should be IDLE
        And adminMode should be ONLINE

The test scenarios are defined in the file ``tests/1_VTS-223.feature``
and the implementations are in ``tests/test_subarray_device.py``.

The test fixture implementation file ``tests/conftest.py`` uses the import::

    from tango.test_context import DeviceTestContext

which, while poorly documented, seems to negate the need to have a running Tango Database Device server.

Docker Image and testing
------------------------

A Docker image containing the SDPSubarray device is published to the `Nexus repository on the EngageSKA cluster
<https://nexus.engageska-portugal.pt/#browse/browse:docker>`_.

Running tests inside a container
++++++++++++++++++++++++++++++++

On a system where ``pytango`` cannot be installed natively, tests of this
device can also be runinside the ``pytango_ska_test`` container with the
following command::

    docker run -t --rm -v $(pwd):/app \
      nexus.engageska-portugal.pt/sdp-prototype/pytango_ska_test:latest \
      python -m pytest \
      --pylint \
      --pycodestyle \
      --pydocstyle \
      --cov=SDPSubarray \
      --cov-report=term \
      --cov-config=./setup.cfg \
      -vv --gherkin-terminal-reporter

or to run the test directly inside the container::

    docker run --rm -it -v $(pwd):/app nexus.engageska-portugal.pt/sdp-prototype/pytango_ska_test:latest

this will create a bash session in the container and then run::

    python3 setup.py test

or equivalently::

    make test

Testing interactively with a Tango facility and iTango
++++++++++++++++++++++++++++++++++++++++++++++++++++++

Start a tango facility by running::

    kubectl exec -it itango-tango-base-sdp-prototype -- /venv/bin/itango3

You obtain a handle for the first subarray device with::

    d = DeviceProxy('mid_sdp/elt/subarray_1')

or for the second device with::

    d = DeviceProxy('mid_sdp/elt/subarray_2')

Then query the state of the device with::

    d.state()

When first initialised the device will report ``'The device is in OFF state.'``

To query the obsState attribute::

    d.obsState

This will return ``<obsState.IDLE: 0>``

Create a configuration string for the scheduling block instance::

    config_sbi = '''
    {
      "id": "sbi-mvp01-20200425-00000",
      "max_length": 21600.0,
      "scan_types": [
        {
          "id": "science",
          "channels": [
            {"count": 372, "start": 0, "stride": 2, "freq_min": 0.35e9, "freq_max": 0.358e9, "link_map": [[0,0], [200,1]]}
          ]
        },
        {
          "id": "calibration",
          "channels": [
            {"count": 372, "start": 0, "stride": 2, "freq_min": 0.35e9, "freq_max": 0.358e9, "link_map": [[0,0], [200,1]]}
          ]
        }
      ],
      "processing_blocks": [
        {
          "id": "pb-mvp01-20200425-00000",
          "workflow": {"type": "realtime", "id": "test_realtime", "version": "0.1.0"},
          "parameters": {}
        },
        {
          "id": "pb-mvp01-20200425-00001",
          "workflow": {"type": "realtime", "id": "test_realtime", "version": "0.1.0"},
          "parameters": {}
        },
        {
          "id": "pb-mvp01-20200425-00002",
          "workflow": {"type": "batch", "id": "test_batch", "version": "0.1.0"},
          "parameters": {},
          "dependencies": [
            {"pb_id": "pb-mvp01-20200425-00000", "type": ["visibilities"]}
          ]
        },
        {
          "id": "pb-mvp01-20200425-00003",
          "workflow": {"type": "batch", "id": "test_batch", "version": "0.1.0"},
          "parameters": {},
          "dependencies": [
            {"pb_id": "pb-mvp01-20200425-00002", "type": ["calibration"]}
          ]
        }
      ]
    }
    '''

Note that the link map for each scan type is included in the configuration.
The format of this may change.

The scheduling block instance is started by the ``AssignResources`` command::

    d.AssignResources(config_sbi)

The subarray should now be ``ON``, but the obsState remains ``IDLE``.

Before executing a scan, we need to configure the scan type. This is done by passing the scan type to the
``Configure`` command::

    d.Configure('{"scan_type": "science"}')

which changes the obsState to ``CONFIGURING`` and then to ``READY``.

To start a scan, we need to pass the scan ID to the ``Scan`` command::

    d.Scan('{"id": 1}')

which changes the obsState to ``SCANNING``.

The scan is ended with the ``EndScan`` command::

    d.EndScan()

which changes the obsState to ``READY`` again.

``Scan`` and ``EndScan`` can be called any number of times to execute an instance of the configured scan type. The scan ID
should be unique for each scan, although SDP does not check this at present.

The scan type can be changed by executing the Configure command again with a different scan type. This should be
one of the predefined scan types, although there is an option to pass new scan types in the ``Configure`` command.
This will only be supported by SDP for special-purpose workflows

To do this, create a configuration string that includes the ``new_scan_types`` entry::

    config_newscantype = '''
    {
      "new_scan_types": [
        {
          "id": "new_calibration",
          "channels": [
            {"count": 372, "start": 0, "stride": 2, "freq_min": 0.35e9, "freq_max": 0.358e9, "link_map": [[0,0], [200,1]]}
          ]
        }
      ],
      "scan_type": "new_calibration"
    }
    '''

and pass that to the ``Configure`` command::

    d.Configure(config_newscantype)

The ``Reset`` command clears the scan type::

    d.Reset()

which changes the obsState to ``IDLE``.

Finally, when the obsState is ``IDLE``, the scheduling block instance is ended by the ``ReleaseResources`` command::

    d.ReleaseResources()

after which the subarray should be ``OFF``.

To list other commands and attributes exposed by the SDPSubarray device::

    d.command_list_query()
    d.attribute_list_query()

Testing from a branch
---------------------

To test the changes made from a branch, create a file called ``test.yaml`` inside the ``charts`` directory and add::

    tangods:
      subarray:
        version: <version>-<git-hash>

where ``<version>`` is the version number and ``<git-hash>`` is the latest git hash of the branch.
Then install the ``sdp-prototype`` chart with::

    helm install test sdp-prototype -f test.yaml

Makefile targets for testing
----------------------------

A Makefile is provided to enable possibly more simple testing using the Docker images

A makefile is provided to simplify some of these tasks. The makefile targets are given by typing
*make help* which will give output like::

    NAME        : tangods_sdp_subarray
    IMAGE       : nexus.engageska-portugal.pt/sdp-prototype/tangods_sdp_subarray
    VERSION     : 0.7.2
    GIT VERSION : d0a58177
    DEFAULT TAG : nexus.engageska-portugal.pt/sdp-prototype/tangods_sdp_subarray:0.7.2-d0a58177
    =
    Imported targets:
        piplock                        Rebuild the Pipfile.lock file
        build                          Build the image, tagged as :$(VERSION)-$(GIT_VERSION)
        push                           Push default image (tagged as :$(VERSION)-(GIT_VERSION)
        push_latest                    Push the image tagged as :latest
        push_version                   Push the image tagged as :$(VERSION) (without the git sha)
        pull                           Fetch the latest image
        pull_default                   Fetch the default Git versioned image
        ls                             List images built from this folder
        rm                             Remove all images built from this folder
        help                           Show this help.
    Local targets:
        register                       register devices (usage: make register <number of devices>)
        unregister                     Unregister devices
        start_dev                      Start the device from the current code
        start_shell                    Start the device from the current code
        start                          Start the device from the current Docker image
        stop                           Stop the device
        test                           Run tests for the device
        test_only                      Run tests for the device
        test_shell                     Provide a test shell with the current code
        dev_shell                      Provide a development shell with the current code
        build_package                  Build the python package


SDP Master Device
=================

The master device should be exactly equivalent.
