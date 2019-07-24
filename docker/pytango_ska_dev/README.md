# Experimental ORCA Docker development image

Extends the ORCA `pytango_ska_base` image with development and testing
packages.

This image can also be used with PyCharm Pro to provide a Python interpreter.

Eventually this should be deprecated in favour of a `ska-docker` base image.

## Quick start

If making a change, update the version number in the `release` file.

Then, if the Pipenv file has been changed:

Build with: 

```bash
make clean_build
```

or, if only the Dockerfile has changed:

```bash
make build
```

Publish (to dockerhub) with:
 
```bash
make push
```

To remove old `skaorca/pytango_ska_dev` image tags:

```bash
make rm_old
```

To remove all `skaorca/pytango_ska_dev` image tags

```bash
make rm
```
