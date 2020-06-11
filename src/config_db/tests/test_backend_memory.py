import pytest
from ska_sdp_config.backend import ConfigVanished, ConfigCollision
from ska_sdp_config.memory_backend import MemoryBackend, MemoryTransaction


@pytest.fixture
def txn() -> MemoryTransaction:
    return MemoryTransaction(MemoryBackend())


def test_stuff(txn: MemoryTransaction):
    txn.create('/x/y', 'v1')
    assert txn.get('/x/y') == 'v1'
    txn.update('/x/y', 'v3')
    assert txn.get('/x/y') == 'v3'
    txn.create('/x/y/z', 'v2')

    with pytest.raises(ConfigCollision):
        txn.create('/x/y', 'v')
    with pytest.raises(ConfigVanished):
        txn.update('/y/x', 'v')
    with pytest.raises(ConfigVanished):
        txn.delete('/y/x', 'v')

    assert len(txn.list_keys('/x')) == 1

    txn.commit()
    assert next(iter(txn)) == txn

    assert txn.backend.lease() is not None
    txn.backend.close()