"""Processing block configuration entities."""

import re
import copy

# Permit identifiers up to 64 bytes in length
_PB_ID_RE = re.compile("^[A-Za-z0-9\\-]{1,64}$")


class ProcessingBlock:
    """Processing block entity.

    Collects configuration information relating to a processing job
    for the SDP. This might be either real-time (supporting a running
    observation) or batch (to process data after the fact).

    Actual execution of processing steps will be performed by a
    (parameterised) workflow interpreting processing block information.
    """

    # pylint: disable=dangerous-default-value
    # pylint: disable=redefined-builtin

    def __init__(self, id, sbi_id, workflow,
                 parameters={}, dependencies=[],
                 **kwargs):
        """
        Create a new processing block structure.

        :param id: Processing block ID
        :param sbi_id: Scheduling block ID (None if not associated with an SBI)
        :param workflow: Workflow description (dictionary for now)
        :param parameters: Workflow parameters
        :param dependencies: Dependencies on other processing blocks (not for
        real-time processing)
        :param dct: Dictionary to load from (will ignore other parameters)
        :returns: ProcessingBlock object
        """
        # Get parameter dictionary
        self._dict = {
            'id': str(id),
            'sbi_id': None if sbi_id is None else str(sbi_id),
            'workflow': dict(copy.deepcopy(workflow)),
            'parameters': dict(copy.deepcopy(parameters)),
            'dependencies': list(copy.deepcopy(dependencies))
        }
        self._dict.update(kwargs)

        # Validate
        if set(self.workflow) != {'type', 'id', 'version'}:
            raise ValueError("Workflow must specify type, ID and version!")
        if not _PB_ID_RE.match(self.id):
            raise ValueError("Processing block ID {} not permissible!".format(
                self.id))

    def to_dict(self):
        """Return data as dictionary."""
        return self._dict

    @property
    def id(self):
        """Return the processing block ID."""
        return self._dict['id']

    @property
    def sbi_id(self):
        """Return scheduling block instance ID, if associated with one."""
        return self._dict.get('sbi_id')

    @property
    def workflow(self):
        """Return information identifying the workflow."""
        return self._dict['workflow']

    @property
    def parameters(self):
        """Return workflow-specific parameters."""
        return self._dict['parameters']

    @property
    def dependencies(self):
        """Return dependencies on other processing blocks."""
        return self._dict['dependencies']

    def __repr__(self):
        """Build string representation."""
        return "ProcessingBlock({})".format(
            ", ".join(["{}={}".format(k, repr(v))
                       for k, v in self._dict.items()]))

    def __eq__(self, other):
        """Equality check."""
        return self.to_dict() == other.to_dict()
