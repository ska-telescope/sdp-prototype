Helm charts for CBF-SDP emulator
================================

These are simple charts
that show how to run the software contained in this package.

Both the sender and the receiver
require an input MS file,
which is mapped as a Volume in both containers.
The source of this volume is fairly free,
and is specified by the ``input.mountType``
and ``inptut.mountTypeOptions`` Helm values.
Their default values are:

.. code-block:: yaml

    mountType: hostPath
    mountTypeOptions:
       type: Directory
       path: /tmp/input.ms

Any other values should work correctly though,
giving users the ability to specify
any mount type for this volume.
