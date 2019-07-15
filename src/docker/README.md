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
