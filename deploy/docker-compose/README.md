# Docker-compose deployment files

## Quick start

Start a minimal tango facility consisting of a Tango database, and Tango
database device server:

```bash
make minimal
```

If this works correctly, `docker ps` should report two containers with names:
`tangodb`, and `databaseds`


Next start the SDP Master and SDP Subarray device server containers:

```bash
make start sdp_master
make start sdp_subarray
```

In order to test the deployment, start an `itango` shell:

```bash
make itango_shell
```

Get the list of registered devices by using the command:

```bash
lsdev
``` 

Create a connection to the SDPMaster device with:

```python
d = DeviceProxy('mid_sdp/elt/master')
```

Query the state of the SDPMaster with:

```python
d.status()
```

If successful, this should report `'The device is in ON state'`.


