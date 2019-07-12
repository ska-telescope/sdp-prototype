
import json
import re
import copy

# Permit identifiers up to 64 bytes in length
_pb_id_re = re.compile("[_A-Za-z0-9]{1,64}")

class ProcessingBlock:

    def __init__(self, pb_id, sbi_id, workflow,
                 parameters={}, scan_parameters={},
                 dct=None):
        """
        Creates a new processing block structure

        :param pb_id: Processing block ID
        :param sbi_id: Scheduling block ID (None if not associated with an SBI)
        :param workflow: Workflow description (dictionary for now)
        :param parameters: Workflow parameters
        :param scan_parameters: Scan parameters (not for batch processing)
        :param dct: Dictionary to load from (will ignore other parameters)
        :returns: ProcessingBlock object
        """

        # Get parameter dictionary
        if dct is not None:
            self._dict = dct
        else:
            self._dict = {
                'pb_id': str(pb_id),
                'sbi_id': None if sbi_id is None else str(sbi_id),
                'workflow': dict(copy.deepcopy(workflow)),
                'parameters': dict(copy.deepcopy(parameters)),
                'scan_parameters': dict(copy.deepcopy(scan_parameters))
            }

        # Validate
        if set(self.workflow) != set(['name', 'type', 'version']):
            raise ValueError("Workflow must specify name, type and version!")
        if not _pb_id_re.match(self.pb_id):
            raise ValueError("Processing block ID {} not permissable!".format(self.pb_id))

    def to_dict(self):
        """ Returns workflow scan parameters """
        return self._dict['scan_parameters']

    @property
    def pb_id(self):
        """ Returns the Processing Block id """
        return self._dict['pb_id']

    @property
    def sbi_id(self):
        """Returns the Scheduling Block Instance id, if one is associated
        with this processing block. """
        return self._dict.get('sbi_id')

    @property
    def workflow(self):
        """ Returns information identifying the workflow """
        return self._dict['workflow']

    @property
    def parameters(self):
        """ Returns workflow parameters """
        return self._dict['parameters']

    @property
    def scan_parameters(self):
        """ Returns workflow scan parameters """
        return self._dict['scan_parameters']

