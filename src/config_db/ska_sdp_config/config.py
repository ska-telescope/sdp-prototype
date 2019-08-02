"""High-level API for SKA SDP configuration."""

import os
import sys
import functools
from datetime import date
import json
from socket import gethostname

from . import backend as backend_mod, entity, deploy


class Config():
    """Connection to SKA SDP configuration."""

    def __init__(self, backend=None, global_prefix='', owner=None,
                 **cargs):
        """
        Connect to configuration using the given backend.

        :param backend: Backend to use. Defaults to environment or etcd3 if
            not set.
        :param global_prefix: Prefix to use within the database
        :param owner: Dictionary used for identifying the process when claiming
            ownership.
        :param cargs: Backend client arguments
        """
        # Determine backend
        backend = os.getenv('SDP_CONFIG_BACKEND', 'etcd3')

        # Instantiate backend, reading configuration from environment/dotenv
        if backend == 'etcd3':
            if 'host' not in cargs:
                cargs['host'] = os.getenv('SDP_CONFIG_HOST', '127.0.0.1')
            if 'port' not in cargs:
                cargs['port'] = int(os.getenv('SDP_CONFIG_PORT', '2379'))
            if 'protocol' not in cargs:
                cargs['protocol'] = os.getenv('SDP_CONFIG_PROTOCOL', 'http')
            if 'cert' not in cargs:
                cargs['cert'] = os.getenv('SDP_CONFIG_CERT', None)
            if 'username' not in cargs:
                cargs['username'] = os.getenv('SDP_CONFIG_USERNAME', None)
            if 'password' not in cargs:
                cargs['password'] = os.getenv('SDP_CONFIG_PASSWORD', None)

            self._backend = backend_mod.Etcd3(**cargs)
        else:
            raise ValueError(
                "Unknown configuration backend {}!".format(backend))

        # Owner dictionary
        if owner is None:
            owner = {
                'pid': os.getpid(),
                'hostname': gethostname(),
                'command': sys.argv
            }
        self.owner = dict(owner)

        # Prefixes
        assert global_prefix == '' or global_prefix[0] == '/'
        self.pb_path = global_prefix+"/pb/"
        self.deploy_path = global_prefix+"/deploy/"

        # Lease associated with client
        self._client_lease = None

    def lease(self, ttl=10):
        """
        Generate a new lease.

        Once entered can be associated with keys,
        which will be kept alive until the end of the lease. At that
        point a daemon thread will be started automatically to refresh
        the lease periodically (default seems to be TTL/4).

        :param ttl: Time to live for lease
        :returns: lease object
        """
        return self._backend.lease(ttl)

    @property
    def client_lease(self):
        """Return the lease associated with the client.

        It will be kept alive until the client gets closed.
        """
        if self._client_lease is None:
            self._client_lease = self.lease()
            self._client_lease.__enter__()

        return self._client_lease

    def txn(self, max_retries=64):
        """Create a :class:`Transaction` for atomic configuration query/change.

        As we do not use locks, transactions might have to be repeated in
        order to guarantee atomicity. Suggested usage is as follows:

        .. code-block:: python

            for txn in config.txn():
                # Use txn to read+write configuration
                # [Possibly call txn.loop()]

        As the `for` loop suggests, the code might get run multiple
        times even if not forced by calling
        :meth:`Transaction.loop`. Any writes using the transaction
        will be discarded if the transaction fails, but the
        application must make sure that the loop body has no other
        observable side effects.

        :param max_retries: Number of transaction retries before a
            :class:`RuntimeError` gets raised.
        """
        return TransactionFactory(
            self, self._backend.txn(max_retries=max_retries))

    def close(self):
        """Close the client connection."""
        if self._client_lease:
            self._client_lease.__exit__(None, None, None)
            self._client_lease = None
        self._backend.close()

    def __enter__(self):
        """Scope the client connection."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Scope the client connection."""
        self.close()
        return False

    # pylint: disable=R0201
    def get_deployment_logs(self, dpl: entity.Deployment,
                            max_lines: int = 500):
        """
        Retrieve logs (stdout) produced by a deployment.

        Might not be supported by all deployment types, and not to all
        processes (e.g. subprocess stdout is only available to the
        spawning process).

        :param dpl: Deployment to query for logs
        :param max_lines: Maximum number of lines to return (log tail)
        :returns: A list of the last log lines
        """
        return deploy.get_deployment_logs(dpl, max_lines)


class TransactionFactory():
    """Helper object for making transactions."""

    def __init__(self, config, txn):
        """Create transaction factory."""
        self._config = config
        self._txn = txn

    def __iter__(self):
        """Create new transaction objects."""
        for txn in self._txn:
            yield Transaction(self._config, txn)


def dict_to_json(obj):
    """Format a dictionary for writing it into the database.

    :param obj: Dictionary object to format
    :returns: String representation
    """
    # We only write dictionaries (JSON objects) at the moment
    assert isinstance(obj, dict)
    # Export to JSON. No need to convert to ASCII, as the backend
    # should handle unicode. Otherwise we optimise for legibility
    # over compactness.
    return json.dumps(
        obj, ensure_ascii=False,
        indent=2, separators=(',', ': '), sort_keys=True)


class Transaction():
    """High-level configuration queries and updates to execute atomically."""

    def __init__(self, config, txn):
        """Instantiate transaction."""
        self._cfg = config
        self._txn = txn
        self._pb_path = config.pb_path
        self._deploy_path = config.deploy_path

    @property
    def raw(self):
        """Return transaction object for accessing database directly."""
        return self._txn

    def _get(self, path):
        """Get a JSON object from the database."""
        txt = self._txn.get(path)
        if txt is None:
            return None
        return json.loads(txt)

    def _create(self, path, obj, lease=None):
        """Set a new path in the database to a JSON object."""
        self._txn.create(path, dict_to_json(obj), lease)

    def _update(self, path, obj):
        """Set a existing path in the database to a JSON object."""
        self._txn.update(path, dict_to_json(obj))

    def loop(self, wait=False):
        """Repeat transaction regardless of whether commit succeeds.

        :param wait: If transaction succeeded, wait for any read
            values to change before repeating it.
        """
        return self._txn.loop(wait)

    def list_processing_blocks(self, prefix=""):
        """Query processing block IDs from the configuration.

        :param prefix: If given, only search for processing block IDs
           with the given prefix
        :returns: Processing block ids, in lexographical order
        """
        # List keys
        pb_path = self._pb_path
        keys = self._txn.list_keys(pb_path + prefix)

        # return list, stripping the prefix
        assert all([key.startswith(pb_path) for key in keys])
        return list([key[len(pb_path):] for key in keys])

    def new_processing_block_id(self, workflow_type: str):
        """Generate a new processing block ID that does not yet in use.

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
            raise RuntimeError("Exceeded daily number of processing blocks!")
        return pb_id

    def get_processing_block(self, pb_id: str) -> entity.ProcessingBlock:
        """
        Look up processing block data.

        :param pb_id: Processing block ID to look up
        :returns: Processing block entity, or None if it doesn't exist
        """
        dct = self._get(self._pb_path + pb_id)
        if dct is None:
            return None
        return entity.ProcessingBlock(**dct)

    def create_processing_block(self, pb: entity.ProcessingBlock):
        """
        Add a new :class:`ProcessingBlock` to the configuration.

        :param obj: Processing block to create
        """
        assert isinstance(pb, entity.ProcessingBlock)
        self._create(self._pb_path + pb.pb_id, pb.to_dict())

    def update_processing_block(self, pb: entity.ProcessingBlock):
        """
        Update a :class:`ProcessingBlock` in the configuration.

        :param obj: Processing block to update
        """
        assert isinstance(pb, entity.ProcessingBlock)
        self._update(self._pb_path + pb.pb_id, pb.to_dict())

    def get_processing_block_owner(self, pb_id: str) -> dict:
        """
        Look up the current processing block owner.

        :param pb_id: Processing block ID to look up
        :returns: Processing block owner data, or None if not claimed
        """
        dct = self._get(self._pb_path + pb_id + "/owner")
        if dct is None:
            return None
        return dct

    def is_processing_block_owner(self, pb_id: str) -> bool:
        """
        Check whether this client is owner of the processing block.

        :param pb_id: Processing block ID to look up
        :returns: Whether processing block is owned
        """
        return self.get_processing_block_owner(pb_id) == self._cfg.owner

    def take_processing_block(self, pb_id: str, lease):
        """
        Take ownership of the processing block.

        :param pb_id: Processing block ID to take ownership of
        :raises: backend.Collision
        """
        # Lease must be provided
        assert lease is not None

        # Provide information identifying this process
        self._create(self._pb_path + pb_id + "/owner", self._cfg.owner, lease)

    def take_processing_block_by_workflow(self, workflow: dict, lease) \
            -> entity.ProcessingBlock:
        """
        Take ownership of unclaimed processing block matching a workflow.

        :param workflow: Workflow description. Must exactly match the
            workflow description used to create the processing block.
        :returns: Processing block, or None if no match was found
        """
        # Look for matching processing block
        for pb_id in self.list_processing_blocks(workflow['type']):
            pb = self.get_processing_block(pb_id)
            if pb.workflow == workflow and \
               self.get_processing_block_owner(pb_id) is None:

                # Take ownership
                self.take_processing_block(pb_id, lease)

                # Return
                return pb

        return None

    def get_deployment(self, deploy_id: str) -> entity.Deployment:
        """
        Retrieve details about a cluster configuration change.

        :param deploy_id: Name of the deployment
        :returns: Deployment details
        """
        dct = self._get(self._deploy_path + deploy_id)
        return entity.Deployment(**dct)

    def create_deployment(self, dpl: entity.Deployment):
        """
        Request a change to cluster configuration.

        :param dpl: Deployment to add to database
        """
        # Add to database
        assert isinstance(dpl, entity.Deployment)
        self._create(self._deploy_path + dpl.deploy_id,
                     dpl.to_dict())

        # Apply deployment on successful deployment (this should
        # eventually be done by a separate controller process!)
        self._txn.on_commit(functools.partial(deploy.apply_deployment, dpl))

    def delete_deployment(self, dpl: entity.Deployment):
        """
        Undo a change to cluster configuration.

        :param dpl: Deployment to remove
        """
        # Delete all data associated with deployment
        deploy_path = self._deploy_path + dpl.deploy_id
        for key in self._txn.list_keys(deploy_path, recurse=5):
            self._txn.delete(key)

        # Apply deployment on successful deployment (this should
        # eventually be done by a separate controller process!)
        self._txn.on_commit(functools.partial(deploy.undo_deployment, dpl))
