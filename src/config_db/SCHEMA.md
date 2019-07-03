
Configuration Schema
====================

This is the schema of the configuration database, effectively the control plane of the SDP.

Design Principles
-----------------

- We utilise a key-value store with watches
- Most objects are represented as JSON objects
- Exceptions are state and ownership fields, which we keep separate
- We will likely want to define schemas and validation eventually, but for the moment this will be by example

Processing Block
----------------

Path: `/pb/[pb_id]`

Static definition of processing block information. We might allow appending additional scan information, but most workflows will likely not support this.

Contents:
```javascript
{
    "id": "27062019_0001_ingest",
    "sbiId": "27062019_0001",
    "type": "realtime",
    "workflow": {
        "id": "vis_ingest",
        "tag": "0.1.0",
    }
    "parameters": { ... }
    "scanParameters:
    { "12345": { ... },
      "12346": { ... },
    }
}
```

Valid types are `realtime` and `batch`. The workflow tag identifies the workflow script version as well as the required underlying software (e.g. processing components, execution engines). `...` stands for arbitrary workflow-defined parameters.

Processing Block Status
-----------------------

Path: `/pb/[pb_id]/state`

Dynamic state information of the Processing Block.

Contents:
```javascript
{
    "state": "executing",
    "subarray": "ON",
    "obsState": "SCANNING",
}
```

Tracks the current state of the Processing Block. This covers both the internal state as well as the subarray state to report via Tango. At some point we might include 

Processing Block Owner
----------------------

Path: `/pb/[pb_id]/owner`

Processing Block Controller process identification. Used for leader election/lock as well as a debugging aid.

Contents: `controller-node-XYZ:123`

