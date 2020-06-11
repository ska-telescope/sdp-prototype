
Configuration Schema
====================

This is the schema of the configuration database, effectively the control plane of the SDP.

Design Principles
-----------------

- Uses a key-value store
- Uses watches on a key or range of keys to monitor for any updates
- Objects are represented as JSON
- We will likely want to define schemas and validation eventually, but
  for the moment this will be by example

Scheduling Block
----------------

Path `/sb/[sbi_id]`

Dynamic state information of the scheduling block instance.

Contents:
```javascript
{
    "id": "sbi-mvp01-20200425-00000",
    "max_length": 21600.0
    "scan_types": [
        { "id": "science", ... },
        { "id": "calibration", ... }
    ]
    "pb_realtime": [ "pb-mvp01-20200425-00000", ... ]
    "pb_batch": [ ... ]
    "pb_receive_addresses": "pb-mvp01-20200425-00000"
    "current_scan_type": "science"
    "status": "SCANNING"
    "scan_id": 12345
}
```

When the scheduling block instance is being executed, the `status` field is
set to the observation state (`obsState`) of the subarray. When the scheduling
block is ended, `status` is set to `FINISHED`.


Processing Block
----------------

Path: `/pb/[pb_id]`

Static definition of processing block information.

Contents:
```javascript
{
    "id": "pb-mvp01-20200425-00000",
    "sbi_id": "sbi-mvp01-20200425-00000",
    "workflow": {
        "type": "realtime",
        "id": "vis_receive",
        "version": "0.2.0"
    }
    "parameters": { ... }
}
```

There are two types of processing, real-time processing and batch (offline)
processing. Real-time processing starts immediately, as it directly
corresponds to an observation that is about to start. Batch processing will
be inserted into a scheduling queue managed by the SDP, where it will
typically be executed according to resource availability.

Valid types are `realtime` and `batch`. The workflow tag identifies the
workflow script version as well as the required underlying software (e.g.
execution engines, processing components). `...` stands for arbitrary
workflow-defined parameters.

### Processing Block State

Path: `/pb/[pb_id]/state`

Dynamic state information of the processing block. If it does not exist, the
processing block is still starting up.

Contents:
```javascript
{
    "resources_available": True
    "status": "RUNNING",
    "receive_addresses": [
        { "scan_type": "science", ... },
        { "scan_type": "calibration", ... },
    ]
}
```

Tracks the current state of the processing block. This covers both the
SDP-internal state (as defined by the Execution Control Data Model) as well as
information to publish via Tango for real-time workflows, such as the status
and receive addresses (for ingest).

### Processing Block Owner

Path: `/pb/[pb_id]/owner`

Identifies the process executing the workflow. Used for leader election/lock
as well as a debugging aid.

Contents:
```javascript
{
  "command": [
    "vis_receive.py",
    "pb-mvp01-20200425-00000"
  ],
  "hostname": "pb-mvp01-20200425-00000-workflow-2kxfz",
  "pid": 1
}
```
