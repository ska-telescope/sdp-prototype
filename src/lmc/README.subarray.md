### Python Package

A Python package with the SDPSubarray device can be installed with:

```bash
python setup.py install
```

and tested with:

```bash
python setup.py test
```

Once installed, the subarray device can be run with:

```bash
SDPSubarray <instance name> [-v4]
```

where `<instance name>` is the name of a SDPSubarray device server instance
which has been registered with the tango database

The device can also be run from the local code folder (without installation)
using:

```bash
python SDPSubarray <instance name> [-v4]
```

or

```bash
python SDPSubarray/SDPSubarray.py <instance name> [-v4]
```

To build and publish the python package:

```bash
python setup.py sdist bdist_wheel
twine upload dist/*
```

### Docker Image

A Docker image containing the SDPSubarray device is published to:

<https://nexus.engageska-portugal.pt/#browse/browse:docker>

With the name:

```
nexus.engageska-portugal.pt/sdp-prototype/tangods_sdp_subarray
```

This image is built and published by the CI script but can also be built
manually if required with:

```bash
make build
make push
make push_version
make push_latest
```

*Note: In order to push images to Nexus you will need to first authenticate
using the `docker login` command.*

*Note: These commands can also be used to push to <https://cloud.docker.com> by
setting the following environment variables:*
```bash
DOCKER_REGISTRY_USER=skaorca
DOCKER_REGISTRY_HOST=index.docker.io
```
*or by passing them to `make`, eg:*
```bash
make DOCKER_REGISTRY_USER=skaorca DOCKER_REGISTRY_HOST=index.docker.io build
```

### Running tests inside a `pytango_ska_test` container

On a system where `pytango` cannot be installed natively, tests of this device
can also be run inside the `pytango_ska_test` container with the following
command:

```bash
docker run -t --rm -v $(pwd):/app \
    nexus.engageska-portugal.pt/sdp-prototype/pytango_ska_test:latest \
    python3 -m pytest \
    --pylint \
    --pycodestyle \
    --pydocstyle \
    --cov=SDPSubarray \
    --cov-report=term \
    --cov-config=./setup.cfg \
    -vv --gherkin-terminal-reporter
```

or to run the test directly inside the container:

```bash
docker run --rm -it -v $(pwd):/app nexus.engageska-portugal.pt/sdp-prototype/pytango_ska_test:latest
```

this will create a bash session in the container and then run:

```bash
python3 setup.py test
```

or equivalently:

```bash
make test
```

### Testing interactively with a Tango facility and iTango

Start a tango facility by running

```bash
kubectl exec -it itango-tango-base-sdp-prototype /venv/bin/itango3
```

First, obtain a handle to the device with:

```python
d = DeviceProxy('mid_sdp/elt/subarray_1')
```

To obtain handle for the second device:

```python
c = DeviceProxy('mid_sdp/elt/subarray_2')
```

Then query the state of the device with:

```python
d.state()
```

When first initialised the device will report `'The device is in OFF state.'`

To query the obsState attribute:

```python
d.obsState
```

This will return `<obsState.IDLE: 0>`

Create a configuration string for the scheduling block instance:
```
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
        "workflow": {"type": "batch", "id": "ical", "version": "0.1.0"},
        "parameters": {},
        "dependencies": [
          {"pb_id": "pb-mvp01-20200425-00000", "type": ["visibilities"]}
        ]
      },
      {
        "id": "pb-mvp01-20200425-00003",
        "workflow": {"type": "batch", "id": "dpreb", "version": "0.1.0"},
        "parameters": {},
        "dependencies": [
          {"pb_id": "pb-mvp01-20200425-00002", "type": ["calibration"]}
        ]
      }
    ]
  }
  '''
```
Note that the link map for each scan type will be included in this configuration when the format is decided.

The scheduling block instance is started by the AssignResources command:

```python
d.AssignResources(config_sbi)
```

The subarray should now be ON, but the obsState remains IDLE.

Before executing a scan, we need to configure the scan type. This is done by passing the scan type to the
Configure command:

```python
d.Configure('{"scan_type": "science"}')
```

which changes the obsState to CONFIGURING and then to READY.

To start a scan, we need to pass the scan ID to the Scan command:

```python
d.Scan('{"id": 1}')
```

which changes the obsState to SCANNING.

The scan is ended with the EndScan command:

```python
d.EndScan()
```

which changes the obsState to READY again.

Scan and EndScan can be called any number of times to execute an instance of the configured scan type. The scan ID
should be unique for each scan, although SDP does not check this at present.

The scan type can be changed by executing the Configure command again with a different scan type. This should be
one of the predefined scan types, although there is an option to pass new scan types in the Configure command.

To do this, create a new configuration string that includes the new_scan_types entry:

```python
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
```

and pass that to the Configure command:

```python
d.Configure(config_newscantype)
```

The Reset command clears the scan type:

```python
d.Reset()
```

which changes the obsState to IDLE.

Finally, when the obsState is IDLE, the scheduling block instance is ended by the ReleaseResources command:

```python
d.ReleaseResources()
```

after which the subarray should be OFF.

To list other commands and attributes exposed by the SDPSubarray device:

```python
d.command_list_query()
d.attribute_list_query()
```

### Testing from a branch

If you have pushed your changes to a branch in the GitHub repository, and the Docker image has
been built by the CI pipeline, you can test it by overriding the version number in the
`sdp-prototype` Helm  chart. To do this, create a file called `test.yaml` inside the charts
directory containing:

```bash
tangods:
  subarray:
    version: <version-number>-<git-hash>
```

where `<version-number>` is the current version number and `<git-hash>` is the latest git hash of the branch.
Then install the prototype with (Helm 3 syntax):

```bash
helm install test sdp-prototype -f test.yaml
```
