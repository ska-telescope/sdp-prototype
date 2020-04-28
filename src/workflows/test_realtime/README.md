## Test Real-Time Workflow

The `test_realtime` workflow is designed to test the processing
controller logic concerning processing block dependencies.

The sequence of actions carried out by the workflow is:

* Claims processing block
* Sets processing block `status` to `'WAITING'`
* Waits for `resources_available` to be `True`
    * This is the signal from the processing controller that the workflow can run
* Sets processing block `status` to `'RUNNING'`
* Waits for scheduling block `status` to be set to `FINISHED`
    * This is the signal from the Subarray device that the scheduling block is finished
* Sets processing block `status` to `'FINISHED'`

The workflow makes no deployments.
