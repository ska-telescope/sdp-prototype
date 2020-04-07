# Docker Images used to build SIM services

This folder contains a number of experimental Docker images currently used to
test and build SIM SDP Tango devices.

- `pytango_build` : Debian Buster, Python 3.7, Pytango==9.3.0
- `pytango_base` : Debian Buster, Python 3.7, Pytango==9.3.0
- `pytango_ska_base` : Debian Buster, Python 3.7, Pytango==9.3.0, lmcbaseclasses
- `pytango_ska_dev` : Extends `pytango_ska_base` with Python testing packages [OLD]
- `pytango_ska_test` : with Python testing packages [LATEST]


## Quick start

- `cd` into one of the subdirectories
- Build the image with `make build`
- Push the image to a docker registry `make push`
- To push the `:latest` tag use `make push_latest`
- To push a version tag without the git SHA use `make push_version` 

## Python packages to the docker image

- Add python packages to the requirements.txt file
- Update the version in the release file, before building and pushing the image
