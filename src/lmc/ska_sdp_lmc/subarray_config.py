"""Config DB related tasks for SDP subarray."""

import logging
from typing import Dict, List, Tuple, Optional

import ska_sdp_config
from .feature_toggle import FeatureToggle

FEATURE_CONFIG_DB = FeatureToggle('config_db', True)

LOG = logging.getLogger('ska_sdp_lmc')


def new_config_db():
    """Return a config DB object (factory function)."""
    backend = 'etcd3' if FEATURE_CONFIG_DB.is_active() else 'memory'
    logging.info("Using config DB %s backend", backend)
    config_db = ska_sdp_config.Config(backend=backend)
    return config_db


class SubarrayConfig:
    """Class to interact with subarray configuration in DB."""

    # pylint: disable=invalid-name

    def __init__(self, subarray_id):
        """Create the object."""
        self.db_client = new_config_db()
        self.subarray_id = subarray_id

    def _lock(self) -> None:
        """Synchronize placeholder."""

    def _unlock(self) -> None:
        """Synchronize placeholder."""

    def init_subarray(self, subarray: Dict) -> None:
        """Initialise subarray in config DB.

        If the subarray entry exists already it is not overwritten: it is
        assumed that this is the existing state that should be resumed. If the
        subarray entry does not exist, it is initialised with device state OFF
        and obsState EMPTY.

        """
        for txn in self.db_client.txn():
            subarray_ids = txn.list_subarrays()
            if self.subarray_id not in subarray_ids:
                txn.create_subarray(self.subarray_id, subarray)

    def create_sbi_pbs(self, subarray: Dict, sbi: Dict, pbs: List) -> None:
        """Create new SBI and PBs, and update subarray in config DB.

        :param subarray: update to subarray
        :param sbi: new SBI to create
        :param pbs: list of new PBs to create

        """
        for txn in self.db_client.txn():
            subarray_tmp = txn.get_subarray(self.subarray_id)
            subarray_tmp.update(subarray)
            txn.update_subarray(self.subarray_id, subarray_tmp)
            sbi_id = sbi.get('id')
            txn.create_scheduling_block(sbi_id, sbi)
            for pb in pbs:
                txn.create_processing_block(pb)

    def update_subarray_sbi(self, subarray: Optional[Dict] = None,
                            sbi: Optional[Dict] = None) -> None:
        """Update subarray and SBI in config DB.

        :param subarray: update to subarray (optional)
        :param sbi: update to SBI (optional)

        """
        for txn in self.db_client.txn():
            subarray_state = txn.get_subarray(self.subarray_id)
            sbi_id = subarray_state.get('sbi_id')
            if subarray:
                subarray_state.update(subarray)
                txn.update_subarray(self.subarray_id, subarray_state)
            if sbi and sbi_id:
                sbi_state = txn.get_scheduling_block(sbi_id)
                sbi_state.update(sbi)
                txn.update_scheduling_block(sbi_id, sbi_state)

    def list_sbis_pbs(self) -> Tuple[List, List]:
        """Get existing SBI and PB IDs from config DB.

        :returns: list of SBI IDs and list of PB IDs

        """
        for txn in self.db_client.txn():
            sbi_ids = txn.list_scheduling_blocks()
            pb_ids = txn.list_processing_blocks()

        return sbi_ids, pb_ids

    def get_sbi(self) -> Dict:
        """Get SBI from config DB.

        :returns: SBI

        """
        for txn in self.db_client.txn():
            subarray = txn.get_subarray(self.subarray_id)
            sbi_id = subarray.get('sbi_id')
            if sbi_id:
                sbi = txn.get_scheduling_block(sbi_id)
            else:
                sbi = {}

        return sbi
