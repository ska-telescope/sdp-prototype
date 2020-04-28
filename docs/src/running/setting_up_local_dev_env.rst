
Setting up a local development environment
==========================================

Kubernetes
----------

You will need Kubernetes installed. `Docker for Desktop
<https://www.docker.com/products/docker-desktop>`_ includes a workable
one-node Kubernetes installation - you just need to activate it in the
settings. Alternatively, you can install
`Minikube <https://minikube.sigs.k8s.io>`_ or
`microk8s <https://microk8s.io>`_.

Docker and Minikube
+++++++++++++++++++

Docker runs containers in a VM on Windows and macOS, and by default Minikube
does this on all systems. The VM needs at least 3 GB of memory to run the
SDP prototype. In Docker this can be found in the settings. For Minikube you
need to specify the amount of memory on the command line when starting a new
instance:

.. code-block::

    $ minikube start --memory='4096m'

Micro8ks
++++++++

Canonical supports microk8s for Ubuntu Linux distributions - and it
is also available for many other distributions (42 according to
`this <https://github.com/ubuntu/microk8s#accessing-kubernetes>`_). It
gives a more-or-less 'one line' Kubernetes installation

- To install type ``sudo snap install microk8s --classic``
- ``microk8s.start`` will start the Kubernetes system
- ``microk8s.enable dns`` is required for the SDP prototype
- ``microk8s.status`` should show that things are active
- ``microk8s.inspect`` shows the report in more detail
- microk8s will install ``kubectl`` as ``microk8s.kubectl``. Unless you have
  another Kubernetes installation in parallel you may wish to set up an
  alias with ``sudo snap alias microk8s.kubectl kubectl``

If you have problems with pods not communicating, you may need to do
``sudo iptables -P FORWARD ACCEPT`` (``microk8s.inspect`` should be able
to diagnose this for you).

Helm
----

Furthermore you will need to install the Helm utility. It is available
from most typical package managers, see `Introduction to Helm
<https://helm.sh/docs/intro/>`_. We recommend using Helm 3.

If you are using Helm 3 for the first time, you need to add the stable
chart repository:

.. code-block::

    $ helm repo add stable https://kubernetes-charts.storage.googleapis.com/


Setting up on Windows
---------------------

Install and configure tools
+++++++++++++++++++++++++++

The hypervisor Hyper-V is built-in on Windows 10 and just needs to be enabled
via settings and a reboot.

Install Minikube, kubectl, Helm 3 and put the executables in the path.

Configure Minikube to use 4GB of memory:

.. code-block::

    > minikube config set memory 4096

This creates a file ``.minikube/config/config.json`` that looks like this:

.. code-block:: json

    {
      "dashboard": true,
      "memory": 4096
    }

Fix the line ends
+++++++++++++++++

A git clone will by default automatically convert all line ends to Windows format.
This causes the SDP devices pod to fail to start. The command to see the error and
the resulting message looks like this:

.. code-block::

    > kubectl logs test-sdp-prototype-sdp-devices-845969f6b8-s9nhf -c dsconfig

    wait-for-it.sh: waiting 30 seconds for databaseds-tango-base-sdp-prototype:10000
    wait-for-it.sh: databaseds-tango-base-sdp-prototype:10000 is available after 0 seconds
    Traceback (most recent call last):
    File "/usr/local/bin/json2tango", line 11, in <module>
    sys.exit(main())
    File "/usr/local/lib/python2.7/dist-packages/dsconfig/json2tango.py", line 88, in main
    with open(json_file) as f:
    IOError: [Errno 2] No such file or directory: 'data/sdp-devices.json\r'
    data/sane-dsconfig.sh: line 7: syntax error near unexpected token `fi'
    data/sane-dsconfig.sh: line 7: `fi'

To fix this, create a file .gitattributes in the top-level project with these contents:

.. code-block::

    *.json text eol=lf
    *.sh text eol=lf
    *.yml text eol=lf
    *.yaml text eol=lf

Then run the commands:

.. code-block::

    > git rm --cached -r .
    > git reset --hard
    > git add --renormalize .
