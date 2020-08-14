# -*- coding: utf-8 -*-
"""Tango SDPSubarray device module."""
# pylint: disable=invalid-name
# pylint: disable=too-many-lines
# pylint: disable=wrong-import-position
# pylint: disable=too-many-public-methods

import os
import sys
import signal
import logging
import json
import threading

import jsonschema

from tango import AttrWriteType, DevState, LogLevel
from tango.server import attribute, command, run

from ska_sdp_logging import tango_logging
try:
    import ska_sdp_config
except ImportError:
    ska_sdp_config = None


from .attributes import AdminMode, HealthState, ObsState
from .base import SDPDevice
from .util import terminate

LOG = logging.getLogger()


class SDPSubarray(SDPDevice):
    """SDP Subarray device class.

    .. note::
        This should eventually inherit from SKASubarray but these need
        some work before doing so would add any value to this device.

    """

    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=no-self-use

    # Features: this is dict mapping feature name (str) to default toggle value
    # (bool).

    _features = {
        'config_db': True
    }

    # ----------
    # Attributes
    # ----------

    obsState = attribute(
        label='Obs State',
        dtype=ObsState,
        access=AttrWriteType.READ,
        doc='The device obs state.'
    )

    adminMode = attribute(
        label='Admin mode',
        dtype=AdminMode,
        access=AttrWriteType.READ_WRITE,
        doc='The device admin mode.'
    )

    healthState = attribute(
        label='Health state',
        dtype=HealthState,
        access=AttrWriteType.READ,
        doc='The health state reported for this device.'
    )

    receiveAddresses = attribute(
        label='Receive Addresses',
        dtype=str,
        access=AttrWriteType.READ,
        doc='Host addresses for the visibility receive workflow as a '
            'JSON string.'
    )

    scanType = attribute(
        label='Scan Type',
        dtype=str,
        access=AttrWriteType.READ,
        doc='Scan type.'
    )

    scanID = attribute(
        label='Scan ID',
        dtype=str,
        access=AttrWriteType.READ,
        doc='Scan ID.'
    )

    processingBlockState = attribute(
        label='State of real-time processing blocks',
        dtype=str,
        access=AttrWriteType.READ,
        doc='Processing block states for real-time workflows as a '
            'JSON string.'
    )

    schedulingBlockInstance = attribute(
        label='Scheduling block instance',
        dtype=str,
        access=AttrWriteType.READ,
        doc='Scheduling block instance as a JSON string.'
    )

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        """Initialise the device."""
        super().init_device()

        self.set_state(DevState.INIT)
        LOG.info('Initialising SDP Subarray: %s', self.get_name())

        # These attributes are updated with push_change_event
        self.set_change_event('obsState', True)
        self.set_change_event('adminMode', True)
        self.set_change_event('healthState', True)
        self.set_change_event('receiveAddresses', True)
        self.set_change_event('scanType', True)
        self.set_change_event('scanID', True)

        # Initialise attributes
        self._set_obs_state(ObsState.EMPTY)
        self._set_admin_mode(AdminMode.ONLINE)
        self._set_health_state(HealthState.OK)
        self._set_receive_addresses(None)
        self._set_scan_type(None)
        self._set_scan_id(None)

        # Initialise instance variables
        self._sbi_id = None
        # TODO NEED TO THINK ABOUT THIS
        self._pb_ids = None

        if ska_sdp_config is not None \
                and self.is_feature_active('config_db'):
            self._config_db_client = ska_sdp_config.Config()
            LOG.debug('SDP Config DB enabled')
        else:
            self._config_db_client = None
            LOG.warning('SDP Config DB disabled %s',
                        '(ska_sdp_config package not found)'
                        if ska_sdp_config is None
                        else 'by feature toggle')

        LOG.info("Adding Subarray ID to config")
        self._subarray_id = self._get_subarray_id()
        if self._config_db_client is not None:
            for txn in self._config_db_client.txn():
                subarray_ids = txn.list_subarrays()
                if self._subarray_id not in subarray_ids:
                    txn.create_subarray(self._subarray_id, {'state': 'OFF',
                                                            'sbi_id': None,
                                                            'subarray_id': self._subarray_id,
                                                            'commanded_obs_state': None,})

        # The subarray device is initialised in the OFF state.
        LOG.debug('Setting device state to OFF')
        self.set_state(DevState.OFF)

        # The subarray device is initialised in the OFF state.
        self.set_state(DevState.OFF)
        LOG.info('SDP Subarray initialised: %s', self.get_name())

    def always_executed_hook(self):
        """Run for on each call."""

    def delete_device(self):
        """Device destructor."""
        LOG.info('Deleting subarray device: %s', self.get_name())

    # ------------------
    # Attributes methods
    # ------------------

    def read_obsState(self):
        """Get the obsState attribute.

        :returns: The current obsState attribute value.

        """
        return self._obs_state

    def read_adminMode(self):
        """Get the adminMode attribute.

        :returns: The current adminMode attribute value.

        """
        return self._admin_mode

    def read_healthState(self):
        """Get the healthState attribute.

        :returns: The current healthState attribute value.

        """
        return self._health_state

    def read_receiveAddresses(self):
        """Get the receive addresses.

        More details are provided on SKA confluence at the address:
        http://bit.ly/2Gad55Q

        :returns: JSON describing receive addresses

        """
        return json.dumps(self._receive_addresses)

    def read_scanType(self):
        """Get the scan type.

        More details are provided on SKA confluence at the address:
        http://bit.ly/2Gad55Q

        :returns: JSON describing receive addresses

        """
        return json.dumps(self._scan_type)

    def read_scanID(self):
        """Get the scan ID.

        More details are provided on SKA confluence at the address:
        http://bit.ly/2Gad55Q

        :returns: JSON describing receive addresses

        """
        return json.dumps(self._scan_id)

    def read_processingBlockState(self):
        """Get the states of the real-time processing blocks.

        :returns: JSON describing real-time processing block states

        """
        pb_state_list = []

        if self._config_db_client is not None and self._sbi_id is not None:
            for txn in self._config_db_client.txn():
                sb = txn.get_scheduling_block(self._sbi_id)
                pb_realtime = sb.get('pb_realtime')
                for pb_id in pb_realtime:
                    pb_state = txn.get_processing_block_state(pb_id)
                    if pb_state is None:
                        pb_state = {'id': pb_id}
                    else:
                        pb_state['id'] = pb_id
                    pb_state_list.append(pb_state)

        return json.dumps(pb_state_list)

    def read_schedulingBlockInstance(self):
        """Get the scheduling block instance.

        :returns: JSON describing scheduling block instance

        """
        sb = None

        if self._config_db_client is not None and self._sbi_id is not None:
            for txn in self._config_db_client.txn():
                sb = txn.get_scheduling_block(self._sbi_id)

        return json.dumps(sb)

    def write_adminMode(self, admin_mode):
        """Set the adminMode attribute.

        :param admin_mode: An admin mode enum value.

        """
        self._set_admin_mode(admin_mode)

    # --------
    # Commands
    # --------

    def is_On_allowed(self):
        """Check if the On command is allowed."""
        return self._command_allowed(
            'On',
            state_allowed=[DevState.OFF],
            obs_state_allowed=[ObsState.EMPTY]
        )

    @command
    def On(self):
        """Set the subarray device into its Operational state."""
        LOG.info('-------------------------------------------------------')
        LOG.info('On (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        LOG.debug('Setting Subarray %s state to ON', self._subarray_id)

        # Set the state to On in subarray
        self._update_subarray_state('state', 'ON')

        # Start the monitoring thread
        self._monitoring = threading.Thread(target=self._monitoring_thread)
        self._monitoring.start()

        LOG.info('-------------------------------------------------------')
        LOG.info('On Successful!')
        LOG.info('-------------------------------------------------------')

    def is_Off_allowed(self):
        """Check if the Off command is allowed."""
        return self._command_allowed(
            'Off',
            state_allowed=[DevState.ON]
        )

    @command
    def Off(self):
        """Set the subarray device to inactive state."""
        LOG.info('-------------------------------------------------------')
        LOG.info('Off (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        LOG.debug('Setting Subarray %s state to OFF', self._subarray_id)
        self._update_subarray_state('commanded_obs_state', 'EMPTY')

        if self._obs_state != ObsState.EMPTY:
            LOG.info('obsState is not EMPTY')

            if self._sbi_id is not None:
                LOG.info('Cancelling the scheduling block instance')

                # Clear scan type, scan ID and set status to CANCELLED
                self._update_sb({'current_scan_type': None, 'scan_id': None,
                                 'status': 'CANCELLED'})

            # Clear the scheduling block instance ID
            self._sbi_id = None
            self._update_subarray_state('sbi_id', None)

        # Set the state to OFF in subarray
        self._update_subarray_state('state', 'OFF')

        LOG.info('-------------------------------------------------------')
        LOG.info('Off Successful!')
        LOG.info('-------------------------------------------------------')

    def is_AssignResources_allowed(self):
        """Check if the AssignResources command is allowed."""
        return self._command_allowed(
            'AssignResources',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.EMPTY],
            admin_mode_allowed=[AdminMode.ONLINE, AdminMode.MAINTENANCE,
                                AdminMode.RESERVED]
        )

    @command(dtype_in=str, doc_in='Resource configuration JSON string')
    def AssignResources(self, config_str):
        """Assign resources to the subarray.

        This creates the processing blocks associated with the
        scheduling block instance.

        :param config_str: Resource configuration JSON string

        """
        LOG.info('-------------------------------------------------------')
        LOG.info('AssignResources (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Set commanded obsState to IDLE
        self._update_subarray_state('commanded_obs_state', 'IDLE')

        # Log the JSON configuration string
        LOG.info('Configuration string:')
        for line in config_str.splitlines():
            LOG.info(line)

        # Validate the JSON configuration string
        config = self._validate_json_config(
            config_str, 'assign_resources.json')

        if config is None:
            # Validation has failed, so set obsState to FAULT and raise
            # an error
            self._update_subarray_state('commanded_obs_state', 'FAULT')
            self._raise_command_error(
                'Configuration validation failed',
                origin='SDPSubarray.AssignResources()'
            )

        # Check IDs against existing IDs in the config DB
        ok = self._config_check_ids(config)

        if not ok:
            # Duplicate scheduling block, so set obsState to FAULT and
            # raise an error
            self._update_subarray_state('commanded_obs_state', 'FAULT')
            self._raise_command_error(
                'Duplicate scheduling block instance ID or processing block'
                ' ID in configuration',
                origin='SDPSubarray.AssignResources()'
            )

        # Create SBI and PBs in config DB
        ok = self._config_create_sb_and_pbs(config)

        if not ok:
            # Creation of SBI and PBs failed, so set obsState to FAULT and
            # raise an error
            self._update_subarray_state('commanded_obs_state', 'FAULT')
            self._raise_command_error(
                'Creation of scheduling block and processing blocks failed',
                origin='SDPSubarray.AssignResources()'
            )

        # Set the scheduling block instance ID
        self._sbi_id = config.get('id')
        self._update_subarray_state('sbi_id', self._sbi_id)

        LOG.info('-------------------------------------------------------')
        LOG.info('AssignResources Successful!')
        LOG.info('-------------------------------------------------------')

    def is_ReleaseResources_allowed(self):
        """Check if the ReleaseResources command is allowed."""
        return self._command_allowed(
            'ReleaseResources',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.IDLE],
            admin_mode_allowed=[AdminMode.OFFLINE, AdminMode.NOT_FITTED],
            admin_mode_invert=True
        )

    @command
    def ReleaseResources(self):
        """Release resources assigned to the subarray.

        This ends the real-time processing blocks associated with the
        scheduling block instance.

        """
        LOG.info('-------------------------------------------------------')
        LOG.info('ReleaseResources (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Set commanded obsState to EMPTY
        self._update_subarray_state('commanded_obs_state', 'EMPTY')

        # Set status to FINISHED
        self._update_sb({'status': 'FINISHED'})

        # Clear the scheduling block instance ID
        self._sbi_id = None
        self._update_subarray_state('sbi_id', None)
        # TODO (NJT) NEED TO FIX THIS
        self._update_subarray_state('subarray_id', None)

        LOG.info('-------------------------------------------------------')
        LOG.info('ReleaseResources Successful!')
        LOG.info('-------------------------------------------------------')

    def is_Configure_allowed(self):
        """Check if the Configure command is allowed."""
        return self._command_allowed(
            'Configure',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.IDLE, ObsState.READY]
        )

    @command(dtype_in=str, doc_in='Scan type configuration JSON string')
    def Configure(self, config_str):
        """Configure SDP scan type.

        :param config_str: Scan type configuration JSON string

        """
        LOG.info('-------------------------------------------------------')
        LOG.info('Configure (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Set commanded obsState to READY
        self._update_subarray_state('commanded_obs_state', 'READY')

        # Log the JSON configuration string
        LOG.info('Configuration string:')
        for line in config_str.splitlines():
            LOG.info(line)

        # Validate the JSON configuration string
        config = self._validate_json_config(config_str, 'configure.json')

        if config is None:
            # Validation has failed, so set obsState to FAULT and raise
            # an error
            self._update_subarray_state('commanded_obs_state', 'FAULT')
            self._raise_command_error(
                'Configuration validation failed',
                origin='SDPSubarray.Configure()'
            )

        # Append new scan types if supplied, and set the scan type
        ok = self._config_set_scan_type(config)

        if not ok:
            # Scan type configuration has failed, so set obsState to FAULT
            # and raise an error
            self._update_subarray_state('commanded_obs_state', 'FAULT')
            self._raise_command_error(
                'Scan type configuration failed',
                origin='SDPSubarray.Configure()'
            )

        # Set status to READY
        self._update_sb({'status': 'READY'})

        LOG.info('-------------------------------------------------------')
        LOG.info('Configure successful!')
        LOG.info('-------------------------------------------------------')

    def is_Scan_allowed(self):
        """Check if the Scan command is allowed."""
        return self._command_allowed(
            'Scan',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.READY]
        )

    @command(dtype_in=str, doc_in='Scan ID configuration JSON string')
    def Scan(self, config_str):
        """Start scan.

        :param config_str: Scan ID configuration JSON string

        """
        LOG.info('-------------------------------------------------------')
        LOG.info('Scan (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Set commanded obsState to SCANNING
        self._update_subarray_state('commanded_obs_state', 'SCANNING')

        # Log the JSON configuration string
        LOG.info('Configuration string:')
        for line in config_str.splitlines():
            LOG.info(line)

        # Validate the JSON configuration string
        config = self._validate_json_config(config_str, 'scan.json')

        if config is None:
            # Validation has failed, so set obsState to FAULT and raise
            # an error
            self._update_subarray_state('commanded_obs_state', 'FAULT')
            self._raise_command_error(
                'Configuration validation failed',
                origin='SDPSubarray.Scan()'
            )

        # Get the scan ID
        scan_id = config.get('id')

        # Set scan ID and set status to SCANNING
        self._update_sb({'scan_id': scan_id, 'status': 'SCANNING'})

        LOG.info('-------------------------------------------------------')
        LOG.info('Scan Successful')
        LOG.info('-------------------------------------------------------')

    def is_EndScan_allowed(self):
        """Check if the EndScan command is allowed."""
        return self._command_allowed(
            'EndScan',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.SCANNING]
        )

    @command
    def EndScan(self):
        """End scan."""
        LOG.info('-------------------------------------------------------')
        LOG.info('EndScan (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Set commanded obsState to READY
        self._update_subarray_state('commanded_obs_state', 'READY')

        # Clear scan ID and set status to READY
        self._update_sb({'scan_id': None, 'status': 'READY'})

        LOG.info('-------------------------------------------------------')
        LOG.info('EndScan Successful')
        LOG.info('-------------------------------------------------------')

    def is_End_allowed(self):
        """Check if the Reset command is allowed."""
        return self._command_allowed(
            'End',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.READY]
        )

    @command
    def End(self):
        """End."""
        LOG.info('-------------------------------------------------------')
        LOG.info('Reset (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Set commanded obsState to IDLE
        self._update_subarray_state('commanded_obs_state', 'IDLE')

        # Clear scan type and scan ID, and set status to IDLE
        self._update_sb({'current_scan_type': None, 'scan_id': None,
                         'status': 'IDLE'})

        LOG.info('-------------------------------------------------------')
        LOG.info('Reset Successful')
        LOG.info('-------------------------------------------------------')

    def is_Abort_allowed(self):
        """Check if the Abort command is allowed."""
        return self._command_allowed(
            'Abort',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.IDLE, ObsState.CONFIGURING,
                               ObsState.READY, ObsState.SCANNING,
                               ObsState.RESETTING]
        )

    @command
    def Abort(self):
        """Abort the subarray device."""
        LOG.info('-------------------------------------------------------')
        LOG.info('Abort (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Set commanded obsState to ABORTED
        self._update_subarray_state('commanded_obs_state', 'ABORTED')

        # Set status to ABORTED
        self._update_sb({'status': 'ABORTED'})

        LOG.info('-------------------------------------------------------')
        LOG.info('Abort Successful')
        LOG.info('-------------------------------------------------------')

    def is_ObsReset_allowed(self):
        """Check if the ObsReset command is allowed."""
        return self._command_allowed(
            'ObsReset',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.ABORTED, ObsState.FAULT]
        )

    @command
    def ObsReset(self):
        """Set obsState to the last known stable state.

        In the case of the subarray device this is Idle.
        """
        LOG.info('-------------------------------------------------------')
        LOG.info('ObsReset (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Set obsState to RESETTING
        self._update_subarray_state('commanded_obs_state', 'IDLE')

        if self._sbi_id is None:
            message = 'Scheduling block instance is not configured, ' + \
                'ObsReset is not permitted'
            LOG.error(message)
            self._update_subarray_state('commanded_obs_state', 'FAULT')
            self._raise_command_error(
                message,
                origin='SDPSubarray.ObsReset()'
            )

        # Clear scan type and scan ID, and set status to IDLE
        self._update_sb({'current_scan_type': None, 'scan_id': None,
                         'status': 'IDLE'})

        LOG.info('-------------------------------------------------------')
        LOG.info('ObsReset Successful')
        LOG.info('-------------------------------------------------------')

    def is_Restart_allowed(self):
        """Check if the Restart command is allowed."""
        return self._command_allowed(
            'Restart',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.ABORTED, ObsState.FAULT]
        )

    @command
    def Restart(self):
        """Restart the subarray device.

        This is like a "hard" rest
        """
        LOG.info('-------------------------------------------------------')
        LOG.info('Restart (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Set obsState to EMPTY
        self._update_subarray_state('commanded_obs_state', 'EMPTY')

        if self._sbi_id is not None:
            # Clear scan type and scan ID, and set status to CANCELLED
            self._update_sb({'current_scan_type': None, 'scan_id': None,
                             'status': 'CANCELLED'})

            # Clear the scheduling block instance ID
            self._sbi_id = None
            self._update_subarray_state('sbi_id', None)

        LOG.info('-------------------------------------------------------')
        LOG.info('Restart Successful')
        LOG.info('-------------------------------------------------------')

    # -------------------------------------
    # Public methods
    # -------------------------------------

    # -------------------------------------
    # Private methods
    # -------------------------------------

    def _get_subarray_id(self):
        """Get Subarray id.

        :returns: Subarray id.

        """
        subarray_id_path = self.get_name().split('/')
        subarray_id_split = subarray_id_path[2].split('_')
        subarray_id = subarray_id_split[1].zfill(2)
        return subarray_id

    def _update_subarray_state(self, current_state, current_value):
        """Update Subarray state device and ObsState states.

        :param current_state: Device state or ObsState
        :param current_value: State value to get updated
        """
        if self._config_db_client is None:
            return None

        for txn in self._config_db_client.txn():
            state = txn.get_subarray(self._subarray_id)
            state[current_state] = current_value
            txn.update_subarray(self._subarray_id, state)

    def _get_transitional_state(self, sbi_id=None):
        """Get the correct transitional state."""
        if self._obs_state == ObsState.EMPTY or \
            self._obs_state == ObsState.IDLE and sbi_id is None:
                LOG.info("ObsState is set to RESOURCING")
                return ObsState.RESOURCING
        elif self._obs_state == ObsState.IDLE:
            if self._obs_state != ObsState.CONFIGURING:
                LOG.info("ObsState is set to CONFIGURING")
                return ObsState.CONFIGURING
        elif self._obs_state == ObsState.ABORTED or \
                self._obs_state == ObsState.FAULT:
            if sbi_id is None:
                LOG.info("ObsState is set to RESTARTING")
                return ObsState.RESTARTING
            else:
                LOG.info("ObsState is set to RESETTING")
                return ObsState.RESETTING
        return None

    def _get_obs_state(self, txn, sbi_id=None, pb_state=None):
        """Get the correct obs state."""
        if sbi_id is not None:
            sb = txn.get_scheduling_block(sbi_id)

        if pb_state is not None:
            if pb_state.get('status') == 'RUNNING' and \
                sb.get('pb_receive_addresses') is not None:
                if sb.get('current_scan_type') is None and \
                    sb.get('scan_id') is None:
                    self._set_scan_type(sb.get('current_scan_type'))
                    self._set_scan_id(sb.get('scan_id'))
                    LOG.info("ObsState is set to IDLE")
                    return ObsState.IDLE
            elif pb_state.get('status') == 'FINISHED':
                # Clear the receive addresses
                # TODO (NJT) NEED TO UPDATE WORKFLOW TO GET RESTART TO WORK
                self._set_receive_addresses(None)
                LOG.info("ObsState is set to EMPTY")
                return ObsState.EMPTY
            elif pb_state.get('status') == 'RUNNING' and \
                    self._obs_state == ObsState.RESTARTING:
                # Clear the receive addresses
                self._set_receive_addresses(None)
                LOG.info("ObsState is set to EMPTY")
                return ObsState.EMPTY
        else:
            if sb.get('scan_id') is not None:
                LOG.info('ObsState is set to SCANNING')
                return ObsState.SCANNING
            elif sb.get('current_scan_type') is not None and \
                    sb.get('scan_id') is None:
                LOG.info("ObsState is set to READY")
                return ObsState.READY
            elif self._pb_ids is None:
                LOG.debug("TEMPORARY - UNTIL WORKFLOW IS UPDATED")
                LOG.info("ObsState is set to EMPTY")
                return ObsState.EMPTY

        return None

    def _monitoring_thread(self):
        """This is the monitoring thread."""
        LOG.info("Monitoring Thread Started")
        for txn in self._config_db_client.txn():
            state = txn.get_subarray(self._subarray_id)
            if state.get('state') == 'ON':
                if self.get_state() != DevState.ON:
                    # Setting device state to ON state
                    LOG.info('Setting device state to ON')
                    self.set_state(DevState.ON)
                sbi_id = state.get('sbi_id')

                if state.get('commanded_obs_state') == 'IDLE':
                    # AssignResources ObsReset and End command
                    if sbi_id is not None:
                        sb = txn.get_scheduling_block(sbi_id)
                        self._pb_ids = sb.get('pb_realtime')
                        transitional_state = self._get_transitional_state(sbi_id)
                        if transitional_state is not None:
                            self._set_obs_state(transitional_state)
                        for pb_id in self._pb_ids:
                            pb_state = txn.get_processing_block_state(pb_id)
                            if pb_state is not None:
                                receive_addresses = self._get_receive_addresses(pb_state)
                                if receive_addresses is not None:
                                    self._set_receive_addresses(receive_addresses)
                                obs_state = self._get_obs_state(txn, sbi_id=sbi_id, pb_state=pb_state)
                                if obs_state is not None:
                                    self._set_obs_state(obs_state)

                elif state.get('commanded_obs_state') == 'EMPTY':
                    # ReleaseResources and Restart command
                    if sbi_id is None:
                        transitional_state = self._get_transitional_state(sbi_id)
                        if transitional_state is not None:
                            self._set_obs_state(transitional_state)
                        if self._pb_ids is not None:
                            for pb_id in self._pb_ids:
                                pb_state = txn.get_processing_block_state(pb_id)
                                if pb_state is not None:
                                    obs_state = self._get_obs_state(txn, pb_state=pb_state)
                                    if obs_state is not None:
                                        self._set_obs_state(obs_state)

                elif state.get('commanded_obs_state') == 'READY':
                    # Configure and EndScan command
                    transitional_state = self._get_transitional_state(sbi_id)
                    if transitional_state is not None:
                        self._set_obs_state(transitional_state)
                    sb = txn.get_scheduling_block(sbi_id)
                    if sb.get('current_scan_type') is not None and \
                            sb.get('scan_id') is None:
                        self._set_scan_type(sb.get('current_scan_type'))
                        self._set_scan_id(sb.get('scan_id'))
                        obs_state = self._get_obs_state(txn, sbi_id=sbi_id)
                        if obs_state is not None:
                            self._set_obs_state(obs_state)

                elif state.get('commanded_obs_state') == 'SCANNING':
                    # Scan command
                    sb = txn.get_scheduling_block(sbi_id)
                    if sb.get('scan_id') is not None:
                        self._set_scan_id(sb.get('scan_id'))
                        obs_state = self._get_obs_state(txn, sbi_id=sbi_id)
                        if obs_state is not None:
                            self._set_obs_state(obs_state)

                elif state.get('commanded_obs_state') == 'ABORTED':
                    # Abort command
                    LOG.debug('ObsState is set to ABORTING')
                    self._set_obs_state(ObsState.ABORTING)
                    sb = txn.get_scheduling_block(sbi_id)
                    # TODO (NJT) Need to work on this
                    if sb.get('status') == 'ABORTED':
                        LOG.info('ObsState is set to ABORTED')
                        self._set_obs_state(ObsState.ABORTED)

                elif state.get('commanded_obs_state') == 'FAULT':
                    # Set to Fault
                    LOG.info('ObsState is set to FAULT')
                    self._set_obs_state(ObsState.FAULT)

            elif state.get('state') == 'OFF':
                if state.get('commanded_obs_state') == 'EMPTY':
                    sbi_id = state.get('sbi_id')
                    # TODO (NJT) NEED TO CHECK IF THE WORKFLOW HAS EXISTED
                    if sbi_id is None:
                        # Clear the receive addresses
                        self._set_receive_addresses(None)
                        self._set_obs_state(ObsState.EMPTY)
                        LOG.info('Setting device state to OFF')
                        self.set_state(DevState.OFF)
                        return
            txn.loop(wait=True)

    def _set_obs_state(self, value, verbose=True):
        """Set the obsState and issue a change event."""
        if verbose:
            LOG.debug('Setting obsState to: %s', repr(ObsState(value)))
        self._obs_state = value
        self.push_change_event('obsState', self._obs_state)

    def _set_admin_mode(self, value, verbose=True):
        """Set the adminMode and issue a change event."""
        if verbose:
            LOG.debug('Setting adminMode to: %s', repr(AdminMode(value)))
        self._admin_mode = value
        self.push_change_event('adminMode', self._admin_mode)

    def _set_health_state(self, value, verbose=True):
        """Set the healthState and issue a change event."""
        if verbose:
            LOG.debug('Setting healthState to: %s', repr(HealthState(value)))
        self._health_state = value
        self.push_change_event('healthState', self._health_state)

    def _set_receive_addresses(self, value):
        """Set the receiveAddresses and issue a change event."""
        self._receive_addresses = value
        self.push_change_event('receiveAddresses',
                               json.dumps(self._receive_addresses))

    def _set_scan_type(self, value):
        """Set the scanType and issue a change event."""
        self._scan_type = value
        self.push_change_event('scanType',
                               json.dumps(self._scan_type))

    def _set_scan_id(self, value):
        """Set the scanID and issue a change event."""
        self._scan_id = value
        self.push_change_event('scanID',
                               json.dumps(self._scan_id))

    def _command_allowed(self, name,
                         state_allowed=None, obs_state_allowed=None,
                         admin_mode_allowed=None, admin_mode_invert=False):
        """Check if command is allowed in a particular state.

        Used by the is_COMMAND_allowed functions. If a list of allowed
        states/modes is None, that state/mode is not checked.

        :param name: name of the command
        :param state_allowed: list of allowed Tango device states
        :param obs_state_allowed: list of allowed observing states
        :param admin_mode_allowed: list of allowed administration modes
        :param admin_mode_invert: inverts condition on administration modes
        :returns: True if the command is allowed, otherwise raises exception

        """
        # pylint: disable=too-many-arguments

        allowed, message = self._check_command(name, state_allowed,
                                               obs_state_allowed,
                                               admin_mode_allowed,
                                               admin_mode_invert)

        if not allowed:
            # Raise command error
            origin = 'SDPSubarray.is_{}_allowed()'.format(name)
            self._raise_error(message, reason='API_CommandNotAllowed',
                              origin=origin)

        return allowed

    @staticmethod
    def _validate_json_config(config_str, schema_filename):
        """Validate a JSON configuration against a schema.

        :param config_str: JSON configuration string
        :param schema_filename: name of schema file in the 'schema'
             sub-directory
        :returns: validated configuration (as dict/list), or None if
            validation fails

        """
        LOG.debug('Validating JSON configuration against schema %s',
                  schema_filename)

        schema_path = os.path.join(os.path.dirname(__file__), 'schema',
                                   schema_filename)
        config = None

        if config_str == '':
            LOG.error('Empty configuration string')
        try:
            config = json.loads(config_str)
            with open(schema_path, 'r') as file:
                schema = json.load(file)
            jsonschema.validate(config, schema)
        except json.JSONDecodeError as error:
            LOG.error('Unable to decode configuration string as JSON: %s',
                      error.msg)
            config = None
        except jsonschema.ValidationError as error:
            LOG.error('Unable to validate JSON configuration: %s',
                      error.message)
            config = None

        if config is not None:
            LOG.debug('Successfully validated JSON configuration')

        return config

    def _config_check_ids(self, config):
        """Parse the configuration to check IDs against existing ones.

        :param config: configuration data
        :returns: True if the configuration is good, False if an ID
            duplicates one in the config DB

        """
        # Log the IDs found in the configuration
        sbi_id = config.get('id')
        pb_ids = [pb.get('id') for pb in config.get('processing_blocks')]
        LOG.info('Scheduling block instance %s', sbi_id)
        LOG.info('Processing blocks %s', pb_ids)

        # Get lists of existing scheduling blocks and processing blocks
        if self._config_db_client is not None:
            for txn in self._config_db_client.txn():
                existing_sb_ids = txn.list_scheduling_blocks()
                existing_pb_ids = txn.list_processing_blocks()
        else:
            existing_sb_ids = []
            existing_pb_ids = []

        # Check for duplicate IDs
        ok = True
        if sbi_id in existing_sb_ids:
            ok = False
            LOG.error('Scheduling block instance %s already exists', sbi_id)
        pb_dup = [pb_id for pb_id in pb_ids if pb_id in existing_pb_ids]
        if pb_dup != []:
            ok = False
            for pb_id in pb_dup:
                LOG.error('Processing block %s already exists', pb_id)

        return ok

    def _config_create_sb_and_pbs(self, config):
        """Parse the configuration and create the SB and PBs.

        :param config: configuration data
        :returns: True if the configuration is good, False if there is an
            error

        """
        # Initialise scheduling block

        sbi_id = config.get('id')

        sb = {
            'id': sbi_id,
            'subarray_id': self._subarray_id,
            'scan_types': config.get('scan_types'),
            'pb_realtime': [],
            'pb_batch': [],
            'pb_receive_addresses': None,
            'current_scan_type': None,
            'status': 'IDLE',
            'scan_id': None
        }

        # Loop over the processing block configurations

        pbs = []

        for pbc in config.get('processing_blocks'):
            pb_id = pbc.get('id')
            LOG.info('Parsing processing block %s', pb_id)

            # Get type of workflow and add the processing block ID to the
            # appropriate list.
            workflow = pbc.get('workflow')
            wf_type = workflow.get('type')
            if wf_type == 'realtime':
                sb['pb_realtime'].append(pb_id)
            elif wf_type == 'batch':
                sb['pb_batch'].append(pb_id)
            else:
                LOG.error('Unknown workflow type: %s', wf_type)

            parameters = pbc.get('parameters')

            if 'dependencies' in pbc:
                if wf_type == 'realtime':
                    LOG.error('dependencies attribute must not appear in '
                              'real-time processing block configuration')
                    dependencies = []
                if wf_type == 'batch':
                    dependencies = pbc.get('dependencies')
            else:
                dependencies = []

            # Add processing block to list
            pbs.append(
                ska_sdp_config.ProcessingBlock(
                    pb_id, sbi_id, workflow,
                    parameters=parameters,
                    dependencies=dependencies
                )
            )

        # Write the SB and PBs to the config DB
        self._create_sb_and_pbs(sb, pbs)

        return True

    def _config_set_scan_type(self, config):
        """Parse the configuration and set the scan type.

        If new scan types are supplied, they are appended to the current
        list.

        :param config: configuration data
        :returns: True if the configuration is good, False if there is an
            error

        """
        if self._config_db_client is not None:

            new_scan_types = config.get('new_scan_types')
            scan_type = config.get('scan_type')

            # Get the existing scan types from SB
            for txn in self._config_db_client.txn():
                sb = txn.get_scheduling_block(self._sbi_id)
            scan_types = sb.get('scan_types')

            # Extend the list of scan types with new ones, if supplied
            if new_scan_types is not None:
                scan_types.extend(new_scan_types)

            # Check scan type is in the list of scan types
            scan_type_ids = [st.get('id') for st in scan_types]
            if scan_type not in scan_type_ids:
                LOG.error('Unknown scan_type: %s', scan_type)
                return False

            # Set current scan type, and update list of scan types if it has
            # been extended
            if new_scan_types is not None:
                self._update_sb({'current_scan_type': scan_type,
                                 'scan_types': scan_types})
            else:
                self._update_sb({'current_scan_type': scan_type})

        return True

    def _create_sb_and_pbs(self, sb, pbs):
        """Create SB and PBs in the config DB.

        This is done in a single transaction. The processing blocks are
        created with an empty state.

        :param sb: scheduling block
        :param pbs: list of processing blocks

        """
        if self._config_db_client is not None:
            for txn in self._config_db_client.txn():
                sbi_id = sb.get('id')
                txn.create_scheduling_block(sbi_id, sb)
                for pb in pbs:
                    txn.create_processing_block(pb)

    def _update_sb(self, new_values):
        """Update SB in the config DB.

        :param new_values: dict containing key/value pairs to update

        """
        if self._config_db_client is not None:
            for txn in self._config_db_client.txn():
                sb = txn.get_scheduling_block(self._sbi_id)
                sb.update(new_values)
                txn.update_scheduling_block(self._sbi_id, sb)

    def _get_receive_addresses(self, pb_state):
        """Get the receive addresses from the receive PB state.

        The channel link map for each scan type is contained in the list of
        scan types in the SBI. The receive workflow uses them to generate the
        receive addresses for each scan type and writes them to the processing
        block state. This function retrieves them from the processing block
        state.

        :returns: dict mapping scan type to receive addresses

        """
        if pb_state is not None:
            receive_addresses = pb_state.get('receive_addresses')
            return receive_addresses

def main(args=None, **kwargs):
    """Run server."""
    # Initialise logging
    log_level = LogLevel.LOG_INFO
    if len(sys.argv) > 2 and '-v' in sys.argv[2]:
        log_level = LogLevel.LOG_DEBUG
    tango_logging.init(device_name='SDPSubarray', level=log_level)

    # Register SIGTERM handler.
    signal.signal(signal.SIGTERM, terminate)

    return run((SDPSubarray,), args=args, **kwargs)