
from processing_controller import processing_controller
import ska_sdp_config
from ska_sdp_config import entity
import workflows_test

import pytest
import datetime

CFG_PREFIX = '/__test_pb'

@pytest.fixture
def config():
    """
    Configuration database client
    """
    with ska_sdp_config.Config(backend='etcd3', global_prefix=CFG_PREFIX) as cfg:
        cfg._backend.delete(CFG_PREFIX, must_exist=False, recursive=True, prefix=True)
        yield cfg
        cfg._backend.delete(CFG_PREFIX, must_exist=False, recursive=True, prefix=True)

@pytest.fixture
def test_pc(config):
    """
    Provides a processing controller with workflow definitions taken from a file
    """
    pc = processing_controller.ProcessingController(
        workflows_test.SCHEMA, workflows_test.WORK_URL, 1)
    pc._workflows.update_file(workflows_test.WORKFLOW)
    return pc

@pytest.fixture
def test_workflows():
    """
    Find test workflows to use. Returns a realtime and batch
    processing block respectively.
    """

    # Read test workflows
    wfs = processing_controller.Workflows(workflows_test.SCHEMA)
    wfs.update_file(workflows_test.WORKFLOW)

    # Find test workflows and their current version
    rt_workflow = None
    batch_workflow = None
    for wf_id, ver in wfs._realtime:
        if wf_id == "test_realtime":
            rt_workflow = { 'type': 'realtime', 'id': wf_id, 'version': ver }
    for wf_id, ver in wfs._batch:
        if wf_id == "test_batch":
            batch_workflow = { 'type': 'batch', 'id': wf_id, 'version': ver }
    assert rt_workflow is not None
    assert batch_workflow is not None

    return (rt_workflow, batch_workflow)

PB_PREFIX = "pb-sdptest-" + datetime.date.today().strftime("%Y%m%d") + "-"

def _create_pb(config, pb_id, workflow):
    """ Helper to create a processing block in configuration database. """
    for txn in config.txn():
        txn.create_processing_block(entity.ProcessingBlock(pb_id, "sbi"+pb_id[2:], workflow))

def _get_pb_state(config, pb_id):
    for txn in config.txn():
        return txn.get_processing_block_state(pb_id)

def _delete_pb(config, pb_id, workflow):
    """ Helper to create a processing block in configuration database. """
    for txn in config.txn():
        txn.delete_processing_block(entity.ProcessingBlock(pb_id, "sbi"+pb_id[2:], workflow))

def test_invalid_pbs(config, test_pc, test_workflows, caplog):

    # Attempt to create invalid processing block
    workflow = test_workflows[0]
    workflow1 = dict(workflow); workflow1['type'] = '__invalid'
    workflow2 = dict(workflow); workflow2['id'] = '__invalid'
    workflow3 = dict(workflow); workflow3['version'] = '__invalid'
    for pb_id, workflow, error_msg in [
            (PB_PREFIX + "invalid-pb", workflow, 'Invalid processing block ID'),
            (PB_PREFIX + "InvalidPb", workflow, 'Invalid processing block ID'),
            (PB_PREFIX + "invalidpb1", workflow1, 'Unknown workflow type'),
            (PB_PREFIX + "invalidpb2", workflow2, 'Could not find image'),
            (PB_PREFIX + "invalidpb3", workflow3, 'Could not find image')]:

        # Create
        _create_pb(config, pb_id, workflow)
        test_pc.run(config, False)

        # Check that there's an error
        assert _get_pb_state(config, pb_id)['status'] == 'FAILED', pb_id
        message_found = False
        for record in caplog.records:
            if record.levelname == 'ERROR' and pb_id in record.message:
                if error_msg in record.message:
                    message_found = True
        assert message_found

def test_pb(config, test_pc, test_workflows):

    # Create processing block
    pb_id = PB_PREFIX + "testpb"
    _create_pb(config, pb_id, test_workflows[0])
    test_pc.run(config, False)

    for txn in config.txn():

        # Check that processing block is starting
        pb_state = txn.get_processing_block_state(pb_id)
        assert pb_state['status'] == 'STARTING'

        # Check that a deployment was created
        deploy = txn.get_deployment(f"proc-{pb_id}-workflow")
        assert deploy.args['values']['pb_id'] == pb_id

def test_many_pbs(config, test_pc, test_workflows):

    # Create processing blocks
    pb_id = PB_PREFIX + "testpbs"
    for txn in config.txn():
        for i in range(20):
            txn.create_processing_block(entity.ProcessingBlock(
                pb_id+str(i), "sbi"+pb_id[2:], test_workflows[0]))
