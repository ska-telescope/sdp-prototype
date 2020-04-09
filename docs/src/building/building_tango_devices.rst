Building SDP Tango Devices
==========================

The SDP Tango devices are SDPMaster and SDPSubarray

These components can be built in several ways - depending on the system and software environments and the intended
use.

To run the Tango devices locally requires a running Tango system - which is based on C++ but will will need several extra
software components (such as omniORB as a CORBA implementation, Zmq for messaging and auxiliary libraries such as Boost).
The Python binding to Tango is PyTango. A functioning Tango system also requires a "Database device server" based on either MySQL
or MariaDB. This is well supported on many Linux based systems which may also be run in Virtual Machines such as VirtualBox.

Tango is less well supported natively on Windows and not at present under macOS.

For unsupported systems - or where Tango is not installed or run in a VM - the software can be built, run locally from source and built
into a Python package using Docker images to provide the Tango enviroment.

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

Building and running locally
----------------------------

To run the software locally without installation requires a locally installed and running
Tango installation - including a Tango database. Given this, and using SDPSubarray as an
example, the device server can be run as follows

he device be run from the local code folder - presently
sdp-prototype/src/tango_sdp{master|subarray} (without installation) using, for example::

    python SDPSubarray <instance name> [-v4]


or

.. code-block:: bash

    python SDPSubarray/SDPSubarray.py <instance name> [-v4]

where `<instance name>` is the name of a SDPSubarray device server instance
which has been registered with the tango database

A Python package with the SDPSubarray device can be installed locally with::

.. code-block:: bash

    python setup.py install

Once installed, the subarray device can be run with::

    SDPSubarray <instance name> [-v4]


To build and publish the python package::

.. code-block:: bash

    python setup.py sdist bdist_wheel
    twine upload dist/*

Docker Image
------------

To enable use of the SDP Device servers as part of the SKA Docker images containing the SDPSubarray
device are published to:

<https://nexus.engageska-portugal.pt/#browse/browse:docker>

With names such as (using subarray as an example)::

    nexus.engageska-portugal.pt/sdp-prototype/tangods_sdp_subarray


This image is automatically built and published by the CI script - on the master branch only! - but
can also be built manually if required using the Makefile:

.. code-block:: bash

  make build
  make push
  make push_version
  make push_latest

*Note: In order to push images to Nexus you will need to first authenticate
using the `docker login` command.*

These commands could also be used to push to <https://cloud.docker.com> - or other repositories - by
setting the following environment variables::

 DOCKER_REGISTRY_USER=skaorca
 DOCKER_REGISTRY_HOST=index.docker.io

or by passing them to `make`, eg::

    make DOCKER_REGISTRY_USER=skaorca DOCKER_REGISTRY_HOST=index.docker.io build
