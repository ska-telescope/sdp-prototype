Running the SDP Prototype in the integration environment
========================================================

The SDP prototype is being integrated with the prototypes of the other
telescope sub-systems as part of the so-called *Minimum Viable Product*
(MVP).

The integration is done in the `SKA MVP Prototype Integration
(SKAMPI) repository <https://gitlab.com/ska-telescope/skampi/>`_.

Instructions for installing and running the MVP can be found in the
`SKAMPI documentation
<https://developer.skatelescope.org/projects/skampi/en/latest/>`_.

To then deploy an SDP workflow without using WebJive etc., follow the instructions in the
`standalone SDP documentation
<https://developer.skatelescope.org/projects/sdp-prototype/en/latest/running/running_standalone.html#connecting-to-the-configuration-database>`_.
However, you will need to append the namespace in which the SDP is running.

.. code-block::

    $ kubectl exec -it deploy/test-sdp-prototype-console -- /bin/bash -n <namespace>

The default namespace into which `skampi` deploys is `-n integration`.

Alternatively, you may run

.. code-block::

    $ kubectl config set-context --current --namespace=integration

to allow you to run the commands without alteration.
