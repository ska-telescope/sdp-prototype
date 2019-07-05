
import etcd3
import re

class BackendEtcd3:

    def __init__(self, *args, **kw_args):
        self._client = etcd3.Client(*args, **kw_args)

    def _tag_depth(self, path, depth=None):
        """
        Add depth tag to path. This is to allow us to use recursive
        "directories" on top of etcd3.
        """
        # All paths must start at the root
        if path[0] != '/':
            raise ValueError("Path must start with /!")
        if depth is None:
            depth = path.count('/')
        return "{}{}".format(depth, path).encode('utf-8')

    def _untag_depth(self, path):
        """
        Remove depth from path
        """
        # Cut from first '/'
        slash_ix = path.index('/')
        if slash_ix is None:
            return path
        else:
            return path[slash_ix:]

    def lease(self, ttl=10):
        """
        Generates a new lease. Once entered can be associated with keys,
        which will be kept alive until the end of the lease. At that
        point a daemon thread will be started automatically to refresh
        the lease periodically (default seems to be TTL/4).

        :param ttl: Time to live for lease
        :returns: lease object
        """

        return self._client.Lease(ttl=ttl)

    def get(self, path, revision=None):
        """
        Get value of a key

        :param path: Path of key to query
        :param revision: Revision of key to read
        :returns: (value, revision). value is None if it doesn't exit
        """

        tagged_path = self._tag_depth(path)
        response = self._client.range(tagged_path, revision=revision)

        # Get value returned
        result = response.kvs
        if result is not None:
            assert len(response.kvs) == 1, "Requesting '{}' yielded more "+ \
                "than one match!".format(tagged_path)
            result = result[0].value.decode('utf-8')

        # Return value together with revision
        return (result, response.header.revision)

    def list_keys(self, path, prefix=False, revision=None):
        """
        List keys under current path

        :param path: Parent path of keys to query
        :param prefix: Return keys on same recursion level with
            matchin prefix instead of children
        :returns: (key list, revision)
        """

        # Prepare parameters
        if prefix:
            tagged_path = self._tag_depth(path)
        else:
            tagged_path = self._tag_depth(path+"/")
        response = self._client.range(
            tagged_path, prefix=True, keys_only=True, revision=revision)
        if response.kvs is None:
            return ([], response.header.revision)
        else:
            return ([ self._untag_depth(kv.key.decode('utf-8'))
                      for kv in response.kvs],
                    response.header.revision)

    def create(self, path, value, lease=None):
        """
        Create a key at the path in question and initialises it with the
        value. Fails if the value already exists.

        :param path: Path to create
        :param value: Value to set
        :param lease: Lease to associate
        :returns: Whether creation succeeded
        """

        # Prepare parameters
        tagged_path = self._tag_depth(path)
        lease_id = (0 if lease is None else lease.ID)
        value = str(value).encode('utf-8')

        # Put value if version is zero (i.e. does not exist)
        txn = self._client.Txn()
        txn.compare(txn.key(tagged_path).version == 0)
        txn.success(txn.put(tagged_path, value, lease_id))
        return txn.commit().succeeded

    def update(self, path, value):
        """
        Updates an existing key. Fails if the key does not exist.

        :param path: Path to update
        :param value: Value to set
        :returns: Whether transaction was successful
        """

        tagged_path = self._tag_depth(path)
        value = str(value).encode('utf-8')
        # Put value if version is *not* zero (i.e. it exists)
        txn = self._client.Txn()
        txn.compare(txn.key(tagged_path).version != 0)
        txn.success(txn.put(tagged_path, value))
        return txn.commit().succeeded

    def delete(self, path,
               must_exist = True, recursive = False, prefix = False,
               max_depth = 16):
        """
        Deletes the given key or key range

        :param path: Path (prefix) of keys to remove
        :param must_exist: Fail if path does not exist?
        :param recursive: Delete children keys at lower levels recursively
        :param prefix: Delete all keys at given level with prefix
        :returns: Whether transaction was successful
        """

        tagged_path = self._tag_depth(path)

        # Determine start recursion level
        txn = self._client.Txn()
        if must_exist:
            txn.compare(txn.key(tagged_path).version != 0)
        txn.success(txn.delete(tagged_path, prefix=prefix))

        # If recursive, we also delete all paths at lower recursion
        # levels that have the path as a prefix
        if recursive:
            depth = path.count('/')
            for d in range(depth+1, depth+max_depth):
                dpath = self._tag_depth(path if prefix else path+'/', d)
                txn.success(txn.delete(dpath, prefix=True))

        # Execute
        return txn.commit().succeeded
