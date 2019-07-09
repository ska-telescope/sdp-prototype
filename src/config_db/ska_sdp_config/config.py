
from . import backend as backend_mod, entity

from datetime import date
import re
import os
import json

# Permit identifiers up to 64 bytes in length
_id_re = re.compile("[_A-Za-z0-9]{1,64}")

class Config(object):

    def __init__(self, backend=None, global_prefix='', **client_args):
        """
        Connects to the configuration database using the given backend

        :param backend: Backend to use. Defaults to environment or etcd3 if not set.
        """

        # Determine backend
        backend = os.getenv('SDP_CONFIG_BACKEND', 'etcd3')

        # Instantiate backend, reading configuration from environment/dotenv
        if backend == 'etcd3':
            if 'host' not in client_args:
                client_args['host'] = os.getenv('SDP_CONFIG_HOST', '127.0.0.1')
            if 'port' not in client_args:
                client_args['port'] = int(os.getenv('SDP_CONFIG_HOST', 2379))
            if 'protocol' not in client_args:
                client_args['protocol'] = os.getenv('SDP_CONFIG_PROTOCOL', 'http')
            if 'cert' not in client_args:
                client_args['cert'] = os.getenv('SDP_CONFIG_CERT', ())
            if 'username' not in client_args:
                client_args['username'] = os.getenv('SDP_CONFIG_USERNAME', None)
            if 'password' not in client_args:
                client_args['password'] = os.getenv('SDP_CONFIG_PASSWORD', None)

            self._backend = backend_mod.Etcd3(**client_args)
        else:
            raise ValueError("Unknown configuration backend {}!".format(backend))

        # Prefixes
        assert global_prefix == '' or global_prefix[0] == '/'
        self._pb_path = global_prefix+"/pb/"

    def lease(self, ttl=10):
        """
        Generates a new lease. Once entered can be associated with keys,
        which will be kept alive until the end of the lease. At that
        point a daemon thread will be started automatically to refresh
        the lease periodically (default seems to be TTL/4).

        :param ttl: Time to live for lease
        :returns: lease object
        """

        return self._backend.lease(ttl)

    def create_pb(self, workflow, parameters={}, scan_parameters={},
                  pb_id=None, sbi_id=None):
        """
        Creates a new processing block

        :param workflow: Workflow description (JSON for now)
        :param parameters: Workflow parameters
        :param scan_parameters: Scan parameters (unneded for batch processing)
        :param pb_id: Processing block ID.
        :param sbi_id: Scheduling block ID, if it exists.
        :returns: ProcessingBlock object
        """

        # Make sure workflow JSON is valid (TODO: move)
        if set(workflow.keys()) != set(['name', 'type', 'version']):
            raise ValueError("Workflow must specify exactly name, type and version!")
        parameters = dict(parameters)
        scan_parameters = dict(scan_parameters)
        if pb_id is not None:
            pb_id = str(pb_id)
        if sbi_id is not None:
            sbi_id = str(sbi_id)

        # Might need to retry if multiple processing blocks are
        # getting created concurrently
        for retry in range(10):

            # Choose new processing block ID
            if pb_id is not None:
                set_pb_id = pb_id
            else:

                # Find existing processing blocks with same prefix
                pb_id_prefix = "{}-{}-".format(
                        workflow['type'],
                        date.today().strftime('%Y%m%d'))
                existing_keys, _ = self._backend.list_keys(
                    self._pb_path+pb_id_prefix, prefix=True)
                print(existing_keys)

                # Choose ID that doesn't exist
                for pb_ix in range(999999):
                    set_pb_id = pb_id_prefix + "{:03}".format(pb_ix)
                    if self._pb_path+set_pb_id not in existing_keys:
                        break

            # Make dictionary describing processing block
            pb = {
                'pb_id': set_pb_id,
                'sbi_id': sbi_id,
                'workflow': workflow,
                'parameters': parameters,
                'scan_parameters': scan_parameters
            }
            pb_path = self._pb_path+set_pb_id

            # Attempt to create processing block
            self._backend.create(pb_path, json.dumps(pb))
            return entity.ProcessingBlock(pb, pb_path)

        raise RuntimeError("Exhausted retries while trying to create processing block!")

