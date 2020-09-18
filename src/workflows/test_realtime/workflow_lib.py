"""High-level API for SKA SDP workflow."""
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

# TODO TO BE REMOVED

import sys
import time
import logging
import ska_sdp_config

LOG = logging.getLogger('worklow')
LOG.setLevel(logging.DEBUG)


class Workflow:

    def __init__(self):
        """Initialisation."""
        print("Init")
        # Get connection to config DB
        LOG.info('Opening connection to config DB')
        self._config = ska_sdp_config.Config()

    def claim_processing_block(self, pb_id):
        # Claim processing block
        for txn in self._config.txn():
            txn.take_processing_block(pb_id, self._config.client_lease)
            pb = txn.get_processing_block(pb_id)
        LOG.info('Claimed processing block')

        LOG.info(pb)
        sbi_id = pb.id
        LOG.info("SBI ID %s", sbi_id)
        return sbi_id

    def get_definition(self, pb_id):
        pass

    def get_parameters(self, pb_id):
        for txn in self._config.txn():
            pb = txn.get_processing_block(pb_id)
            # TODO (NJT): Not just duration parameter - But this just for the time being
            # Get parameter and parse it
            duration = pb.parameters.get('duration')
            if duration is None:
                duration = 60.0
            LOG.info('duration: %f s', duration)
        return duration

    def resource_request(self, pb_id):
        # Set state to indicate workflow is waiting for resources
        LOG.info('Setting status to WAITING')
        for txn in self._config.txn():
            state = txn.get_processing_block_state(pb_id)
            state['status'] = 'WAITING'
            txn.update_processing_block_state(pb_id, state)

        # Wait for resources_available to be true
        LOG.info('Waiting for resources to be available')
        for txn in self._config.txn():
            state = txn.get_processing_block_state(pb_id)
            ra = state.get('resources_available')
            if ra is not None and ra:
                LOG.info('Resources are available')
                break
            txn.loop(wait=True)

    def process_started(self, pb_id):
        # Set state to indicate processing has started
        LOG.info('Setting status to RUNNING')
        for txn in self._config.txn():
            state = txn.get_processing_block_state(pb_id)
            state['status'] = 'RUNNING'
            txn.update_processing_block_state(pb_id, state)

    def release(self, status):
        pass

    def monitor_sbi(self, sbi_id, pb_id):
        # Wait until SBI is marked as FINISHED or CANCELLED
        LOG.info('Waiting for SBI to end')
        LOG.info(sbi_id)
        LOG.info(pb_id)
        for txn in self._config.txn():
            sbi = txn.get_scheduling_block(sbi_id)
            status = sbi.get('status')
            if status in ['FINISHED', 'CANCELLED']:
                LOG.info('SBI is %s', status)
                break
            txn.loop(wait=True)

        # Set state to indicate processing has ended
        LOG.info('Setting status to %s', status)
        for txn in self._config.txn():
            state = txn.get_processing_block_state(pb_id)
            state['status'] = status
            txn.update_processing_block_state(pb_id, state)

    def monitor_sbi_batch(self, status, duration, pb_id):
        # Do some 'processing' for the required duration
        LOG.info('Starting processing for %f s', duration)
        time.sleep(duration)
        LOG.info('Finished processing')

        # Set state to indicate processing has ended
        LOG.info('Setting status to %s', status)
        for txn in self._config.txn():
            state = txn.get_processing_block_state(pb_id)
            state['status'] = status
            txn.update_processing_block_state(pb_id, state)
    #
    # def exit(self):
    #     # Close connection to config DB
    #     LOG.info('Closing connection to config DB')
    #     self._config.close()
    #     LOG.info('Asked to terminate')
    #     sys.exit(0)




