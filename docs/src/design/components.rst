Components
==========


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
  Database.

* The **Configuration Database** is the central store of configuration
  information in the SDP. It is the means by which the components
  communicate with each other.

**Platform**:

* The **Helm Deployer** is the service that the Platform uses to respond
  to deployment requests in the Configuration Database. It makes
  deployments by installing Helm charts (a collection of files that
  describe a related set of Kubernetes resources) into a Kubernetes cluster.

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
