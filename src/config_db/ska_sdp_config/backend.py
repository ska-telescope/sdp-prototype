
import etcd3
import queue as queue_m

class Etcd3(object):

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

    def txn(self, max_retries=64):
        """ Creates a new (STM) transaction
        """
        return Etcd3Transaction(self, max_retries)

    def get(self, path, revision=None, watch=False):
        """
        Get value of a key

        :param path: Path of key to query
        :param revision: Database revision for which to read key
        :returns: (value, revision). value is None if it doesn't exit
        """

        # Check/prepare parameters
        if path[-1] == '/':
            raise ValueError("Path should not have a trailing '/'!")
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
        :param revision: Database revision from which to watch
        :returns: (value, revision). value is None if it doesn't exit
        """

        if path[-1] == '/':
            raise ValueError("Path should not have a trailing '/'!")
        tagged_path = self._tag_depth(path)
        rev = (None if revision is None else revision.revision)

        # Set up watcher
        watcher = self._client.Watcher(tagged_path, start_revision=rev, prev_kv=True)
        return Etc3Watcher(watcher, path)

    def list_keys(self, path, prefix=False, revision=None):
        """
        List keys under current path

        :param path: Prefix of keys to query. Append '/' to list
           child paths
        :param revision: Database revision for which to list
        :returns: (key list, revision)
        """

        # Prepare parameters
        tagged_path = self._tag_depth(path)
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
        if not txn.commit().succeeded:
            raise Collision(path, "Cannot create {}, as it already exists!".format(path))

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
        if not txn.commit().succeeded:
            raise Vanished(path, "Cannot update {}, as it does not exist!".format(path))

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
        if not txn.commit().succeeded:
            raise Vanished(path, "Cannot delete {}, as it does not exist!".format(path))

    def close(self):
        """ Closes the client connection """
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

class Collision(RuntimeError):

    def __init__(self, path, message):
        self.path = path
        super().__init__(message)

    def __str__(self):
        return super(self).__str__()

    def __repr__(self):
        return super().__repr__()

class Vanished(RuntimeError):

    def __init__(self, path, message):
        self.path = path
        super().__init__(message)

    def __str__(self):
        return super().__str__()

    def __repr__(self):
        return super().__repr__()

class Etcd3Revision(object):
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

class Etc3Watcher(object):
    """Wrapper for etc3 watch requests.

    Enter to start watching the key, at which point 
    """

    def __init__(self, watcher, path):
        self._watcher = watcher
        self.path = path
        self.queue = None

    def start(self, queue=None):
        """ Activates the watcher, yielding a queue for updates """

        if queue is None:
            self.queue = queue = queue_m.Queue()
        def on_event(event):
            if event.type == etcd3.EventType.PUT:
                queue.put((self.path, event.value.decode('utf-8'),
                           Etcd3Revision(event.mod_revision, event.mod_revision)))
            else:
                queue.put((self.path, None, Etcd3Revision(event.mod_revision, None)))

        self._watcher.onEvent(on_event)
        self._watcher.runDaemon()

    def stop(self):
        """ Deactivates the watcher """
        self._watcher.clear_callbacks()
        self._watcher.stop()
        self.queue = None

    def __enter__(self):
        self.start()
        return self.queue

    def __exit__(self, *args):
        self.stop()

class Etcd3Transaction(object):

    def __init__(self, backend, max_retries=64):
        self._backend = backend
        self._revision = None
        self._queries = {}
        self._updates = {}
        # TODO: deletes? Might get tricky mixing ranged deletes with
        # create...
        self._max_retries = max_retries
        self._committed = False
        self._loop = False
        self._watch = False

        self._watchers = {}
        self._watch_queue = queue_m.Queue()

    def _ensure_uncommitted(self):
        if self._committed:
            raise RuntimeError("Attempted to modify committed transaction!")

    def get(self, path):

        self._ensure_uncommitted()

        # Check whether it was written as part of this transaction
        if path in self._updates:
            return self._updates[path][0]

        # Check whether we already have the request response
        query = ("get", path)
        if query in self._queries:
            return self._queries[query][0]

        # Perform get request
        v, rev = self._queries[query] = self._backend.get(path, revision=self._revision)

        # Set revision, if not already done so
        if self._revision is None:
            self._revision = rev
        return v

    def list_keys(self, path):

        self._ensure_uncommitted()

        # Check whether any written keys match the description
        updated_keys = [ key for key in self._updates.keys()
                         if key.startswith(path) ]

        # Check whether we already have the request response
        query = ("list_keys", path)
        if query in self._queries:
            return self._queries[query][0]

        # Perform request
        v, rev = self._queries[query] = self._backend.list_keys(
            path, revision=self._revision)

        # Set revision, return
        if self._revision is None:
            self._revision = rev
        return v

    def create(self, path, value, lease=None):

        self._ensure_uncommitted()

        # Attempt to get the value - mainly to check whether it exists
        # and put it into the query log
        result = self.get(path)
        if result is not None:
            raise Collision(path, "Cannot create {}, as it already exists!".format(path))

        # Add update request
        self._updates[path] = (value, lease)

    def update(self, path, value):

        self._ensure_uncommitted()

        # As with "update"
        result = self.get(path)
        if result is None:
            raise Collision(path, "Cannot update {}, as it does not exist!".format(path))

        # Add update request
        self._updates[path] = (value, None)
        return True

    def commit(self):

        self._ensure_uncommitted()

        # If we have made no updates, we don't need to verify the log
        if len(self._updates) == 0:
            self._committed = True
            return True

        # Create transaction
        txn = self._backend._client.Txn()

        # Verify the query log
        for query, result in self._queries.items():

            if query[0] == 'get':
                tagged_path = self._backend._tag_depth(query[1])
                rev = result[1]

                if rev.modRevision is None:
                    # Did not exist? Verify continued non-existance. Note
                    # that it is not possible for the key to have been
                    # created, then deleted again in the meantime.
                    txn.compare(txn.key(tagged_path).version == 0)
                else:
                    # Otherwise check matching modRevision. This
                    # actually guarantees that the key has not been
                    # touched since we read it.
                    txn.compare(txn.key(tagged_path).mod == rev.modRevision)

            elif query[0] == 'list_keys':
                tagged_path = self._backend._tag_depth(query[1])
                rev = result[1]

                # Make sure that all returned keys still exist
                for res_path in result[0]:
                    tagged_res_path = self._backend._tag_depth(res_path)
                    txn.compare(txn.key(tagged_res_path).version > 0)

                # Also check that no new keys have entered the range
                # (by checking whether the request would contain any
                # keys with a newer create revision than our request)
                txn.compare(txn.key(tagged_path, prefix=True).create
                            < self._revision.revision+1)

            else:
                assert False

        # Commit changes. Note that the dictionary guarantees that we
        # only update any key at most once.
        for path, (value, lease) in self._updates.items():
            tagged_path = self._backend._tag_depth(path)
            txn.success(txn.put(tagged_path, value, lease))

        # Done
        self._committed = True
        return txn.commit().succeeded

    def reset(self, revision=None):
        """
        After a call to commit(), resets the transaction so it can be restarted.
        """

        if not self._committed:
            raise RuntimeError("Called reset on an uncomitted transaction!")

        # Reset
        self._revision = revision
        self._queries = {}
        self._updates = {}
        self._committed = False
        self._loop = False
        self._watch = False

    def loop(self, watch=False):
        """Always repeat transaction execution, even if it succeeds

        :param watch: Wait with repeat until one of the values read in the
        transaction changed
        """

        if self._loop:
            # If called multiple times, looping immediately takes precedence
            self._watch = (self._watch and watch)
        else:
            self._loop = True
            self._watch = watch

    def __iter__(self):

        try:

            for _ in range(self._max_retries):

                # Should build up a transaction
                yield self

                # Try to commit, done if succeeded
                if self.commit():

                    # No further loop?
                    if not self._loop:
                        return

                    # Set watches?
                    if self._watch:
                        # Wait for something to happen
                        rev = self.watch()
                        # Reset setting new revision
                        self.reset(rev)
                        continue

                # Repeat after reset otherwise
                self.reset()

        finally:
            self.clear_watch()

        # Ran out of repeats? Fail
        raise RuntimeError("Transaction did not succeed after {} retries!"
                           .format(self.max_retries))

    def clear_watch(self):

        # Remove watchers
        for watcher in self._watchers.values():
            watcher.stop()
        self._watchers = {}

    def watch(self):
        """Wait for a change on one of the values read. Returns the revision
        at which a change was detected."""

        # Make sure we have a watcher on every key read
        # (TODO: lists)
        for typ, key in self._queries:
            if typ == 'get' and self._watchers.get(key) is None:
                self._watchers[key] = self._backend.watch(key, revision=self._revision)
                self._watchers[key].start(self._watch_queue)

        # TODO: remove watches that are not used any more?

        while True:

            # Wait for something to get pushed on the queue
            path, value, rev = self._watch_queue.get()

            # Check that revision is newer (prevent duplicated updates)
            if rev.revision <= self._revision.revision:
                continue

            # Check that it is actually something we are waiting on
            if ('get', path) not in self._queries:
                continue

            # Alright, finished waiting
            return rev
