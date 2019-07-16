# Tango SDPMaster device & device server

## Quick start

### Run tests

Run tests using the `skaorca/ptango_ska_dev` container

```bash
make test
```

### Build the image

```bash
make build
```

### Push the image to docker hub

```bash
make push
```

## Test interactively with a Tango facility

- Start the `tangods` and `databaseds` containers. This can be done by using the
  command `make up` in the `deploy/docker-compose`
- Register devices with the database using `make register`
- Start the SDPMaster devices using `make start`
- Start a iTango container with make start itango from the
  `deploy/docker-compose` folder
- Obtain an `itango` prompt with `docker exec -it itango itango3` from the
  `deploy/docker-compose` folder
- check the device list with `lsdev`
- get a device handle with `d = DeviceProxy('mid_sdp/elt/master')`
- check the device state with `d.State()`... this should be `DevState.ON`
- check the operatingState with `d.OperatingState`
- to get command list `d.get_command_list()`
- to get attribute list `d.get_attribute_list()`
