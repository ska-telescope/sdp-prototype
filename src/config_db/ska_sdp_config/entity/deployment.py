"""Deployment configuration entities."""


import re
import copy


# Permit identifiers up to 96 bytes in length
_DEPLOY_ID_RE = re.compile("^[A-Za-z0-9\\-]{1,96}$")

# Supported deployment types
DEPLOYMENT_TYPES = {
    'process-direct',  # Directly spawn local processes
    'kubernetes-direct',  # Workflow directly changes Kubernetes configuration
    'helm'  # Use helm controller process
}


class Deployment:
    """Deployment entity.

    Collects configuration information relating to a cluster
    configuration change.
    """

    # pylint: disable=W0102,W0622
    def __init__(self, deploy_id, type, args):
        """
        Create a new deployment structure.

        :param deploy_id: Deployment ID
        :param type: Type of the deployment (method by which
            it is applied)
        :param args: Type-specific deployment arguments
        :returns: Deployment object
        """
        # Get parameter dictionary
        self._dict = {
            'deploy_id': str(deploy_id),
            'type': str(type),
            'args': dict(copy.deepcopy(args)),
        }

        # Validate
        if type not in DEPLOYMENT_TYPES:
            raise ValueError("Unkown deployment type {}!".format(type))
        if not _DEPLOY_ID_RE.match(self.deploy_id):
            raise ValueError("Deployment ID {} not permissable!".format(
                self.deploy_id))

    def to_dict(self):
        """Return data as dictionary."""
        return self._dict

    @property
    def deploy_id(self):
        """Return the Deployment id."""
        return self._dict['deploy_id']

    @property
    def type(self):
        """Return deployment type."""
        return self._dict.get('type')

    @property
    def args(self):
        """Return deployment arguments."""
        return self._dict['args']
