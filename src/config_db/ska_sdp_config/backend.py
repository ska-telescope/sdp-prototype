
import etcd3
import queue

class Etcd3:

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
        """Generates a new lease.

        Once entered can be associated with keys, which will be kept
        alive until the end of the lease. Note that this involves
        starting a daemon thread that will refresh the lease
        periodically (default seems to be TTL/4).

        :param ttl: Time to live for lease
        :returns: lease object
        """

        return self._client.Lease(ttl=ttl)

    def get(self, path, revision=None, watch=False):
        """
        Get value of a key

        :param path: Path of key to query
        :param revision: Revision of key to read
        :returns: (value, revision). value is None if it doesn't exit
        """

        tagged_path = self._tag_depth(path)
        rev = (None if revision is None else revision.revision)

        # Query range
        response = self._client.range(tagged_path, revision=rev)

        # Get value returned
        result = response.kvs
        modRevision = None
        if result is not None:
            assert len(response.kvs) == 1, "Requesting '{}' yielded more "+ \
                "than one match!".format(tagged_path)
            modRevision = result[0].mod_revision
            result = result[0].value.decode('utf-8')

        # Return value together with revision
        return (result, Etcd3Revision(response.header.revision, modRevision))

    def watch(self, path, revision=None, watch=False):
        """
        Watch value of a key

        :param path: Path of key to query
        :param revision: Revision of first key value to read
        :returns: (value, revision). value is None if it doesn't exit
        """

        tagged_path = self._tag_depth(path)
        rev = (None if revision is None else revision.revision)

        # Set up watcher
        watcher = self._client.Watcher(tagged_path, start_revision=rev, prev_kv=True)
        return Etc3Watcher(watcher)

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
        rev = None
        if revision is not None:
            rev = revision.revision

        # Query range
        response = self._client.range(
            tagged_path, prefix=True, keys_only=True, revision=rev)

        # We do not return a mod revision here - this would not be
        # very useful anyway as we are not returning values
        revision = Etcd3Revision(response.header.revision, None)

        if response.kvs is None:
            return ([], revision)
        else:
            return ([ self._untag_depth(kv.key.decode('utf-8'))
                      for kv in response.kvs ],
                    revision)

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

    def update(self, path, value, must_be_rev=None):
        """ Updates an existing key. Fails if the key does not exist.

        :param path: Path to update
        :param value: Value to set
        :param from_revision: Fail if found value does not match given
            revision (atomic update)
        :returns: Whether transaction was successful

        """

        tagged_path = self._tag_depth(path)
        value = str(value).encode('utf-8')
        # Put value if version is *not* zero (i.e. it exists)
        txn = self._client.Txn()
        txn.compare(txn.key(tagged_path).version != 0)
        if must_be_rev is not None:
            if must_be_rev.modRevision is None:
                raise ValueError("Did not pass a valid modRevision!")
            txn.compare(txn.key(tagged_path).mod == must_be_rev.modRevision)
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

class Etcd3Revision:
    """Identifies the revision of the database (+ a key)

    This has two parts:

    * `revision` is the database revision. Used for looking up
      specific revisions in the database, for instance for querying a
      consistent snapshot.

    * `modRevision` identifies how often a given key has been modified
      total. This can be used for checking whether a given key has
      changed, for instance to implement an atomic update.
    """

    def __init__(self, revision, modRevision):
        self.revision = revision
        self.modRevision = modRevision

    def __repr__(self):
        return "Etc3Revision({},{})".format(self.revision, self.modRevision)

class Etc3Watcher:
    """Wrapper for etc3 watch requests.

    Enter to start watching the key, at which point 
    """

    def __init__(self, watcher):
        self._watcher = watcher

    def __enter__(self):
        """ Activates the watcher, yielding a queue for updates """

        q = queue.Queue()
        def on_event(event):
            if event.type == etcd3.EventType.PUT:
                q.put((event.value.decode('utf-8'),
                       Etcd3Revision(event.mod_revision, event.mod_revision)))
            else:
                q.put((None, Etcd3Revision(event.mod_revision, None)))

        self._watcher.onEvent(on_event)
        self._watcher.runDaemon()
        return q

    def __exit__(self, *args):
        """ Deactivates the watcher """
        self._watcher.clear_callbacks()
        self._watcher.stop()
