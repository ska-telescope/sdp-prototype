"""
Workflow related tasks for SDPSubarray.

This is the first stage to isolate the database operations.
There should probably be another layer to fully separate the workflow logic
from the database operations. Then more code can be moved from SDPSubarray
into that layer.
"""

import logging
from typing import Dict, List, Tuple, Optional

import ska_sdp_config
from .feature_toggle import FeatureToggles

CONFIG_DB = 'config_db'
FEATURES = FeatureToggles((CONFIG_DB,))


def new_config_db():
    """Return a config db object (factory function)."""
    backend = 'etcd3' if FEATURES.is_active(CONFIG_DB) else 'memory'
    logging.info("Using config db backend %s", backend)
    config_db = ska_sdp_config.Config(backend=backend)
    return config_db


class SubarrayConfig:
    """Class to hold workflow and database state."""

    # pylint: disable=invalid-name
    def __init__(self):
        """Create the object."""
        self.db_client = new_config_db()
        self._sbi_id = None

    def _lock(self) -> None:
        """Synchronize placeholder."""

    def _unlock(self) -> None:
        """Synchronize placeholder."""

    @property
    def sbi_id(self) -> str:
        """
        Get the scheduling block instance ID.

        :return: the id
        """
        return self._sbi_id

    @sbi_id.setter
    def sbi_id(self, value: Optional[str]) -> None:
        """
        Set the scheduling block instance ID.

        :param value: the ID
        """
        self._lock()
        self._sbi_id = value
        self._unlock()

    def is_sbi_active(self) -> bool:
        """
        Is the scheduling block instance ID set.

        :return: true if it is
        """
        return self.sbi_id is not None

    def clear_sbi(self) -> None:
        """Clear the scheduling block instance ID."""
        self.sbi_id = None

    def get_processing_block_state(self) -> List:
        """
        Get the processing block state.

        :return: list of states
        """
        pb_state_list = []

        if self.is_sbi_active():
            self._lock()
            for txn in self.db_client.txn():
                sb = txn.get_scheduling_block(self.sbi_id)
                pb_realtime = sb.get('pb_realtime')
                for pb_id in pb_realtime:
                    pb_state = txn.get_processing_block_state(pb_id)
                    if pb_state is None:
                        pb_state = {'id': pb_id}
                    else:
                        pb_state['id'] = pb_id
                    pb_state_list.append(pb_state)
            self._unlock()
        return pb_state_list

    def get_scheduling_block(self) -> Optional[Dict]:
        """
        Get the scheduling block.

        :return: scheduling block or None if not active
        """
        sb = None

        self._lock()
        if self.is_sbi_active():
            for txn in self.db_client.txn():
                sb = txn.get_scheduling_block(self.sbi_id)
        self._unlock()
        return sb

    def get_existing_ids(self) -> Tuple[List, List]:
        """
        Get the existing scheduling and processing block ids.

        :return: tuple of ids, scheduling then processing
        """
        existing_sb_ids = []
        existing_pb_ids = []
        self._lock()
        for txn in self.db_client.txn():
            existing_sb_ids = txn.list_scheduling_blocks()
            existing_pb_ids = txn.list_processing_blocks()
        self._unlock()
        return existing_sb_ids, existing_pb_ids

    def create_sb_and_pbs(self, sb: Dict, pbs: List) -> None:
        """Create SB and PBs in the config DB.

        This is done in a single transaction. The processing blocks are
        created with an empty state.

        :param sb: scheduling block
        :param pbs: list of processing blocks
        """
        self._lock()
        for txn in self.db_client.txn():
            logging.info("before create %s", txn.list_scheduling_blocks())
            sbi_id = sb.get('id')
            txn.create_scheduling_block(sbi_id, sb)
            for pb in pbs:
                txn.create_processing_block(pb)
            logging.info("after create %s", txn.list_scheduling_blocks())
        self._unlock()

    def update_sb(self, new_values: Dict) -> None:
        """Update SB in the config DB.

        :param new_values: dict containing key/value pairs to update
        """
        self._lock()
        for txn in self.db_client.txn():
            sb = txn.get_scheduling_block(self.sbi_id)
            sb.update(new_values)
            txn.update_scheduling_block(self.sbi_id, sb)
        self._unlock()

    def get_receive_addresses(self) -> Dict:
        """Get the receive addresses from the receive PB state.

        The channel link map for each scan type is contained in the list of
        scan types in the SBI. The receive workflow uses them to generate the
        receive addresses for each scan type and writes them to the processing
        block state. This function retrieves them from the processing block
        state.

        :returns: dict mapping scan type to receive addresses
        """
        logging.info('Waiting for receive addresses')

        # Wait for pb_receive_addresses in SBI
        self._lock()
        for txn in self.db_client.txn():
            sb = txn.get_scheduling_block(self.sbi_id)
            pb_id = sb.get('pb_receive_addresses')
            if pb_id is None:
                txn.loop(wait=True)

        # Wait for receive_addresses in PB state
        for txn in self.db_client.txn():
            pb_state = txn.get_processing_block_state(pb_id)
            if pb_state is None:
                txn.loop(wait=True)
                continue
            receive_addresses = pb_state.get('receive_addresses')
            if receive_addresses is None:
                txn.loop(wait=True)

        self._unlock()
        return receive_addresses

    def set_scan_type(self, new_scan_types: List, scan_type: str) -> bool:
        """Set the scan type.

        If new scan types are supplied, they are appended to the current
        list.

        :param new_scan_types: new scan types
        :param scan_type: scan type
        :returns: True if the configuration is good, False if there is an
            error
        """
        self._lock()

        # Get the existing scan types from SB
        for txn in self.db_client.txn():
            sb = txn.get_scheduling_block(self.sbi_id)
        scan_types = sb.get('scan_types')

        # Extend the list of scan types with new ones, if supplied
        if new_scan_types is not None:
            scan_types.extend(new_scan_types)

        # Check scan type is in the list of scan types
        scan_type_ids = [st.get('id') for st in scan_types]
        if scan_type not in scan_type_ids:
            logging.error('Unknown scan_type: %s', scan_type)
            return False

        # Set current scan type, and update list of scan types if it has
        # been extended
        if new_scan_types is not None:
            self.update_sb({'current_scan_type': scan_type,
                            'scan_types': scan_types})
        else:
            self.update_sb({'current_scan_type': scan_type})

        self._unlock()
        return True
