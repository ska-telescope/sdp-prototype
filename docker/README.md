# Docker Images used to build ORCA services

This folder contains a number of experimental Docker images currently used to
test and build ORCA SDP Tango devices.

- `pytango_build` : Debian Buster, Python 3.7, Pytango==9.3.0
- `pytango_base` : Debian Buster, Python 3.7, Pytango==9.3.0
- `pytango_ska_base` : Debian Buster, Python 3.7, Pytango==9.3.0, lmcbaseclasses
- `pytango_ska_dev` : Extends `pytango_ska_base` with Python testing packages

## TODO

- Complete rewrite of these images are pretty badly written at the moment! 
- The development image should not run as root by default
- Publish key build layers to support build caching using the `--target` build
  option. See
  <https://andrewlock.net/caching-docker-layers-on-serverless-build-hosts-with-multi-stage-builds---target,-and---cache-from/>
- Remove these images in favour of
  [`ska-docker`](https://github.com/ska-telescope/ska-docker) images.

## Quick start

- `cd` into one of the subdirectories
- Build the image with `make build`
- Push the image to a docker registry `make push`
- To push the `:latest` tag use `make push_latest`
- To push a version tag without the git SHA use `make push_version` 
- Optionally specify DOCKER_REGISTRY_HOST & DOCKER_REGISTRY_USER. eg. `make
  DOCKER_REGISTRY_HOST=nexus.engageska-portugal.pt
  DOCKER_REGISTRY_USER=ska-prototype <build, push>` will build and push images
  to the SKA nexus registry. 
