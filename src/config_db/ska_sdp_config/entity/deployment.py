"""Deployment configuration entities."""

import re
import copy

# Permit identifiers up to 96 bytes in length
_DEPLOY_ID_RE = re.compile("^[A-Za-z0-9\\-]{1,96}$")

# Supported deployment types
DEPLOYMENT_TYPES = {
    'helm'  # Use helm controller process
}


class Deployment:
    """Deployment entity.

    Collects configuration information relating to a cluster
    configuration change.
    """

    # pylint: disable=dangerous-default-value
    # pylint: disable=redefined-builtin

    def __init__(self, id, type, args):
        """
        Create a new deployment structure.

        :param id: Deployment ID
        :param type: Type of the deployment (method by which
            it is applied)
        :param args: Type-specific deployment arguments
        :returns: Deployment object
        """
        # Get parameter dictionary
        self._dict = {
            'id': str(id),
            'type': str(type),
            'args': dict(copy.deepcopy(args)),
        }

        # Validate
        if type not in DEPLOYMENT_TYPES:
            raise ValueError("Unknown deployment type {}!".format(type))
        if not _DEPLOY_ID_RE.match(self.id):
            raise ValueError("Deployment ID {} not permissible!".format(
                self.id))

    def to_dict(self):
        """Return data as dictionary."""
        return self._dict

    @property
    def id(self):
        """Return the deployment id."""
        return self._dict['id']

    @property
    def type(self):
        """Return deployment type."""
        return self._dict.get('type')

    @property
    def args(self):
        """Return deployment arguments."""
        return self._dict['args']

    def __repr__(self):
        """Produce object representation."""
        return "entity.Deployment({})".format(
            ",".join(["{}={}".format(k, repr(v)) for
                      k, v in self.to_dict().items()]))

    def __eq__(self, other):
        """Equality check."""
        return self.to_dict() == other.to_dict()
