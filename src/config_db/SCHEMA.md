
Configuration Schema
====================

This is the schema of the configuration database, effectively the control plane of the SDP.

Design Principles
-----------------

- We utilise a key-value store with watches
- Most objects are represented as JSON objects
- Exceptions are state and ownership fields, which we keep separate
- We will likely want to define schemas and validation eventually, but
  for the moment this will be by example

Processing Block
----------------

Path: `/pb/[pb_id]`

Static definition of processing block information. We might allow
appending additional scan information, but most workflows will likely
not support this.

Contents:
```javascript
{
    "id": "realtime-27062019-0001",
    "sbiId": "27062019_0001",
    "workflow": {
        "type": "realtime",
        "id": "vis_ingest",
        "version": "0.1.0"
    }
    "parameters": { ... }
    "scanParameters":
    { 
        "12345": { ... },
        "12346": { ... }
    }
}
```

Valid types are `realtime` and `batch`. The workflow tag identifies
the workflow script version as well as the required underlying
software (e.g. processing components, execution engines). `...` stands
for arbitrary workflow-defined parameters.

### Processing Block Status

Path: `/pb/[pb_id]/state`

Dynamic state information of the Processing Block. If it doesn't
exist, the processing block is still in "startup" state.

Contents:
```javascript
{
    "state": "executing",
    "subarray": "ON",
    "obsState": "SCANNING",
    "receiveAddresses": {
        "<phase_bin>": {
            "<channel_id>": ["<ip>", <port>],
            ...
        }
    }
}
```

Tracks the current state of the Processing Block. This covers both the
SDP-internal state (as defined by the Execution Control Data Model) as
well as the subarray state to report via Tango for real-time
processing blocks (as defined by SDP-to-TM ICD).

This is also where further attributes to publish via Tango are going
to get populated, such as receiver addresses for ingest.

### Processing Block Owner

Path: `/pb/[pb_id]/owner`

Processing Block Controller process identification. Used for leader election/lock as well as a debugging aid.

Contents: `controller-node-XYZ:123`

Subarray
--------

Path: `/subarray/[subarray_id]`

Definition and state of a telescope sub-array. Especially used for
tracking attributes that might be required even if the subarray is not
currently active (like `adminMode`).

Contents:
```javascript
{
    "adminState": "ONLINE",
    "command": "Scan",
    "currentPb": "[pb_id]",
}
```

The command is the last command given by the TANGO interface. This
might cause a state change of the associated processing block.
