
import json
import re

class ProcessingBlock:

    def __init__(self, json, path):
        self._json = json
        self._path = path

    @property
    def pb_id(self):
        """ Returns the Processing Block id """
        return self._json['pb_id']

    @property
    def sbi_id(self):
        """Returns the Scheduling Block Instance id, if one is associated
        with this processing block. """
        return self._json.get('sbi_id')

    @property
    def workflow(self):
        """ Returns information identifying the workflow """
        return self._json['workflow']

    @property
    def parameters(self):
        """ Returns workflow parameters """
        return self._json['parameters']

    @property
    def scan_parameters(self):
        """ Returns workflow scan parameters """
        return self._json['scan_parameters']


