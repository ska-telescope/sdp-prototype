SDP Master Device
=================

Introduction
------------

The SDP Master Tango device is designed to provide the overall control of the
SDP. The commands it receives cause the other SDP services to be stopped or started,
and its attributes report on the overall state of the system.

The present implementation of the SDP Master device does very little apart
from performing the internal state transitions in response to commands.


Interface
---------

Attributes
^^^^^^^^^^

Device attributes:

============== ====== ========== ============================ ===========
Attribute      Type   Read/Write Values                       Description
============== ====== ========== ============================ ===========
serverVersion  String Read       Semantic version             Master device server version
-------------- ------ ---------- ---------------------------- -----------
OperatingState Enum   Read       :ref:`master_operatingstate` SDP operating state
-------------- ------ ---------- ---------------------------- -----------
heathState     Enum   Read       :ref:`master_healthstate`    SDP health state
============== ====== ========== ============================ ===========

.. _master_operatingstate:

OperatingState values
"""""""""""""""""""""

============== ===========
OperatingState Description
============== ===========
INIT (0)       The SDP Master is available, but one or more of the persistent SDP
               services are still starting up. During this state SDP will not accept
               scheduling commands.
-------------- -----------
ON (1)         Reported when the SDP is fully operational and will accept commands
               which schedule processing.
-------------- -----------
DISABLE (2)    SDP is in a drain state with respect to processing. In this state
               SDP will allow any executing Processing Blocks to complete, but not
               accept new scheduling commands.
-------------- -----------
STANDBY (3)    Reported when the SDP is in low-power mode and not accepting any new
               scheduling commands and is no longer executing any Processing Blocks.
-------------- -----------
ALARM (4)      SDP is operational but an alarm condition has been triggered.
-------------- -----------
FAULT (5)      SDP has encountered an unrecoverable error that requires human
               intervention.
-------------- -----------
OFF (6)        Reported when only the SDP Master device (and TBD other critical
               Execution Control services) are running but the rest of SDP is
               powered off. What constitutes the rest of SDP here is still TBD.
-------------- -----------
UNKNOWN (7)    Reported when the state can not be obtained.
============== ===========

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

The commands change the OperatingState attribute as described below, but at
present they have no other effect on SDP.

======= ============= =========== ======
Command Argument type Return type Action
======= ============= =========== ======
on      None          None        Set OperatingState to ON
------- ------------- ----------- ------
disable None          None        Set OperatingState to DISABLE
------- ------------- ----------- ------
standby None          None        Set OperatingState to STANDBY
------- ------------- ----------- ------
off     None          None        Set OperatingState to OFF
======= ============= =========== ======


Python API
----------

.. automodule:: SDPMaster
    :members:
    :undoc-members:
