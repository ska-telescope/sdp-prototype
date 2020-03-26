
Setting up a local development environment
==========================================

Kubernetes
----------

You will need Kubernetes installed. [Docker for
Desktop](https://www.docker.com/products/docker-desktop) includes a
workable one-node Kubernetes installation - just need to activate it
in the settings. Alternatively, you can install
[Minikube](https://minikube.sigs.k8s.io) or
[microk8s](https://microk8s.io).

Docker and Minikube
-------------------

Docker runs containers in a VM on Windows and macOS, and by default Minikube
does this on all systems. The VM needs at least 3 GB of memory to run the
SDP prototype. In Docker this can be found in the settings. For Minikube you
need to specify the amount of memory on the command line when starting a new
instance:

.. code-block::

    $ minikube start --memory='4096m'

Micro8ks
--------

Canonical supports **microk8s** for Ubuntu Linux distributions - and it
is also available for many other distributions (42 according to
[this](https://github.com/ubuntu/microk8s#accessing-kubernetes)). It
gives a more-or-less 'one line' Kubernetes installation

- To install type `sudo snap install microk8s --classic`
    -   Tested with version 1.15. This specific version can be installed using
        `snap refresh --classic --channel=1.15/stable microk8s`.
- `microk8s.start` will start the Kubernetes system
- `microk8s.enable dns` is required for the SDP prototype
- `microk8s.status` should show that things are active
- microk8s.inspect shows the report in more detail
- microk8s will install `kubectl` as `microk8s.kubectl`. Unless you have
  another Kubernetes installation in parallel you may wish to set up an
  alias with `sudo snap alias microk8s.kubectl kubectl`

If you have problems with pods not communicating, you may need to do
`sudo iptables -P FORWARD ACCEPT` (`microk8s.inspect` should be able
to diagnose this for you).


Helm
----

Furthermore you will need to install the Helm utility. It is available
from most typical package managers, see [Using
Helm](https://helm.sh/docs/using_helm/). You can use either version 2
or version 3 of Helm. Instructions are given below for both.

It may be available in the 'snap' installation system (eg. on
recent Ubuntu installations)

If you are using Helm 2, you will typically need to initialise it
(this will create the 'Tiller' controller):

.. code-block::

    $ helm init


Helm 3 does not use Tiller, but if you are using it for the first time,
you need to add the stable chart repository:

.. code-block::

    $ helm repo add stable https://kubernetes-charts.storage.googleapis.com/


Install the etcd operator
-------------------------
The SDP Configuration database is implemented on top of `etcd`, a strongly consistent, distributed
key-value store that provides a reliable way to store data that needs to be accessed by a
distributed system or cluster of machines.  etcd is the primary datastore of Kubernetes; storing and
replicating all Kubernetes cluster state. As a critical component of a Kubernetes cluster having a
reliable automated approach to its configuration and management is imperative.

While this is also the database system used by kubernetes it is currently necessary to
install etcd using the instructions below.

We are not creating an etcd cluster ourselves, but instead leave it to
an 'operator' that needs to be installed first. The etcd operator enables users to configure and
manage the complexities of etcd using simple declarative configuration that will create, configure,
and manage etcd clusters.

For Helm 2, simply execute:

.. code-block::

    $ helm install stable/etcd-operator -n etcd


or for Helm 3:

.. code-block::

    $ helm install etcd stable/etcd-operator


If you now execute:

.. code-block::

    $ kubectl get pod --watch


You should eventually see an pod called
`etcd-etcd-operator-etcd-operator-[...]` in 'Running' state (yes,
Helm is exceedingly redundant with its names). If not wait a bit, if
you try to go to the next step before this has completed there's a
chance it will fail.


Setting up on Windows
---------------------

Install and configure tools
+++++++++++++++++++++++++++


The hypervisor Hyper-V is built-in on Windows 10 and just needs to be enabled via settings and a reboot.
Full details are here.

Install minikube, kubectl, helm 3 and put the executables in the path.

Configure minikube to use 4GB of memory:

>minikube config set memory 4096

This creates a file .minikube/config.config.json that looks like this:

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

    > kubectl logs sdp-prototype-sdp-devices-845969f6b8-s9nhf -c dsconfig

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

There are a lot of different suggestions on the web of how to fix it, most of which didn't work for me.
This one did:

Create a file .gitattributes in the top-level project with these contents:

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