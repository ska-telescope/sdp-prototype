# Experimental ORCA Docker development image

Extends the ORCA pytango SLA base image with development and testing packages.

This image can also be used with PyCharm Pro to provide a Python interpreter.

# Quick start

Build with:

```bash
make
```

Publish with: 
```bash
make publish
```

Update the version number in the `release` file.

Update the `pipenv` lock file with:

```bash
pipenv lock -v --clear --dev 
```


## TODO

- Add `make piplock` target to update the `Pipfile.lock` file
- Update to Python 3.6 or 3.7 (currently limited by libboost-python on stretch) 
- Use the ska-docker images instead!

