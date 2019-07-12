# Docker-compose deployment files

## Quick start

Start a minimal tango facility consisting of a Tango database, and Tango
database device server:

```bash
make up
```

Start the SDP Master device server container:

```bash
make sdp_master
```

Start the SDP Subarray device server container:

```bash
make sdp_subarray
```

Start an `itango` shell:

```bash
make itango_shell
```


