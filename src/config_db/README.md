SKA SDP Configuration Database
==============================

This is the frontend module for accessing SKA SDP configuration
information. It provides ways for SDP controller and processing
components to discover and manipulate the intended state of the
system.

At the moment this is implemented on top of `etcd`, a highly-available
database. This library provides primitives for atomic queries and
updates to the stored configuration information.

Installation
------------

Install from PyPI:

```bash
pip install ska-sdp-config
```

Basic Usage
-----------

Make sure you have a database backend accessible (etcd3 is supported
at the moment). Location can be configured using the `SDP_CONFIG_HOST`
and `SDP_CONFIG_PORT` environment variables. The defaults are
`127.0.0.1` and `2379`, which should work with a local `etcd` started
without any configuration.

This should give you access to SDP configuration information, for
instance try:

```python
import ska_sdp_config

config = ska_sdp_config.Config()

for txn in config.txn():
    for pb_id in txn.list_processing_blocks():
        pb = txn.get_processing_block(pb_id)
        print("{} ({}:{})".format(pb_id, pb.workflow['name'], pb.workflow['version']))
```

To read a list of currently active processing blocks with their
associated workflows.

Command line
------------

This package also comes with a command line utility for easy access to
configuration data. For instance run:

```bash
sdpcfg list values /pb/
```

To query all processing blocks.

Documentation
-------------

See [SKA developer
portal](https://developer.skatelescope.org/projects/sdp-prototype/en/latest/config_db.html)
for the API documentation.
