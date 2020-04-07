# Processing Controller

## Introduction

The processing controller (PC) is the SDP service responsible for the
controlling the execution of processing blocks (PBs).

Each scheduling block instance (SBI) that SDP is configured to execute
contains a number of PBs, either real-time or batch. The real-time PBs run
simultaneously for the duration of the SBI. Batch PBs run after the SBI is
finished, and they may have dependencies on other PBs, both real-time and
batch.

The SDP architecture requires the PC to use a model of the available resources
to determine if a PB can be executed. This has not been implemented yet, so
real-time PBs are always executed immediately, and batch processing ones when
their dependencies are finished.

## Processing block and its state

The PB and its state are created in the configuration database by the subarray
Tango device when starting the SBI. Their paths are:
```bash
/pb/[pb_id]
/pb/[pb_id]/state
```
Once the PB is created it does not change. The state is empty when it is
created, and it is subsequently updated by the PC and the workflow.

The entries in the PB state relevant to the PC are `status` and
`resources_available`, for example:
```javascript
{
    "status": "WAITING",
    "resources_available": false
}
```
`status` is a string indicating the status of the workflow. Possible values
are:
* `STARTING`: set by the PC when it deploys the workflow, hereafter the
  workflow is responsible for setting `status`
* `WAITING`: workflow has started, but is waiting for resources to be
  available to execute its processing
* `RUNNING`: workflow is executing its processing
* `FINISHED`: workflow has finished its processing
* `FAILED`: set by the PC if it fails to deploy the workflow, or by the
  workflow in the case of a non-recoverable error

`resources_available` is a boolean set by the PC to inform the workflow
whether it has the resources available to start its processing. Although the
resource model is not implemented yet, this is used to control when batch PBs
with dependencies start.

## Behaviour

The behaviour of the PC is summarised as follows:

1. The PC uses HTTPS to retrieve the workflow definition file. This is a JSON
   file that specifies the mapping between the workflow ID and version, and a
   Docker container image. The workflow definition file is updated at regular
   intervals (the default is every 5 minutes).

2. If a PB is new, the PC will create the workflow deployment for it. A PB is
   deemed to be new if `status` is not present in the PB state and its
   workflow is not deployed. The PC sets `status` to `STARTING` and
   `resources_available` to `false`. If the workflow ID and version is not
   found in the definition file, the PC sets the `status` to `FAILED`.

3. If a PB's dependencies are all `FINISHED`, the PC sets
   `resources_available` to `true` to allow it to start executing. Real-time
   PBs do not have dependencies, so they start executing immediately.

4. The PC removes processing deployments (workflows and execution engines) not
   associated with any existing PB. This is used to clean up if a PB is
   deleted from the configuration DB. At present there is no mechanism for
   doing this (other than manually), but it might be used in future to abort
   a workflow execution.
