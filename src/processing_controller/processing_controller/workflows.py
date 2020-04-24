"""
Class to handle workflow definitions.
"""

import json
import logging
import requests
import jsonschema

LOG = logging.getLogger('processing_controller')


class Workflows:
    """Processing controller workflow definitions."""

    def __init__(self, schema_file):
        """Initialise empty workflow list with schema.

        :param schema_file: name of schema file
        """
        self._schema = self._read_schema(schema_file)
        self._version = {}
        self._realtime = {}
        self._batch = {}

    @staticmethod
    def _read_schema(schema_file):
        """Read workflow definition schema.

        :param schema_file: name of schema file.
        """
        LOG.info('Using schema file: %s', schema_file)
        try:
            with open(schema_file, 'r') as file:
                schema = json.load(file)
        except FileNotFoundError as error:
            LOG.error('Cannot read schema file: %s', error.strerror)
            schema = {}
        except json.JSONDecodeError as error:
            LOG.error('Cannot decode schema as JSON: %s', error.msg)
            schema = {}

        return schema

    @property
    def version(self):
        """Version of workflow definitions."""
        return self._version

    def realtime(self, wf_id, version):
        """Get name of real-time workflow Docker image.

        :param wf_id: Workflow ID
        :param version: Workflow version
        :returns: Workflow image or None if not defined
        """
        if (wf_id, version) in self._realtime:
            image = self._realtime[(wf_id, version)]
        else:
            image = None
        return image

    def batch(self, wf_id, version):
        """Get name of batch workflow Docker image.

        :param wf_id: Workflow ID
        :param version: Workflow version
        :returns: Workflow image or None if not defined
        """
        if (wf_id, version) in self._batch:
            image = self._batch[(wf_id, version)]
        else:
            image = None
        return image

    def update_file(self, workflows_file):
        """Update workflow definitions from file.

        :param workflows_file: name of workflow definition file
        """
        try:
            with open(workflows_file, 'r') as file:
                workflows_str = file.read()
        except FileNotFoundError as error:
            LOG.error('Cannot read workflows from file: %s', error.strerror)
            return

        self._update(workflows_str)

    def update_url(self, workflows_url):
        """Update workflow definitions from URL.

        :param workflows_url: URL of workflow definition file
        """
        with requests.get(workflows_url) as req:
            if not req.ok:
                LOG.error('Cannot read workflows from URL: %s', req.reason)
                return
            workflows_str = req.text

        self._update(workflows_str)

    def _update(self, workflows_str):
        """Update workflow definitions.

        :param workflows_str: workflow definitions (str)
        """
        try:
            workflows = json.loads(workflows_str)
            jsonschema.validate(workflows, self._schema)
        except json.JSONDecodeError as error:
            LOG.error('Cannot decode workflow definition as JSON: %s', error.msg)
            return
        except jsonschema.ValidationError as error:
            LOG.error('Cannot validate workflow definition against schema: %s', error.message)
            return

        # Get version of workflow definition file.
        self._version = workflows['version']

        # Parse repositories.
        repositories = {}
        for repo in workflows['repositories']:
            repo_name = repo['name']
            repo_path = repo['path']
            if repo_name in repositories:
                LOG.warning('Repository %s already defined, will be overwritten', repo_name)
            repositories[repo_name] = repo_path

        # Parse workflow definitions.
        self._realtime = {}
        self._batch = {}
        for wf in workflows['workflows']:
            wf_type = wf['type']
            wf_id = wf['id']
            wf_repo = wf['repository']
            wf_image = wf['image']
            wf_versions = wf['versions']
            if wf_repo not in repositories:
                LOG.warning('Repository %s for %s workflow %s not found, skipping', wf_repo, wf_type, wf_id)
                continue
            if wf_type == 'realtime':
                wfdict = self._realtime
            elif wf_type == 'batch':
                wfdict = self._batch
            else:
                LOG.warning('Workflow %s has unknown type %s, skipping', wf_id, wf_type)
                continue
            for vers in wf_versions:
                if (wf_id, vers) in wfdict:
                    LOG.warning('%s workflow %s version %s already defined, '
                                'will be overwritten', wf_type, wf_id, vers)
                wfdict[(wf_id, vers)] = repositories[wf_repo] + "/" + wf_image + ":" + vers

        LOG.debug('Workflow definitions version:')
        for k, v in self._version.items():
            LOG.debug('%s: %s', k, v)
        LOG.debug('Realtime workflows:')
        for k, v in self._realtime.items():
            LOG.debug('%s: %s', k, v)
        LOG.debug('Batch workflows:')
        for k, v in self._batch.items():
            LOG.debug('%s: %s', k, v)
