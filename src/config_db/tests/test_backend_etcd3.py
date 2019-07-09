
from ska_sdp_config import backend

import pytest
import multiprocessing
import time

prefix = "/__test"

@pytest.fixture(scope="session")
def etcd3():
    with backend.Etcd3() as etcd3:
        etcd3.delete(prefix, must_exist=False, recursive=True)
        yield etcd3
        etcd3.delete(prefix, must_exist=False, recursive=True)

def test_valid(etcd3):
    with pytest.raises(ValueError, match="trailing"):
        etcd3.get(prefix + "/")
    with pytest.raises(ValueError, match="trailing"):
        etcd3.watch(prefix + "/")

def test_create(etcd3):
    key = prefix + "/test_create"

    etcd3.create(key, "foo")
    with pytest.raises(backend.Collision):
        etcd3.create(key, "foo")

    # Check value
    v,ver = etcd3.get(key)
    assert v == 'foo'

    # Update, check again. Make sure version was incremented
    etcd3.update(key, 'bar', must_be_rev=ver)
    v2,ver2 = etcd3.get(key)
    assert v2 == 'bar'
    assert ver2.revision > ver.revision
    assert ver2.modRevision == ver.modRevision + 1

    # Check that we cannot update the original key if we provide the
    # wrong revision
    with pytest.raises(backend.Vanished):
        etcd3.update(key, 'baz', must_be_rev=ver)
    v2b,ver2b = etcd3.get(key)
    assert v2b == 'bar'
    assert ver2.modRevision == ver2b.modRevision

    # Check that we can obtain the previous version
    v3,ver3 = etcd3.get(key, ver)
    assert v3 == 'foo'

    # Delete key
    etcd3.delete(key)
    with pytest.raises(backend.Vanished):
        etcd3.delete(key)

def test_list(etcd3):

    key = prefix + "/test_list"

    # Create a bunch of keys
    etcd3.create(key+"/a", "")
    etcd3.create(key+"/ab", "")
    etcd3.create(key+"/b", "")
    etcd3.create(key+"/ax", "")
    etcd3.create(key+"/ab/c", "")
    etcd3.create(key+"/a/d", "")
    etcd3.create(key+"/a/d/x", "")

    # Try listing
    assert set(etcd3.list_keys(key+'/')[0]) == set([
        key+"/a", key+"/ab", key+"/b", key+"/ax"])
    assert set(etcd3.list_keys(key)[0]) == set([])
    assert set(etcd3.list_keys(key+"/a")[0]) == set([
        key+"/a", key+"/ab", key+"/ax"])
    assert set(etcd3.list_keys(key+"/b")[0]) == set([
        key+"/b"])
    assert set(etcd3.list_keys(key+"/a/")[0]) == set([
        key+"/a/d"])
    assert set(etcd3.list_keys(key+"/ab/")[0]) == set([
        key+"/ab/c"])
    assert set(etcd3.list_keys(key+"/ab")[0]) == set([
        key+"/ab"])

    # Remove
    etcd3.delete(key, must_exist=False, recursive=True)

def test_lease(etcd3):
    key = prefix + "/test_lease"
    with etcd3.lease(ttl=5) as lease:
        etcd3.create(key, "blub", lease=lease)
        with pytest.raises(backend.Collision):
            etcd3.create(key, "blub", lease=lease)
        assert lease.alive()
    # Key should have been removed by lease expiring
    with pytest.raises(backend.Vanished):
        etcd3.delete(key)

def test_delete(etcd3):

    key = prefix + "/test_delete"

    # Two passes - with and without deleting keys with same prefix
    for del_prefix in [False, True]:

        # Create deeply recursive structure
        childs = [ "/".join([key] + n * ['x']) for n in range(10) ]
        for n, child in enumerate(childs):
            etcd3.create(child, n)

        # Create some keys in a parallel structure sharing a prefix
        if del_prefix == False:
            etcd3.create(key + "x", "keep!")
            etcd3.create(key + "x/x", "keep!")

        # Delete root
        etcd3.delete(key, prefix=del_prefix)
        for n, child in enumerate(childs):
            if n > 0:
                assert etcd3.get(child)[0] == str(n), child
        assert (etcd3.get(key + "x")[0] is None) == del_prefix
        assert etcd3.get(key + "x/x")[0] == "keep!"

        # This should fail now
        with pytest.raises(backend.Vanished):
            etcd3.delete(key, recursive=True, must_exist=True,
                         prefix=del_prefix)
        for n, child in enumerate(childs):
            if n > 0:
                assert etcd3.get(child)[0] == str(n), child
        assert (etcd3.get(key + "x")[0] is None) == del_prefix
        assert etcd3.get(key + "x/x")[0] == "keep!"

        # But this one should work, and remove remaining keys
        # (except those with the same prefix but different path
        #  unless we set the option before)
        etcd3.delete(key, recursive=True, must_exist=False,
                     prefix=del_prefix)
        for child in childs:
            assert etcd3.get(child)[0] is None, child
        assert (etcd3.get(key + "x")[0] is None) == del_prefix
        assert (etcd3.get(key + "x/x")[0] is None) == del_prefix

@pytest.mark.timeout(10)
def test_watch(etcd3):

    key = prefix + "/test_watch"

    etcd3.delete(key, must_exist=False)

    with etcd3.watch(key) as watch:

        # Reduce likelihood of races between the watch start and the
        # first update
        time.sleep(0.1)

        etcd3.create(key, "bla")
        etcd3.update(key, "bla2")
        etcd3.update(key, "bla3")
        etcd3.update(key, "bla4")

        assert watch.get()[1] == 'bla'
        assert watch.get()[1] == 'bla2'
        assert watch.get()[1] == 'bla3'
        assert watch.get()[1] == 'bla4'

def test_transaction_simple(etcd3):

    key = prefix + "/test_txn"
    key2 = prefix + "/test_txn/2"

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
        txn.update(key, "test4")
        assert txn.get(key) == "test4"
        assert txn.get(key2) == "test2"
    assert etcd3.get(key2)[0] == "test2"

    etcd3.delete(key, recursive=True)

def test_transaction_conc(etcd3):

    key = prefix + "/test_txn2"
    key2 = key + "/2"
    key3 = key + "/3"
    key4 = key + "/4"

    # Ensure reading is consistent
    etcd3.create(key, "1")
    etcd3.create(key2, "1")
    for i, txn in enumerate(etcd3.txn()):
        # First "get" should bake in revision, so subsequent calls
        # return values from this point in time
        v1 = txn.get(key)
        etcd3.update(key2, "2")
        assert txn.get(key2)[0] == "1"
    # As this transaction is not writing anything, it will not get repeated
    assert i == 0

    # Now check the behaviour if we write something. This time we
    # might be writing an inconsistent value to the database, so the
    # transaction needs to be repeated (10 times!)
    for i, txn in enumerate(etcd3.txn()):
        v2 = txn.get(key2)
        if i < 10:
            etcd3.update(key2, i)
        txn.create(key3, int(v2) + 1)
    assert i == 10
    assert etcd3.get(key2)[0] == "9"
    assert etcd3.get(key3)[0] == "10"

    # Same experiment, but with a key that didn't exist yet
    for i, txn in enumerate(etcd3.txn()):
        txn.get(key4)
        if i == 0:
            etcd3.create(key4, "1")
        txn.update(key3, int(i))
    assert i == 1
    etcd3.delete(key4)

    # This is especially important because it underpins the safety
    # check of create():
    for i, txn in enumerate(etcd3.txn()):
        # "Succeeds" first time only to cause the transaction to get
        # re-run to find a failure the second time around
        if i == 0:
            txn.create(key4, "2")
            etcd3.create(key4, "1")
        if i == 1:
            with pytest.raises(backend.Collision):
                txn.create(key4, "2")
    assert i == 1

    etcd3.delete(key, recursive=True)

def test_transaction_list(etcd3):

    key = prefix + "/test_txn_list"
    keys = [ key+"/"+str(i) for i in range(10) ]
    for k in keys:
        etcd3.create(k, k)

    # Ensure that we can list the keys
    assert set(etcd3.list_keys(key+'/')[0]) == set(keys)
    for txn in etcd3.txn():
        assert set(txn.list_keys(key+'/')) == set(keys)
    etcd3.delete(key, recursive=True, must_exist=False)

    # Test iteratively building up
    for i,k in enumerate(keys):
        for txn in etcd3.txn():
            txn.create(k, k)
            assert set(txn.list_keys(key+'/')) == set(keys[:i])

    # Removing keys causes a re-run, but a value update does not.
    for i,txn in enumerate(etcd3.txn()):
        txn.list_keys(key+'/')
        etcd3.delete(keys[5], must_exist=False)
        txn.update(keys[4], keys[3-i]) # stand-in side effect
    assert i == 1
    assert etcd3.get(keys[5])[0] is None

    # Adding a new key into the range should also invalidate the transaction
    for i,txn in enumerate(etcd3.txn()):
        txn.list_keys(key+'/')
        if i == 0:
            etcd3.create(keys[5], keys[5])
        txn.update(keys[4], keys[3-i]) # stand-in side effect
    assert i == 1
    etcd3.delete(key, recursive=True, must_exist=False)


def test_transaction_wait(etcd3):

    key = prefix + "/test_txn_wait"

    etcd3.create(key, "0")

    # Test straightforward looping
    values_seen = []
    for i, txn in enumerate(etcd3.txn()):
        values_seen.append(txn.get(key))
        if i < 4:
            txn.loop()
        if i == 0:
            for j in range(1,5):
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
        if i == 0:
            for j in range(1,5):
                etcd3.update(key, str(j))
    assert i == 4
    assert values_seen == ['4','1','2','3','4']
    assert len(txn._watchers) == 0

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
    assert len(txn._watchers) == 0
    assert i == 1
    assert values_seen == ['4','x']

if __name__ == '__main__':
    pytest.main()
