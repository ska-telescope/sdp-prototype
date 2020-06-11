# Batch Imaging Workflow

The `batch_imaging` workflow is a proof-of-concept of integrate a scientific
workflow with the SDP prototype. It simulates visibilities and images them using
RASCIL with Dask as an execution engine.

The workflow simulates SKA1-Low visibility data in a range of hour angles from
-30 to 30 degrees and adds phase errors. The visibilities are then calibrated
and imaged using the ICAL pipeline.

The workflow creates buffer reservations for storing the visibilities and
images.

## Parameters

The workflow parameters are:

* `n_workers`: number of Dask workers to deploy
* `freq_min`: minimum frequency (in hertz)
* `freq_max`: maximum frequency (in hertz)
* `nfreqwin`: number of frequency windows
* `ntimes`: number of time samples
* `rmax`: maximum distance of stations to include from array centre (in metres)
* `ra`: right ascension of the phase centre (in degrees)
* `dec`: declination of the phase centre (in degrees)
* `buffer_vis`: name of the buffer reservation to store visibilities
* `buffer_img`: name of the buffer reservation to store images

For example:

```json
{
  "n_workers": 4,
  "freq_min": 0.9e8,
  "freq_max": 1.1e8,
  "nfreqwin": 8,
  "ntimes": 5,
  "rmax": 750.0,
  "ra": 0.0,
  "dec": -30.0,
  "buffer_vis": "buff-pb-mvp01-20200523-00001-vis",
  "buffer_img": "buff-pb-mvp01-20200523-00001-img"
}
```

## Running the workflow

If using Minikube, make sure to increase the memory size (minimum 16 GB):

```console
minikube start --memory=16g
```

Once the sdp-prototype is running, start a iTango shell with:

```console
kubectl exec -it itango-tango-base-sdp-prototype -- /venv/bin/itango3
```

First, obtain a handle to a subarray device with:

```python
d = DeviceProxy('mid_sdp/elt/subarray_1')
```

Create a configuration string for the scheduling block instance. This contains
one real-time processing block, which uses the `test_realtime` workflow as a
placeholder, and one batch processing block containing the `batch_imaging`
workflow, which uses the example parameters from above:

```python
config_sbi = '''
{
  "id": "sbi-mvp01-20200523-00000",
  "max_length": 21600.0,
  "scan_types": [
    {
      "id": "science",
      "channels": [
        {"count": 8, "start": 0, "stride": 1, "freq_min": 0.9e8, "freq_max": 1.1e8, "link_map": [[0,0]]}
      ]
    }
  ],
  "processing_blocks": [
    {
      "id": "pb-mvp01-20200523-00000",
      "workflow": {"type": "realtime", "id": "test_realtime", "version": "0.2.0"},
      "parameters": {}
    },
    {
      "id": "pb-mvp01-20200523-00001",
      "workflow": {"type": "batch", "id": "batch_imaging", "version": "0.1.0"},
      "parameters": {
        "n_workers": 4,
        "freq_min": 0.9e8,
        "freq_max": 1.1e8,
        "nfreqwin": 8,
        "ntimes": 5,
        "rmax": 750.0,
        "ra": 0.0,
        "dec": -30.0,
        "buffer_vis": "buff-pb-mvp01-20200523-00001-vis",
        "buffer_img": "buff-pb-mvp01-20200523-00001-img"
      },
      "dependencies": [
        {"pb_id": "pb-mvp01-20200523-00000", "type": ["none"]}
      ]
    }
  ]
}
'''
```

The scheduling block instance is created by the `AssignResources` command:

```python
d.AssignResources(config_sbi)
```

You can run the subarray commands as normal, but the batch processing does not
start until you end the real-time processing with the `ReleaseResources`
command:

```python
d.ReleaseResources()
```

You can watch the pods and persistent volume clams (for the buffer reservations)
being deployed with:

```console
watch kubectl get pod,pvc -n sdp
```

At this stage you should see a pod called
`proc-pb-mvp01-20200523-00001-workflow-...` and the status is `RUNNING`. To see
the logs, run:

```console
kubectl logs <pod-name> -n sdp
```

and it should look like this:

```console
INFO:batch_imaging:Claimed processing block pb-mvp01-20200523-00001
INFO:batch_imaging:Waiting for resources to be available
INFO:batch_imaging:Resources are available
INFO:batch_imaging:Creating buffer reservations
INFO:batch_imaging:Deploying Dask EE
INFO:batch_imaging:Running simulation pipeline
INFO:batch_imaging:Running ICAL pipeline
...
```

## Accessing the data

The buffer reservations are realised as Kubernetes persistent volume claims.
They should have persistent volumes created to satisfy them automatically. The
name of the corresponding persistent volume is in the output of:

```console
kubectl get pvc -n sdp
```

The location of the persistent volume in the filesystem is shown in the output
of:

```console
kubectl describe pv <pv-name>
```

If you are running Kubernetes with Minikube in a VM, you need to log in to it
first to gain access to the files:

```console
minikube ssh
```
