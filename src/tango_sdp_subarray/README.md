# Tango SDPSubarray device & device server

## Quick start

### Run tests

Run tests using the `skaorca/ptango_ska_dev` container

```bash
make test
```

### Test interactively with a Tango facility and iTango

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
  d = DeviceProxy('mid_sdp/elt/subarray_00')
  ```
- Then query the state of the device with: 
  ```python
  d.state()
  ```
  When first intialised the device will report `'The device is in OFF state.'`
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
   
    
### Building and pushing new images

This should not be necessary as images are built from the CI script.

### Build the image

```bash
make build
```

### Push the image to docker hub

```bash
make push
make push_version
make push_latest
```
