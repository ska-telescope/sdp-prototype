# ORCA Docker base and development images

This folder contains a number of experimental Docker images currently used to
test and build ORCA components and modules.

## pytango

This folder contains PyTango Docker base image(s).


## pytango-orca-dev

This folder contains a development + test environment tango devices developed in
this project.

##  ska-lmc-baseclasses

This folder contains SKA LMC baseclasses Docker base image(s).


## Quick-start

***TODO! More description here!***

These images are built by the gitlab CI whenever a change is made. New versions
of the image are published by means of creating a git tag with the pattern:

```
<image name>==<image tag>
```

For example:

```bash
git tag -a pytango-9.3.0==buster-slim -m "<message>"
git tag -a ska-lmc-baseclasses==devel-buster-slim -m "<message>"
git tag -a pytango-orca-dev==0.3.0-buster-slim -m "<message>"
```

Published images for the latest versions of these dockerfiles can be found in
the [SKA nexus repository](https://nexus.engageska-portugal.pt/#browse/browse:docker:v2%2Fsdp-prototype)
