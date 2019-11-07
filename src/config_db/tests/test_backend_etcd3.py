"""Tests for etcd3 backend."""

# pylint: disable=missing-docstring,redefined-outer-name,invalid-name

import os
import time
import pytest

from ska_sdp_config import backend

PREFIX = "/__test"


@pytest.fixture(scope="session")
def etcd3():
    host = os.getenv('SDP_TEST_HOST', '127.0.0.1')
    port = os.getenv('SDP_CONFIG_PORT', '2379')
    with backend.Etcd3(host=host, port=port) as etcd3:
        etcd3.delete(PREFIX, must_exist=False, recursive=True)
        yield etcd3
        etcd3.delete(PREFIX, must_exist=False, recursive=True)


def test_valid(etcd3):
    with pytest.raises(ValueError, match="must start"):
        etcd3.create("", "")
    with pytest.raises(ValueError, match="must start"):
        etcd3.create("foo", "")
    with pytest.raises(ValueError, match="trailing"):
        etcd3.create(PREFIX + "/", "")
    with pytest.raises(ValueError, match="trailing"):
        etcd3.update(PREFIX + "/", "")
    with pytest.raises(ValueError, match="trailing"):
        etcd3.get(PREFIX + "/")
    with pytest.raises(ValueError, match="trailing"):
        etcd3.watch(PREFIX + "/")
    etcd3.watch(PREFIX + "/", prefix=True)
    with pytest.raises(ValueError, match="trailing"):
        for txn in etcd3.txn():
            txn.get(PREFIX + "/")


def test_create(etcd3):
    key = PREFIX + "/test_create"

    etcd3.create(key, "foo")
    with pytest.raises(backend.Collision):
        etcd3.create(key, "foo")

    # Check value
    v, ver = etcd3.get(key)
    assert v == 'foo'

    # Update, check again. Make sure version was incremented
    etcd3.update(key, 'bar', must_be_rev=ver)
    v2, ver2 = etcd3.get(key)
    assert v2 == 'bar'
    assert ver2.revision > ver.revision
    assert ver2.mod_revision == ver.mod_revision + 1

    # Check that we cannot update the original key if we provide the
    # wrong revision
    with pytest.raises(backend.Vanished):
        etcd3.update(key, 'baz', must_be_rev=ver)
    v2b, ver2b = etcd3.get(key)
    assert v2b == 'bar'
    assert ver2.mod_revision == ver2b.mod_revision

    # Check that we can obtain the previous version
    v3, ver3 = etcd3.get(key, ver)
    assert v3 == 'foo'
    assert ver3.mod_revision == ver.mod_revision

    # Delete key
    etcd3.delete(key)
    with pytest.raises(backend.Vanished):
        etcd3.delete(key)


def test_list(etcd3):

    key = PREFIX + "/test_list"

    # Create a bunch of keys
    etcd3.create(key+"/a", "")
    etcd3.create(key+"/ab", "")
    etcd3.create(key+"/b", "")
    etcd3.create(key+"/ax", "")
    etcd3.create(key+"/ab/c", "")
    etcd3.create(key+"/a/d", "")
    etcd3.create(key+"/a/d/x", "")

    # Try listing
    assert etcd3.list_keys(key+'/')[0] == [
        key+"/a", key+"/ab", key+"/ax", key+"/b"]
    assert etcd3.list_keys(key)[0] == []
    assert etcd3.list_keys(key+"/a")[0] == [
        key+"/a", key+"/ab", key+"/ax"]
    assert etcd3.list_keys(key+"/b")[0] == [
        key+"/b"]
    assert etcd3.list_keys(key+"/a/")[0] == [
        key+"/a/d"]
    assert etcd3.list_keys(key+"/ab/")[0] == [
        key+"/ab/c"]
    assert etcd3.list_keys(key+"/ab")[0] == [
        key+"/ab"]

    # Try listing recursively
    assert etcd3.list_keys(key, recurse=1)[0] == [
        key+"/a", key+"/ab", key+"/ax", key+"/b"]
    assert etcd3.list_keys(key, recurse=(1,))[0] == [
        key+"/a", key+"/ab", key+"/ax", key+"/b"]
    assert etcd3.list_keys(key, recurse=2)[0] == [
        key+"/a", key+"/a/d", key+"/ab", key+"/ab/c",
        key+"/ax", key+"/b"]
    assert etcd3.list_keys(key, recurse=(2,))[0] == [
        key+"/a/d", key+"/ab/c"]
    assert etcd3.list_keys(key+"/", recurse=1)[0] == [
        key+"/a", key+"/a/d", key+"/ab", key+"/ab/c",
        key+"/ax", key+"/b"]
    assert etcd3.list_keys(key, recurse=3)[0] == [
        key+"/a", key+"/a/d", key+"/a/d/x",
        key+"/ab", key+"/ab/c", key+"/ax", key+"/b"]
    assert etcd3.list_keys(key, recurse=[3, 2, 1])[0] == [
        key+"/a", key+"/a/d", key+"/a/d/x",
        key+"/ab", key+"/ab/c", key+"/ax", key+"/b"]
    assert etcd3.list_keys(key+"/a", recurse=2)[0] == [
        key+"/a", key+"/a/d", key+"/a/d/x",
        key+"/ab", key+"/ab/c", key+"/ax"]
    assert etcd3.list_keys(key+"/a/", recurse=1)[0] == [
        key+"/a/d", key+"/a/d/x"]
    assert set(etcd3.list_keys("/", recurse=32)[0]) >= set([
        key+"/a", key+"/a/d", key+"/a/d/x",
        key+"/ab", key+"/ab/c", key+"/ax"])

    # Remove
    etcd3.delete(key, must_exist=False, recursive=True)


def test_lease(etcd3):
    key = PREFIX + "/test_lease"
    with etcd3.lease(ttl=5) as lease:
        etcd3.create(key, "blub", lease=lease)
        with pytest.raises(backend.Collision):
            etcd3.create(key, "blub", lease=lease)
        assert lease.alive()
    # Key should have been removed by lease expiring
    with pytest.raises(backend.Vanished):
        etcd3.delete(key)


def test_delete(etcd3):

    key = PREFIX + "/test_delete"

    # Two passes - with and without deleting keys by PREFIX
    for del_PREFIX in [False, True]:

        # Create deeply recursive structure
        childs = ["/".join([key] + n * ['x']) for n in range(10)]
        for n, child in enumerate(childs):
            etcd3.create(child, n)

        # Create some keys in a parallel structure sharing a PREFIX
        if not del_PREFIX:
            etcd3.create(key + "x", "keep!")
            etcd3.create(key + "x/x", "keep!")

        # Delete root
        etcd3.delete(key, prefix=del_PREFIX)
        for n, child in enumerate(childs):
            if n > 0:
                assert etcd3.get(child)[0] == str(n), child
        assert (etcd3.get(key + "x")[0] is None) == del_PREFIX
        assert etcd3.get(key + "x/x")[0] == "keep!"

        # This should fail now
        with pytest.raises(backend.Vanished):
            etcd3.delete(key, recursive=True, must_exist=True,
                         prefix=del_PREFIX)
        for n, child in enumerate(childs):
            if n > 0:
                assert etcd3.get(child)[0] == str(n), child
        assert (etcd3.get(key + "x")[0] is None) == del_PREFIX
        assert etcd3.get(key + "x/x")[0] == "keep!"

        # But this one should work, and remove remaining keys
        # (except those with the same PREFIX but different path
        #  unless we set the option before)
        etcd3.delete(key, recursive=True, must_exist=False,
                     prefix=del_PREFIX)
        for child in childs:
            assert etcd3.get(child)[0] is None, child
        assert (etcd3.get(key + "x")[0] is None) == del_PREFIX
        assert (etcd3.get(key + "x/x")[0] is None) == del_PREFIX


@pytest.mark.timeout(10)
def test_watch(etcd3):

    key = PREFIX + "/test_watch"

    etcd3.delete(key, must_exist=False)

    with etcd3.watch(key) as watch:

        # Reduce likelihood of races between the watch start and the
        # first update
        time.sleep(0.1)

        etcd3.create(key, "bla")
        etcd3.update(key, "bla2")
        etcd3.update(key, "bla3")
        etcd3.update(key, "bla4")
        etcd3.delete(key)

        assert watch.get()[1] == 'bla'
        assert watch.get()[1] == 'bla2'
        assert watch.get()[1] == 'bla3'
        assert watch.get()[1] == 'bla4'
        assert watch.get()[1] is None

    # Check that we can watch all children
    with etcd3.watch(key+"/", prefix=True) as watch:
        time.sleep(0.1)

        etcd3.create(key+"/ab", "bla")
        etcd3.create(key+"/ac", "bla2")
        etcd3.create(key+"/ba", "bla3")
        etcd3.create(key+"/ad", "bla4")

        assert watch.get()[0:2] == (key+"/ab", 'bla')
        assert watch.get()[0:2] == (key+"/ac", 'bla2')
        assert watch.get()[0:2] == (key+"/ba", 'bla3')
        assert watch.get()[0:2] == (key+"/ad", 'bla4')

    etcd3.delete(key, must_exist=False, recursive=True)

    # Check that we can also watch multiple keys with the same PREFIX
    with etcd3.watch(key+"/a", prefix=True) as watch:
        time.sleep(0.1)

        etcd3.create(key+"/ab", "bla")
        etcd3.create(key+"/ac", "bla2")
        etcd3.create(key+"/ba", "bla3")
        etcd3.create(key+"/ad", "bla4")

        assert watch.get()[0:2] == (key+"/ab", 'bla')
        assert watch.get()[0:2] == (key+"/ac", 'bla2')
        assert watch.get()[0:2] == (key+"/ad", 'bla4')

    etcd3.delete(key, recursive=True, must_exist=False)


def test_transaction_simple(etcd3):

    key = PREFIX + "/test_txn"
    key2 = PREFIX + "/test_txn/2"

    # Make sure we can do simple things, like reading a key
    for txn in etcd3.txn():
        txn.create(key, "test")
    assert etcd3.get(key)[0] == "test"
    for txn in etcd3.txn():
        assert txn.get(key) == "test"
        assert txn.get(key) == "test"
    for txn in etcd3.txn():
        txn.update(key, "test2")
    assert etcd3.get(key)[0] == "test2"
    for txn in etcd3.txn():
        txn.update(key, "test3")
        assert txn.get(key) == "test3"
    assert etcd3.get(key)[0] == "test3"
    etcd3.delete(key)
    for txn in etcd3.txn():
        txn.create(key, "test")
        assert txn.get(key) == "test"
        txn.update(key, "test2")
        assert txn.get(key) == "test2"
    assert etcd3.get(key)[0] == "test2"

    for txn in etcd3.txn():
        assert txn.get(key2) is None
        assert txn.get(key) == "test2"
        txn.create(key2, "test2")
        assert txn.get(key2) == "test2"
        txn.update(key, "test4")
        assert txn.get(key) == "test4"
        assert txn.get(key2) == "test2"
    assert etcd3.get(key2)[0] == "test2"

    etcd3.delete(key, recursive=True)


def test_transaction_delete(etcd3):

    key = PREFIX + "/test_txn_delete"

    etcd3.create(key, "1")
    for txn in etcd3.txn():
        txn.delete(key)
    assert etcd3.get(key)[0] is None

    etcd3.create(key, "1")
    for txn in etcd3.txn():
        with pytest.raises(backend.Collision):
            txn.create(key, "2")
        txn.delete(key)
        with pytest.raises(backend.Vanished):
            txn.update(key, "3")
        with pytest.raises(backend.Vanished):
            txn.delete(key)
        txn.create(key, "4")
    assert etcd3.get(key)[0] == "4"

    etcd3.delete(key)
    for txn in etcd3.txn():
        with pytest.raises(backend.Vanished):
            txn.update(key, "3")
        with pytest.raises(backend.Vanished):
            txn.delete(key)
        txn.create(key, "4")
        with pytest.raises(backend.Collision):
            txn.create(key, "2")
        txn.update(key, "3")
        txn.delete(key)
    assert etcd3.get(key)[0] is None


def test_transaction_lease(etcd3):

    key = PREFIX + "/test_txn_lease"

    with etcd3.lease(ttl=5) as lease:
        for txn in etcd3.txn():
            txn.create(key, "blub", lease=lease)
            with pytest.raises(backend.Collision):
                txn.create(key, "blub", lease=lease)
        for txn in etcd3.txn():
            assert txn.get(key) == "blub"
        assert lease.alive()
    for txn in etcd3.txn():
        assert txn.get(key) is None


# pylint: disable=W0631
def test_transaction_conc(etcd3):

    key = PREFIX + "/test_txn2"
    key2 = key + "/2"
    key3 = key + "/3"
    key4 = key + "/4"

    counter = {'i': 0}

    def increase_counter():
        counter['i'] += 1

    # Ensure reading is consistent
    etcd3.create(key, "1")
    etcd3.create(key2, "1")
    for i, txn in enumerate(etcd3.txn()):
        txn.on_commit(increase_counter)
        # First "get" should bake in revision, so subsequent calls
        # return values from this point in time
        txn.get(key)
        etcd3.update(key2, "2")
        assert txn.get(key2)[0] == "1"
    # As this transaction is not writing anything, it will not get repeated
    assert i == 0
    assert counter['i'] == 0  # No commit happens

    # Now check the behaviour if we write something. This time we
    # might be writing an inconsistent value to the database, so the
    # transaction needs to be repeated (10 times!)
    for i, txn in enumerate(etcd3.txn()):
        txn.on_commit(increase_counter)
        v2 = txn.get(key2)
        if i < 10:
            etcd3.update(key2, i)
        txn.create(key3, int(v2) + 1)
    assert i == 10
    assert etcd3.get(key2)[0] == "9"
    assert etcd3.get(key3)[0] == "10"
    assert counter['i'] == 1
    counter['i'] = 0

    # Same experiment, but with a key that didn't exist yet
    for i, txn in enumerate(etcd3.txn()):
        txn.on_commit(increase_counter)
        txn.get(key4)
        if i == 0:
            etcd3.create(key4, "1")
        txn.update(key3, int(i))
    assert i == 1
    assert counter['i'] == 1
    etcd3.delete(key4)
    counter['i'] = 0

    # This is especially important because it underpins the safety
    # check of create():
    for i, txn in enumerate(etcd3.txn()):
        txn.on_commit(increase_counter)
        # "Succeeds" first time only to cause the transaction to get
        # re-run to find a failure the second time around
        if i == 0:
            txn.create(key4, "2")
            etcd3.create(key4, "1")
        if i == 1:
            with pytest.raises(backend.Collision):
                txn.create(key4, "2")
    assert i == 1
    assert counter['i'] == 0  # No commit

    etcd3.delete(key, recursive=True)


def test_transaction_list(etcd3):

    key = PREFIX + "/test_txn_list"
    keys = [key+"/"+str(i) for i in range(5)]
    keys_sub = [key+"/sub" for key in keys]
    for txn in etcd3.txn():
        for k in keys:
            txn.create(k, k)
            txn.create(k+"/sub", k+"/sub")

    # Ensure that we can list the keys
    assert etcd3.list_keys(key+'/')[0] == keys
    for txn in etcd3.txn():
        assert txn.list_keys(key+'/') == keys
        assert txn.list_keys(key+'/', recurse=1) == sorted(keys + keys_sub)
        assert txn.list_keys(key+'/', recurse=(1,)) == keys_sub
    for txn in etcd3.txn():
        assert txn.list_keys(key+'/', recurse=(1,)) == keys_sub

    # Ensure that we can add another key into the range and have it
    # appear to the transaction *before* we commit
    keys.append(key+"/xxx")
    assert etcd3.list_keys(key+'/')[0] == keys[:-1]
    for txn in etcd3.txn():
        assert txn.list_keys(key+'/') == keys[:-1]
        txn.create(key+"/xxx", "xxx")
        assert txn.list_keys(key+'/', recurse=3) == sorted(keys + keys_sub)
        assert txn.list_keys(key+'/') == keys
        assert etcd3.list_keys(key+'/')[0] == keys[:-1]
    assert etcd3.list_keys(key+'/')[0] == keys

    # Test iteratively building up
    etcd3.delete(key, recursive=True, must_exist=False)
    for i, k in enumerate(keys):
        for txn in etcd3.txn():
            assert txn.list_keys(key+'/') == keys[:i]
            txn.create(k, k)

    # Removing keys causes a re-run, but a value update does not.
    for i, txn in enumerate(etcd3.txn()):
        txn.list_keys(key+'/')
        etcd3.delete(keys[5], must_exist=False)
        txn.update(keys[4], keys[3-i])  # stand-in side effect
    assert i == 1
    assert etcd3.get(keys[5])[0] is None

    # Adding a new key into the range should also invalidate the transaction
    for i, txn in enumerate(etcd3.txn()):
        txn.list_keys(key+'/')
        if i == 0:
            etcd3.create(keys[5], keys[5])
        txn.update(keys[4], keys[3-i])  # stand-in side effect
    assert i == 1
    etcd3.delete(key, recursive=True, must_exist=False)


# pylint: disable=W0212
@pytest.mark.timeout(2)
def test_transaction_wait(etcd3):

    key = PREFIX + "/test_txn_wait"

    etcd3.create(key, "0")

    # Test straightforward looping
    values_seen = []
    for i, txn in enumerate(etcd3.txn()):
        values_seen.append(txn.get(key))
        if i < 4:
            txn.loop()
        if i == 0:
            for j in range(1, 5):
                etcd3.update(key, str(j))
    assert values_seen == ['0'] + 4 * ['4']

    # Now test with watch flag set. This would block unless we make
    # the appropriate number of updates. Note that in contrast to the
    # last example, here we have a guarantee that we see every
    # individual value.
    values_seen = []
    for i, txn in enumerate(etcd3.txn()):
        values_seen.append(txn.get(key))
        if i < 4:
            txn.loop(watch=True)
            etcd3.update(key, str(i+1))
    assert i == 4
    assert values_seen == ['4', '1', '2', '3', '4']
    assert not txn._watchers

    # Make sure we can successfully cancel underlying watchers using "break"
    values_seen = []
    for i, txn in enumerate(etcd3.txn()):
        values_seen.append(txn.get(key))
        if i == 0:
            etcd3.update(key, "x")
            txn.loop(watch=True)
        if i == 1:
            assert len(txn._watchers) == 1
            break
    assert not txn._watchers
    assert i == 1
    assert values_seen == ['4', 'x']


@pytest.mark.timeout(2)
def test_transaction_watchers(etcd3):

    key = PREFIX + "/test_txn_watchers"
    etcd3.create(key, "test")

    # Test that watchers get cancelled as we read fewer values
    # pylint: disable=W0212
    def watcher_count(typ, txn):
        return len([() for wk in txn._watchers if wk[0] == typ])
    for i, txn in enumerate(etcd3.txn()):
        txn.get(key)
        if i == 0:
            # No watch request yet
            assert watcher_count("get", txn) == 0
            assert watcher_count("list", txn) == 0
            txn.list_keys(key+"/")
            txn.get(key+"/1")
            txn.get(key+"/2")
        if i == 1:
            # Get watcher for "key", list watcher for "key/*"
            assert watcher_count("get", txn) == 1
            assert watcher_count("list", txn) == 1
            txn.get(key+"/1")
            txn.get(key+"/2")
        if i == 2:
            # Get watchers for "key", "key/1" and "key/2"
            assert watcher_count("get", txn) == 3
            assert watcher_count("list", txn) == 0
            txn.get(key+"/1")
        if i == 3:
            # Get watchers for "key" and "key/1"
            assert len(txn._watchers) == 2
        if i == 4:
            assert len(txn._watchers) == 1
        else:
            etcd3.update(key, str(i))
            txn.loop(watch=True)
    assert not txn._watchers
    assert i == 4

    etcd3.delete(key, recursive=True, must_exist=False)


@pytest.mark.timeout(2)
def test_transaction_watch_list(etcd3):

    key = PREFIX + "/test_txn_watchers"
    etcd3.create(key + "/a", "test")
    etcd3.create(key + "/b", "test2")
    etcd3.create(key + "/c", "test3")

    for i, txn in enumerate(etcd3.txn()):
        keys = txn.list_keys(key+"/")
        if i == 0:
            assert not txn._got_timeout
            assert keys == [key + "/a", key + "/b", key + "/c"]
            # Deleting a key in range should cause loop
            etcd3.delete(key + "/a")
        if i == 1:
            assert not txn._got_timeout
            assert keys == [key + "/b", key + "/c"]
            # Creating a key in range should cause loop
            etcd3.create(key + "/a", "asd")
        if i == 2:
            assert not txn._got_timeout
            assert keys == [key + "/a", key + "/b", key + "/c"]
            # Updating a key should *not* cause a loop
            etcd3.update(key + "/a", "asd2")
        if i == 3:
            assert txn._got_timeout
            assert keys == [key + "/a", key + "/b", key + "/c"]
            # Except of course if we also read it
            txn.get(key + "/a")
            etcd3.update(key + "/a", "asd3")
        if i == 4:
            assert not txn._got_timeout
            assert keys == [key + "/a", key + "/b", key + "/c"]
            # Similarly, updating keys at higher or lower levels
            # should be ignored
            etcd3.create(key, "parent")
            etcd3.create(key + "/a/b", "child")
        if i == 5:
            assert txn._got_timeout
            assert keys == [key + "/a", key + "/b", key + "/c"]
            break
        # Use a timeout to make sure we don't block. A bit of an
        # inexact science.
        txn.loop(watch=True, watch_timeout=0.5)

    etcd3.delete(key, must_exist=False, recursive=True)


@pytest.mark.timeout(10)
def test_transaction_retries(etcd3):

    key = PREFIX + "/test_txn_retries"

    etcd3.create(key, "0")

    # Check that we actually give up eventually
    with pytest.raises(RuntimeError, match="9 retries"):
        for i, txn in enumerate(etcd3.txn(max_retries=9)):
            v2 = txn.get(key)
            etcd3.update(key, i)
            txn.update(key, v2 + "x")
    assert i == 9
    assert etcd3.get(key)[0] == "9"

    # Check that the counter resets if a transactions succeeds, even
    # if we loop explicitly
    with pytest.raises(RuntimeError, match="5 retries"):
        for i, txn in enumerate(etcd3.txn(max_retries=5)):
            v2 = txn.get(key)
            if i != 5:
                etcd3.update(key, i)
            txn.update(key, v2 + "x")
            txn.loop()
    assert i == 11


if __name__ == '__main__':
    pytest.main()
