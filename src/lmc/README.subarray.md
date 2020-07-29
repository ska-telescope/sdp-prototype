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
