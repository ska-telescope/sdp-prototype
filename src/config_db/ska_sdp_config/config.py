
from . import backend as backend_mod, entity

from datetime import date
import re
import os
import json

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

    def txn(self, max_retries=64):
        """Returns a transaction object that can be used for consistently
        querying or changing the configuration state. As we do not use
        locks, transactions might have to be repeated in order to
        guarantee atomicity.

        Suggested usage is as follows:
        ```
        for txn in config.txn():
            # Use txn to read+write configuration
            # [Possibly call txn.loop()]
        ```

        As the `for` loop suggests, the code might get run multiple
        times even if not forced by calling `loop`. Any writes using
        the transaction will be discarded if the transaction fails,
        but the application must make sure that the loop body has no
        other observable side effects.

        :param max_retries: Number of transaction retries before a
            `RuntimeError` gets raised.
        """
        return TransactionFactory(
            self, self._backend.txn(max_retries=max_retries))

class TransactionFactory(object):
    """ Helper object for making transactions """

    def __init__(self, config, txn):
        self._config = config
        self._txn = txn

    def __iter__(self):
        for txn in self._txn:
            yield Transaction(self._config, txn)

class Transaction(object):

    def __init__(self, config, txn):
        self._cfg = config
        self._txn = txn
        self._pb_path = config._pb_path

    def _to_json(self, obj):
        # We only write dictionaries (JSON objects) at the moment
        assert(isinstance(obj, dict))
        # Export to JSON. No need to convert to ASCII, as the backend
        # should handle unicode. Otherwise we optimise for legibility
        # over compactness.
        return json.dumps(
            obj, ensure_ascii=False,
            indent=2, separators=(',', ': '), sort_keys=True)

    def _get(self, path):
        """ Gets a JSON object from the database """

        txt = self._txn.get(path)
        if txt is None:
            return None
        else:
            return json.loads(txt)

    def _create(self, path, obj):
        """ Sets a new path in the database to a JSON object """
        self._txn.create(path, self._to_json(obj))

    def _update(self, path, obj):
        """ Sets a existing path in the database to a JSON object """
        self._txn.update(path, self._to_json(obj))

    def list_processing_blocks(self, prefix=""):
        """Querys processing block IDs that currently exist in the
        configuration.

        :param prefix: If given, only search for processing block IDs
           with the given prefix
        :returns: Processing block ids, in lexographical order
        """

        # List keys
        pb_path = self._pb_path
        keys = self._txn.list_keys(pb_path + prefix)

        # return list, stripping the prefix
        assert all([ key.startswith(pb_path) for key in keys])
        return list([ key[len(pb_path):] for key in keys ])

    def new_processing_block_id(self, workflow_type):
        """Generates a new processing block ID that does not yet exist in the
        configuration.

        :param workflow_type: Type of workflow / processing block to create

        :returns: Processing block id
        """

        # Find existing processing blocks with same prefix
        pb_id_prefix = "{}-{}-".format(
            workflow_type,
            date.today().strftime('%Y%m%d'))
        existing_ids = self.list_processing_blocks(pb_id_prefix)

        # Choose ID that doesn't exist
        for pb_ix in range(9999):
            pb_id = pb_id_prefix + "{:04}".format(pb_ix)
            if pb_id not in existing_ids:
                break
        if pb_ix >= 9999:
            raise RuntimeError("Exhausted maximum number of processing blocks!")
        return pb_id

    def get_processing_block(self, pb_id):
        """
        Looks up processing block data.

        :param pb_id: Processing block ID to look up
        :returns: Processing block entity, or None if it doesn't exist
        """
        dct = self._get_json(self._cfg.pb_path + pb_id)
        if dct is None:
            return None
        else:
            return ProcessingBlock(None, None, None, dct=dct)

    def create(self, obj):
        """
        Creates an entity in the database

        :param obj: Object to create
        """

        if isinstance(obj, entity.ProcessingBlock):
            self._create(self._pb_path + obj.pb_id, obj.to_dict())
        else:
            raise ValueError("Unknown object type: {}".format(obj))

    def update(self, obj):
        """
        Updates an entity in the database

        :param obj: Object to update
        """

        if isinstance(obj, entity.ProcessingBlock):
            self._update(self._pb_path + obj.pb_id, obj.dict)
        else:
            raise ValueError("Unknown object type: {}".format(obj))
