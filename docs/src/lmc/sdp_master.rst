SDP Master Device
=================

Introduction
------------

The SDP Master Tango device is designed to provide the overall control of the
SDP. The commands it receives cause the other SDP services to be stopped or
started, and its attributes report on the overall state of the system.

The present implementation of the SDP Master device does very little apart from
performing the state transitions in response to commands.


Interface
---------

Attributes
^^^^^^^^^^

Device attributes:

============== ====== ========== ============================ ===========
Attribute      Type   Read/Write Values                       Description
============== ====== ========== ============================ ===========
version        String Read       Semantic version             Master device server version
-------------- ------ ---------- ---------------------------- -----------
heathState     Enum   Read       :ref:`master_healthstate`    SDP health state
============== ====== ========== ============================ ===========

.. _master_healthstate:

healthState values
""""""""""""""""""

============ ===========
healthState  Description
============ ===========
OK (0)
------------ -----------
DEGRADED (1)
------------ -----------
FAILED (2)
------------ -----------
UNKNOWN (3)
============ ===========


Commands
^^^^^^^^

The commands change the device state as described below, but at present they
have no other effect on SDP.

======= ============= =========== ======
Command Argument type Return type Action
======= ============= =========== ======
On      None          None        Set device state to ON
------- ------------- ----------- ------
Disable None          None        Set device state to DISABLE
------- ------------- ----------- ------
Standby None          None        Set device state to STANDBY
------- ------------- ----------- ------
Off     None          None        Set device state to OFF
======= ============= =========== ======


Python API
----------

.. automodule:: ska_sdp_lmc.master
    :members:
    :undoc-members:
