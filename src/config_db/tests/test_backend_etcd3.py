
from ska_sdp_config import backend

import pytest

prefix = "/__test"

@pytest.fixture(scope="session")
def etcd3():
    etcd3 = backend.BackendEtcd3()
    assert etcd3.delete(prefix, must_exist=False, recursive=True)
    return etcd3

def test_create(etcd3):
    key = prefix + "/test_create"

    assert etcd3.create(key, "foo")
    assert not etcd3.create(key, "foo")

    # Check value
    v,ver = etcd3.get(key)
    assert v == 'foo'

    # Update, check again. Make sure version was incremented
    assert etcd3.update(key, 'bar', must_be_rev=ver)
    v2,ver2 = etcd3.get(key)
    assert v2 == 'bar'
    assert ver2.revision > ver.revision
    assert ver2.modRevision == ver.modRevision + 1

    # Check that we cannot update the original key if we provide the
    # wrong revision
    assert not etcd3.update(key, 'baz', must_be_rev=ver)
    v2b,ver2b = etcd3.get(key)
    assert v2b == 'bar'
    assert ver2.modRevision == ver2b.modRevision

    # Check that we can obtain the previous version
    v3,ver3 = etcd3.get(key, ver)
    assert v3 == 'foo'

    # Delete key
    assert etcd3.delete(key)
    assert not etcd3.delete(key)

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
    assert set(etcd3.list_keys(key)[0]) == set([
        key+"/a", key+"/ab", key+"/b", key+"/ax"])
    assert set(etcd3.list_keys(key, prefix=True)[0]) == set([])
    assert set(etcd3.list_keys(key+"/a", prefix=True)[0]) == set([
        key+"/a", key+"/ab", key+"/ax"])
    assert set(etcd3.list_keys(key+"/b", prefix=True)[0]) == set([
        key+"/b"])
    assert set(etcd3.list_keys(key+"/a")[0]) == set([
        key+"/a/d"])
    assert set(etcd3.list_keys(key+"/ab")[0]) == set([
        key+"/ab/c"])
    assert set(etcd3.list_keys(key+"/ab", prefix=True)[0]) == set([
        key+"/ab"])

    # Remove
    etcd3.delete(key, must_exist=False, recursive=True)

def test_lease(etcd3):
    key = prefix + "/test_lease"
    with etcd3.lease(ttl=5) as lease:
        assert etcd3.create(key, "blub", lease=lease)
        assert not etcd3.create(key, "blub", lease=lease)
        assert lease.alive()
    # Key should have been removed by lease expiring
    assert not etcd3.delete(key)

def test_delete(etcd3):

    key = prefix + "/test_delete"

    # Two passes - with and without deleting keys with same prefix
    for del_prefix in [False, True]:

        # Create deeply recursive structure
        childs = [ "/".join([key] + n * ['x']) for n in range(10) ]
        for n, child in enumerate(childs):
            etcd3.create(child, n)

        # Create some keys in a parallel structure sharing a prefix
        etcd3.create(key + "x", "keep!")
        etcd3.create(key + "x/x", "keep!")

        # Delete root
        assert etcd3.delete(key, prefix=del_prefix)
        for n, child in enumerate(childs):
            if n > 0:
                assert etcd3.get(child)[0] == str(n), child
        assert (etcd3.get(key + "x")[0] is None) == del_prefix
        assert etcd3.get(key + "x/x")[0] == "keep!"

        # This should fail now
        assert not etcd3.delete(key, recursive=True, must_exist=True,
                                prefix=del_prefix)
        for n, child in enumerate(childs):
            if n > 0:
                assert etcd3.get(child)[0] == str(n), child
        assert (etcd3.get(key + "x")[0] is None) == del_prefix
        assert etcd3.get(key + "x/x")[0] == "keep!"

        # But this one should work, and remove remaining keys
        # (except those with the same prefix but different path
        #  unless we set the option before)
        assert etcd3.delete(key, recursive=True, must_exist=False,
                            prefix=del_prefix)
        for child in childs:
            assert etcd3.get(child)[0] is None, child
        assert (etcd3.get(key + "x")[0] is None) == del_prefix
        assert (etcd3.get(key + "x/x")[0] is None) == del_prefix

if __name__ == '__main__':
    pytest.main()
