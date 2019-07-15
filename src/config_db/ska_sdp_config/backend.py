
import etcd3
import queue as queue_m
import time

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
        """ Creates a new transaction
        """
        return Etcd3Transaction(self, max_retries)

    def get(self, path, revision=None, watch=False):
        """
        Get value of a key

        :param path: Path of key to query
        :param revision: Database revision for which to read key
        :returns: (value, revision). value is None if it doesn't exist
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

    def watch(self, path, prefix=False, revision=None):
        """
        Watch key or key range.  Use a path ending with `'/'` in
        combination with `prefix` to watch all child keys.

        :param path: Path of key to query, or prefix of keys.
        :param prefix: Watch for keys with given prefix if set
        :param revision: Database revision from which to watch
        :returns: `Etcd3Watcher` object for watch request
        """

        if path[-1] == '/' and not prefix:
            raise ValueError("Path should not have a trailing '/'!")
        tagged_path = self._tag_depth(path)
        rev = (None if revision is None else revision.revision)

        # Set up watcher
        watcher = self._client.Watcher(
            tagged_path, start_revision=rev, prev_kv=True, prefix=prefix)
        return Etc3Watcher(watcher, self)

    def list_keys(self, path, revision=None):
        """
        List keys under given path

        :param path: Prefix of keys to query. Append '/' to list
           child paths.
        :param revision: Database revision for which to list
        :returns: (sorted key list, revision)
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
            return (sorted([ self._untag_depth(kv.key.decode('utf-8'))
                             for kv in response.kvs ]),
                    revision)

    def create(self, path, value, lease=None):
        """
        Create a key at the path in question and initialises it with the
        value. Fails if the key already exists. If a lease is given,
        the key will automatically get deleted once it expires.

        :param path: Path to create
        :param value: Value to set
        :param lease: Lease to associate
        :raises: Collision
        """

        # Prepare parameters
        if path[-1] == '/':
            raise ValueError("Path should not have a trailing '/'!")
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
        :param must_be_rev: Fail if found value does not match given
            revision (atomic update)
        :raises: Vanished
        """

        # Validate parameters
        if path[-1] == '/':
            raise ValueError("Path should not have a trailing '/'!")
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
    """Exception generated if we attempt to create a key that does already
    exist."""

    def __init__(self, path, message):
        self.path = path
        super(RuntimeError, self).__init__(message)

    def __str__(self):
        return super(RuntimeError, self).__str__()

class Vanished(RuntimeError):
    """Exception generated if we attempt to update a key that does not
    exist."""

    def __init__(self, path, message):
        self.path = path
        super(RuntimeError, self).__init__(message)

    def __str__(self):
        return super(RuntimeError, self).__str__()

class Etcd3Revision(object):
    """Identifies the revision of the database

    This has two parts:

    * `revision` is the database revision at the point in time when
      the query was made. Can be used for querying a consistent
      snapshot.

    * `modRevision` given the revision when a key was last
      modified. This can be used for checking whether a key has
      changed, for instance to implement an atomic update.
    """

    def __init__(self, revision, modRevision):
        self.revision = revision
        self.modRevision = modRevision

    def __repr__(self):
        return "Etc3Revision({},{})".format(self.revision, self.modRevision)

class Etc3Watcher(object):
    """Wrapper for etc3 watch requests.

    Entering the watcher using a `with` block yields a queue of `(key,
    val, rev)` triples.
    """

    def __init__(self, watcher, backend):
        self._watcher = watcher
        self._backend = backend
        self.queue = None

    def start(self, queue=None):
        """ Activates the watcher, yielding a queue for updates """

        if queue is None:
            self.queue = queue = queue_m.Queue()
        def on_event(event):
            key = self._backend._untag_depth(event.key.decode('utf-8'))
            if event.type == etcd3.EventType.PUT:
                val = event.value.decode('utf-8')
                rev = Etcd3Revision(event.mod_revision, event.mod_revision)
            else:
                val = None
                rev = Etcd3Revision(event.mod_revision, event.mod_revision)
            queue.put((key, val, rev))

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
    """
    Makes it possible to string multiple queries and updates together
    in a way that we can guarantee atomicity. This might occassionally
    require iterating the transaction.
    """

    # TODO/ideas:
    #
    # Ranged deletes - in contrast to the main backend we cannot
    # release a range of keys (especially recursively) in a
    # transaction yet. The tricky bit is to make this consistent with
    # the rest of the transaction machinery and properly
    # atomic. Easiest solution might just be to simply use a bunch of
    # list_key and single delete calls to get the same effect. Would
    # be slightly inefficient, but would get the job done.
    #
    # Caching - especially when looping a transaction most of the
    # queried data from the database might still be valid. So after a
    # loop we could just migrate the known information to a _cache
    # (plus any further information we got from watches). Then once
    # the "new" database revision has been determined we might just
    # send one cheap query to the database to figure out which bits of
    # it are still current.
    #
    # Cheaper update/create checks - right now we query the old value
    # of the key on every update/create call, even though we are only
    # interested in whether or not the key exists. We could instead
    # query this along the same lines as list_keys. Not entirely sure
    # this is worthwhile though, given that it is quite typical to
    # "get" a key before "updating" it anyway, and collisions on
    # "create" should be quite rare.

    def __init__(self, backend, max_retries=64):
        self._backend = backend
        self._max_retries = max_retries

        self._revision = None # Revision backed in after first read
        self._get_queries = {} # Query log
        self._list_queries = {} # Query log
        self._updates = {} # Delayed updates

        self._committed = False
        self._loop = False
        self._watch = False
        self._watch_timeout = None
        self._got_timeout = False # For test cases
        self._retries = 0

        self._watchers = {}
        self._watch_queue = queue_m.Queue()

    def _ensure_uncommitted(self):
        if self._committed:
            raise RuntimeError("Attempted to modify committed transaction!")

    def get(self, path):
        """
        Get value of a key

        :param path: Path of key to query
        :returns: Key value. None if it doesn't exist.
        """

        self._ensure_uncommitted()

        # Check whether it was written as part of this transaction
        if path in self._updates:
            return self._updates[path][0]

        # Check whether we already have the request response
        if path in self._get_queries:
            return self._get_queries[path][0]

        # Perform get request
        v, rev = self._get_queries[path] = \
            self._backend.get(path, revision=self._revision)

        # Set revision, if not already done so
        if self._revision is None:
            self._revision = rev
        return v

    def list_keys(self, path):
        """
        List keys under given path

        :param path: Prefix of keys to query. Append '/' to list
           child paths.
        :returns: sorted key list
        """

        self._ensure_uncommitted()

        # We might have created or deleted an uncommitted key that
        # falls into the range - add to list
        tagged_path = self._backend._tag_depth(path)
        matching_vals = [
            kv for kv in self._updates.items()
            if self._backend._tag_depth(kv[0]).startswith(tagged_path) ]
        added_keys = set([ key for key, val in matching_vals
                           if val is not None ])
        removed_keys = set([ key for key, val in matching_vals
                             if val is None ])

        # Check whether we already have the request response
        if path in self._list_queries:
            return sorted(set(self._list_queries[path][0])
                          - removed_keys | added_keys)

        # Perform request
        v, rev = self._list_queries[path] = self._backend.list_keys(
            path, revision=self._revision)

        # Set revision, return
        if self._revision is None:
            self._revision = rev
        return sorted(set(v) - removed_keys | added_keys)

    def create(self, path, value, lease=None):
        """Create a key at the path in question and initialises it with the
        value. Fails if the key already exists. If a lease is given,
        the key will automatically get deleted once it expires.

        :param path: Path to create
        :param value: Value to set
        :param lease: Lease to associate
        :raises: Collision
        """

        self._ensure_uncommitted()

        # Attempt to get the value - mainly to check whether it exists
        # and put it into the query log
        result = self.get(path)
        if result is not None:
            raise Collision(path, "Cannot create {}, as it already exists!".format(path))

        # Add update request
        self._updates[path] = (value, lease)

    def update(self, path, value):
        """ Updates an existing key. Fails if the key does not exist.

        :param path: Path to update
        :param value: Value to set
        :raises: Vanished
        """

        self._ensure_uncommitted()

        # As with "update"
        result = self.get(path)
        if result is None:
            raise Vanished(path, "Cannot update {}, as it does not exist!".format(path))

        # Add update request
        self._updates[path] = (value, None)

    def delete(self, path, must_exist = True):
        """
        Deletes the given key or key range

        :param path: Path (prefix) of keys to remove
        :param must_exist: Fail if path does not exist?
        """

        # As with "update"
        result = self.get(path)
        if result is None:
            raise Vanished(path, "Cannot delete {}, as it does not exist!".format(path))

        # Add delete request
        self._updates[path] = (None, None)

    def commit(self):
        """
        Commits the transaction. This can fail, in which case the
        transaction must get `reset` and built up again.
        :returns: Whether the commit succeeded
        """

        self._ensure_uncommitted()

        # If we have made no updates, we don't need to verify the log
        if len(self._updates) == 0:
            self._committed = True
            return True

        # Create transaction
        txn = self._backend._client.Txn()

        # Verify get() calls from the query log
        for path, (_ , rev) in self._get_queries.items():
            tagged_path = self._backend._tag_depth(path)

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

        # Verify list_keys() calls from the query log
        for path, (result, rev) in self._list_queries.items():
            tagged_path = self._backend._tag_depth(path)

            # Make sure that all returned keys still exist
            for res_path in result:
                tagged_res_path = self._backend._tag_depth(res_path)
                txn.compare(txn.key(tagged_res_path).version > 0)

            # Also check that no new keys have entered the range
            # (by checking whether the request would contain any
            # keys with a newer create revision than our request)
            txn.compare(txn.key(tagged_path, prefix=True).create
                        < self._revision.revision+1)

        # Commit changes. Note that the dictionary guarantees that we
        # only update any key at most once.
        for path, (value, lease) in self._updates.items():
            tagged_path = self._backend._tag_depth(path)
            lease_id = (None if lease is None else lease.ID)
            if value is None:
                txn.success(txn.delete(tagged_path, value, lease_id))
            else:
                txn.success(txn.put(tagged_path, value, lease_id))

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
        self._get_queries = {}
        self._list_queries = {}
        self._updates = {}
        self._committed = False
        self._loop = False
        self._watch = False
        self._watch_timeout = None

    def loop(self, watch=False, watch_timeout=None):
        """Always repeat transaction execution, even if it succeeds

        :param watch: Once the transaction succeeds, block until one of
           the values read changes, then loop the transaction
        """

        if self._loop:
            # If called multiple times, looping immediately takes precedence
            self._watch = (self._watch and watch)
        else:
            self._loop = True
            self._watch = watch
        if watch and watch_timeout is not None:
            self._watch_timeout = watch_timeout

    def __iter__(self):

        try:

            while self._retries <= self._max_retries:

                # Should build up a transaction
                yield self

                # Try to commit, count how many times we have tried
                if not self.commit():
                    self._retries += 1
                else:
                    self._retries = 0

                    # No further loop?
                    if not self._loop:
                        return

                    # Use watches? Then wait for something to happen
                    # before looping.
                    if self._watch:
                        self.watch()

                # Repeat after reset otherwise
                self.reset()

        finally:
            self.clear_watch()

        # Ran out of repeats? Fail
        raise RuntimeError("Transaction did not succeed after {} retries!"
                           .format(self._max_retries))

    def clear_watch(self):

        # Remove watchers
        for watcher in self._watchers.values():
            watcher.stop()
        self._watchers = {}

    def _update_watchers(self):

        # Watch any ranges we listed. Note that this will trigger also
        # on key updates, we will filter that below.
        prefixes = []
        active_watchers = set()
        for path in self._list_queries:
            query = ('list', path)
            # Add tagged prefixes so we can check for key overlap later
            prefixes.append(self._backend._tag_depth(path))
            active_watchers.add(query)
            # Start a watcher, if required
            if self._watchers.get(query) is None:
                self._watchers[query] = self._backend.watch(
                    path, revision=self._revision, prefix=True)
                self._watchers[query].start(self._watch_queue)

        # Watch any individual key we read
        for path in self._get_queries:
            query = ('get', path)

            # Check that we are not already watching this key as
            # part of a range. This is basically using the
            # above-mentioned property of range watches to our
            # advantage. This is actually a fairly important
            # optimisation, as it means that listing keys followed
            # by iterating over the values won't create extra
            # watches here!
            tagged_path = self._backend._tag_depth(path)
            if not any([ tagged_path.startswith(prefix) for prefix in prefixes]):
                active_watchers.add(query)
                # Start individual watcher, if required
                if self._watchers.get(query) is None:
                    self._watchers[query] = self._backend.watch(
                        path, revision=self._revision)
                    self._watchers[query].start(self._watch_queue)

        # Remove any watchers that we are not currently using. Note
        # that we only do this on the next watch() call, so watchers
        # will be kept alive through transaction failures *and*
        # non-waiting loops. So as long as the set of keys waited on
        # is relatively constant (and ideally forms ranges), we will
        # not generate much churn here.
        for query, watcher in list(self._watchers.items()):
            if query not in active_watchers:
                watcher.stop()
                del self._watchers[query]

    def watch(self):
        """Wait for a change on one of the values read. Returns the revision
        at which a change was detected."""

        # Make sure the watchers we have in place match what we read
        self._update_watchers()

        # Wait for updates from the watcher queue
        block = True
        revision = self._revision
        start_time = time.time()
        while True:

            # Determine timeout
            timeout = None
            if self._watch_timeout is not None:
                timeout = max(0, start_time + self._watch_timeout - time.time())

            # Wait for something to get pushed on the queue
            try:
                path, value, rev = self._watch_queue.get(block, timeout)
            except queue_m.Empty:
                self._got_timeout = block
                return revision

            # Check that revision is newer (prevent duplicated updates)
            if rev.revision <= revision.revision:
                continue

            # Are we waiting on a value change of this one?
            if path not in self._get_queries:

                # Are we getting this because of one of the list queries?
                tagged_path = self._backend._tag_depth(path)
                found_match = False
                for list_path, (result, _) in self._list_queries.items():
                    if tagged_path.startswith(self._backend._tag_depth(list_path)):

                        # We should not notify for a value change,
                        # only if a key was added / removed. Good
                        # thing we can check that using the log.
                        if value is None or path not in result:
                            found_match = True
                            break

                # Otherwise this is either a misfire from an old
                # watcher, or a value update from a list watcher (see
                # above). Ignore.
                if not found_match:
                    continue

            # Alright, we can stop waiting. However, we will attempt
            # to clear the queue before we do so, as we might get a
            # lot of updates in batch
            revision = rev
            block = False
