# Docker Images used to build ORCA services

This folder contains a number of experimental Docker images currently used to
test and build ORCA SDP Tango devices.

- `pytango_base` : Debian Buster, Python 3.7, Pytango==9.3.0
- `pytango_ska_base` : Debian Buster, Python 3.7, Pytango==9.3.0, lmcbaseclasses
- `pytango_ska_dev` : Extends `pytango_ska_base` with Python testing packages

## TODO

- Complete rewrite of these images are pretty badly written at the moment! 
- The development image should not run as root by default
- Remove these images in favour of 
  [`ska-docker`](https://github.com/ska-telescope/ska-docker) images.

## Quick start

- `cd` into one of the subdirectories
- Build the image with `make build`
  - Optionally specify `DOCKER_BUILD_ARGS` eg `make 
    DOCKER_BUILD_ARGS="--no-cache" build`
- Push the image to a docker registry `make push`
  - Optionally specify a `DOCKER_REGISTRY_HOST` eg. `make
    DOCKER_REGISTRY_HOST=nexus.engageska-portugal.pt push`.
