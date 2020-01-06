Design Overview
===============

Introduction
------------

This prototype is a partial implementation of the SDP software architecture
adopted by the SKA. Its purpose is to implement and test parts of the
architecture to de-risk the construction of the SDP.

The most recent version of the complete SDP architecture can be found in
the `SDP Consortium close-out documentation
<http://ska-sdp.org/publications/sdp-cdr-closeout-documentation>`_. The
architecture is intended to be a living document that evolves alongside its
implementation, so it will eventually be available in a form that can more
readily be changed.


Components
----------

.. figure:: ../images/sdp_system_cc.svg
   :align: center

   Component and connector diagram of the prototype implementation.

**Execution Control**:

* The **SDP Master Tango Device** is intended to provide the top-level
  control of SDP services. The present implementation does very little,
  apart from executing internal state transitions in response to Tango
  commands. As shown in the diagram, it does not yet have a connection
  to the Configuration Database.

* The **SDP Subarray Tango Devices** control the processing associated
  with SKA Subarrays. When a Processing Block is submitted to SDP
  through one of the devices, it is added to the Configuration Database.
  During the execution of the Processing Block, the device publishes the
  status of the Processing Block through its attributes.

* The **Processing Controller** controls the execution of Processing
  Blocks. It detects them by monitoring the Configuration Database. To
  execute a Processing Block, it requests the deployment of the
  corresponding Workflow by creating an entry in the Configuration
  Database. Only real-time Workflows are supported at this time.

* The **Configuration Database** is the central store of configuration
  information in the SDP. It is the means by which the components
  communicate with each other.

**Platform**:

* The **Helm Deployer** is the service that the Platform uses to respond
  to deployment requests in the Configuration Database. It makes
  deployments by installing Helm charts into a Kubernetes cluster.

* **Kubernetes** is the underlying mechanism for making dynamic
  deployments of Workflows and Execution Engines.

**Processing Block Deployment**:

* A **Workflow** controls the execution of a Processing Block (in the
  architecture it is called the Processing Block Controller). Workflows
  connect to the Configuration Database to retrieve the parameters defined
  in the Processing Block and to request the deployment of Execution
  Engines.

* **Execution Engines** are the means by which Workflows process the data.
  They typically enable distributed execution of processing functions,
  although Workflows may use a single process as a serial Execution
  Engine.
