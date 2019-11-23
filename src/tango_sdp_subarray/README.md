# SDPSubarray

This package provides a prototype of the SKA SDP Subarray Tango device server.

# Python Package

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

## Docker Image

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

## Running tests inside a `pytango_ska_dev` container

On a system where `pytango` cannot be installed natively, tests of this device
can also be run inside the `pytango_ska_dev` container with the following
command:

```bash
docker run -t --rm -v $(pwd):/app \
    nexus.engageska-portugal.pt/sdp-prototype/pytango_ska_dev:latest \
    python -m pytest \
    --pylint \
    --codestyle \
    --docstyle \
    --cov=SDPSubarray \
    --cov-report=term \
    --cov-config=./setup.cfg \
    -vv --gherkin-terminal-reporter    
```

or equivalently:

```bash
make test
```

## Testing interactively with a Tango facility and iTango

- Start a tango facility. See scripts in the `deploy/compose` folder for
  examples.
- Start the device. Assuming the tango databaseds service is started with name
  `databaseds` it is possible to register and start an SDPSubarray device with
  the following command:  
  ```bash
  docker run --rm -t --network=container:databaseds -e TANGO_HOST=localhost:10000 
    nexus.engageska-portugal.pt/sdp-prototype/tangods_sdp_subarray:latest
  ```
  This is because the SDPSubarray will register itself into the database, if it
  detects that this has not already been done. If started correctly you should
  see a massage with:
  ```bash
  Ready to accept request
  ```
- The Subarray device can be tested interactively using an iTango shell.
- First, obtain a handle to the device with: 
  ```python
  d = DeviceProxy('mid_sdp/elt/subarray_1')
  ```
  To obtain handle for the second device:
  ```
  c = DeviceProxy('mid_sdp/elt/subarray_2')
  ```
- Then query the state of the device with: 
  ```python
  d.state()
  ```
  When first initialised the device will report `'The device is in OFF state.'`
- To query the obsState attribute: 
  ```python
  d.obsState
  ```
  This will return `<obsState.IDLE: 0>`
- The obsState can be set by the int enum value or a string as follows: 
  ```python
  d.obsState = 1
  d.obsState = 'CONFIGURING'  
  ```  
- To list other commands and attributes exposed by the SDPSubarray device: 
  ```python
  d.command_list_query()
  d.attribute_list_query()
  ```

## API Documentation

See [SKA developer
portal](https://developer.skatelescope.org/projects/sdp-prototype/en/latest/sdp_subarray.html)
for the API documentation.
