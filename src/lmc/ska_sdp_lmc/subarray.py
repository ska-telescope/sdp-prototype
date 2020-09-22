# -*- coding: utf-8 -*-
"""Tango SDPSubarray device module."""
# pylint: disable=invalid-name
# pylint: disable=too-many-lines
# pylint: disable=wrong-import-position
# pylint: disable=too-many-public-methods
# pylint: disable=unused-import
# pylint: disable=E0202

import os
import sys
import signal
import logging
import threading
import json

import jsonschema

from tango import AttrWriteType, DevState, LogLevel, EnsureOmniThread
from tango.server import attribute, command, run

import ska_sdp_config

from . import tango_logging
from .attributes import AdminMode, HealthState, ObsState
from .base import SDPDevice
from .util import terminate, log_command, log_lines
from .subarray_config import SubarrayConfig, FEATURE_CONFIG_DB
from .feature_toggle import FeatureToggle

FEATURE_EVENT_LOOP = FeatureToggle('event_loop', True)

MSG_CONFIG_STR = 'Configuration string:'
MSG_VALIDATION_FAILED = 'Configuration validation failed'
MSG_DUPLICATE_ID = 'Duplicate SBI ID or PB ID in configuration'

tango_logging.configure(device_name='SDPSubarray')
LOG = logging.getLogger('ska_sdp_lmc')


class SDPSubarray(SDPDevice):
    """SDP Subarray device class."""

    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=no-self-use

    # ----------
    # Attributes
    # ----------

    obsState = attribute(
        label='Observing state',
        dtype=ObsState,
        access=AttrWriteType.READ,
        doc='The device observing state.'
    )

    adminMode = attribute(
        label='Admininistration mode',
        dtype=AdminMode,
        access=AttrWriteType.READ_WRITE,
        doc='The device administration mode.'
    )

    healthState = attribute(
        label='Health state',
        dtype=HealthState,
        access=AttrWriteType.READ,
        doc='Subarray device health state.'
    )

    receiveAddresses = attribute(
        label='Receive Addresses',
        dtype=str,
        access=AttrWriteType.READ,
        doc='Host addresses for the visibility receive workflow as a '
            'JSON string.'
    )

    scanType = attribute(
        label='Scan type',
        dtype=str,
        access=AttrWriteType.READ,
        doc='Scan type.'
    )

    scanID = attribute(
        label='Scan ID',
        dtype=int,
        access=AttrWriteType.READ,
        doc='Scan ID.'
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

        # Initialise private values of attributes
        self._obs_state = None
        self._admin_mode = None
        self._health_state = None
        self._receive_addresses = None
        self._scan_type = 'null'
        self._scan_id = 0

        # Set attributes not updated by event loop
        self._set_admin_mode(AdminMode.ONLINE)
        self._set_health_state(HealthState.OK)

        # Get subarray number from the device name
        subarray_id = self._get_subarray_id()

        # Get connection to the config DB
        self._config = SubarrayConfig(subarray_id)

        # Initialise the subarray entry
        subarray = {'state': 'OFF', 'sbi_id': None}
        self._subarray_add_command(subarray, None, ObsState.EMPTY)
        self._config.init_subarray(subarray)

        # Start event loop
        self._event_loop = self._start_event_loop()

        LOG.info('SDP Subarray initialised: %s', self.get_name())

    def always_executed_hook(self):
        """Run for on each call."""

    def delete_device(self):
        """Device destructor."""
        LOG.info('Deleting subarray device: %s', self.get_name())

    # -----------------
    # Attribute methods
    # -----------------

    def read_obsState(self):
        """Get the obsState.

        :returns: the current obsState.

        """
        return self._obs_state

    def read_adminMode(self):
        """Get the adminMode.

        :returns: the current adminMode.

        """
        return self._admin_mode

    def read_healthState(self):
        """Get the healthState.

        :returns: the current healthState.

        """
        return self._health_state

    def read_receiveAddresses(self):
        """Get the receive addresses.

        :returns: JSON receive address map

        """
        return json.dumps(self._receive_addresses)

    def read_scanType(self):
        """Get the scan type.

        :returns: scan type ('null' = no scan type)

        """
        return self._scan_type

    def read_scanID(self):
        """Get the scan ID.

        :returns: scan ID (0 = no scan ID)

        """
        return self._scan_id

    def write_adminMode(self, admin_mode):
        """Set the adminMode.

        :param admin_mode: an admin mode enum value.

        """
        self._set_admin_mode(admin_mode)

    # --------
    # Commands
    # --------

    def is_On_allowed(self):
        """Check if the On command is allowed."""
        commname = 'On'
        self._command_allowed_state(commname, [DevState.OFF])
        self._command_allowed_obs_state(commname, [ObsState.EMPTY])
        return True

    @log_command
    @command
    def On(self):
        """Turn the subarray on."""
        # Update subarray in the config DB
        subarray = {'state': 'ON'}
        self._subarray_add_command(subarray, 'On', ObsState.EMPTY)
        self._config.update_subarray_sbi(subarray=subarray)

    def is_Off_allowed(self):
        """Check if the Off command is allowed."""
        commname = 'Off'
        self._command_allowed_state(commname, [DevState.ON])
        return True

    @log_command
    @command
    def Off(self):
        """Turn the subarray off."""
        # Update subarray and SBI in the config DB
        if self._obs_state == ObsState.EMPTY:
            # This is a normal Off command.
            subarray = {'state': 'OFF'}
            sbi = None
        else:
            # ObsState is not EMPTY, so cancel the scheduling block instance.
            LOG.info('obsState is not EMPTY')
            LOG.info('Cancelling the scheduling block instance')
            subarray = {'state': 'OFF', 'sbi_id': None}
            sbi = {'subarray_id': None, 'status': 'CANCELLED',
                   'current_scan_type': None, 'scan_id': None}
        self._subarray_add_command(subarray, 'Off', ObsState.EMPTY)
        self._config.update_subarray_sbi(subarray=subarray, sbi=sbi)

    def is_AssignResources_allowed(self):
        """Check if the AssignResources command is allowed."""
        commname = 'AssignResources'
        self._command_allowed_state(commname, [DevState.ON])
        self._command_allowed_obs_state(commname, [ObsState.EMPTY])
        return True

    @log_command
    @command(dtype_in=str, doc_in='Resource configuration JSON string')
    def AssignResources(self, config_str):
        """Assign resources to the subarray.

        This creates the scheduling block instance and the processing blocks.

        :param config_str: Resource configuration JSON string

        """
        # Validate the configuration
        subarray, sbi, pbs = self._validate_assign_resources(config_str)

        # Update subarray and create SBI and PBs in the config DB
        self._subarray_add_command(subarray, 'AssignResources', ObsState.IDLE)
        self._config.create_sbi_pbs(subarray, sbi, pbs)

    def is_ReleaseResources_allowed(self):
        """Check if the ReleaseResources command is allowed."""
        commname = 'ReleaseResources'
        self._command_allowed_state(commname, [DevState.ON])
        self._command_allowed_obs_state(commname, [ObsState.IDLE])
        return True

    @log_command
    @command
    def ReleaseResources(self):
        """Release resources assigned to the subarray.

        This ends the scheduling block instance and its real-time processing
        blocks.

        """
        # Update subarray and SBI in the config DB
        subarray = {'sbi_id': None}
        self._subarray_add_command(subarray, 'ReleaseResources',
                                   ObsState.EMPTY)
        sbi = {'subarray_id': None, 'status': 'FINISHED'}
        self._config.update_subarray_sbi(subarray=subarray, sbi=sbi)

    def is_Configure_allowed(self):
        """Check if the Configure command is allowed."""
        commname = 'Configure'
        self._command_allowed_state(commname, [DevState.ON])
        self._command_allowed_obs_state(commname, [ObsState.IDLE,
                                                   ObsState.READY])
        return True

    @log_command
    @command(dtype_in=str, doc_in='Scan type configuration JSON string')
    def Configure(self, config_str):
        """Configure scan type.

        :param config_str: Scan type configuration JSON string

        """
        # Validate the configuration string
        sbi = self._validate_configure(config_str)

        # Update subarray and SBI in the config DB
        subarray = {}
        self._subarray_add_command(subarray, 'Configure', ObsState.READY)
        self._config.update_subarray_sbi(subarray=subarray, sbi=sbi)

    def is_Scan_allowed(self):
        """Check if the Scan command is allowed."""
        commname = 'Scan'
        self._command_allowed_state(commname, [DevState.ON])
        self._command_allowed_obs_state(commname, [ObsState.READY])
        return True

    @log_command
    @command(dtype_in=str, doc_in='Scan ID configuration JSON string')
    def Scan(self, config_str):
        """Start scan.

        :param config_str: Scan ID configuration JSON string

        """
        # Validate the configuration string
        sbi = self._validate_scan(config_str)

        # Update subarray and SBI in the config DB
        subarray = {}
        self._subarray_add_command(subarray, 'Scan', ObsState.SCANNING)
        self._config.update_subarray_sbi(subarray=subarray, sbi=sbi)

    def is_EndScan_allowed(self):
        """Check if the EndScan command is allowed."""
        commname = 'EndScan'
        self._command_allowed_state(commname, [DevState.ON])
        self._command_allowed_obs_state(commname, [ObsState.SCANNING])
        return True

    @log_command
    @command
    def EndScan(self):
        """End scan."""
        # Update subarray and SBI in the config DB
        subarray = {}
        self._subarray_add_command(subarray, 'EndScan', ObsState.READY)
        sbi = {'scan_id': None}
        self._config.update_subarray_sbi(subarray=subarray, sbi=sbi)

    def is_End_allowed(self):
        """Check if the End command is allowed."""
        commname = 'End'
        self._command_allowed_state(commname, [DevState.ON])
        self._command_allowed_obs_state(commname, [ObsState.READY])
        return True

    @log_command
    @command
    def End(self):
        """End."""
        # Update subarray and SBI in the config DB
        subarray = {}
        self._subarray_add_command(subarray, 'End', ObsState.IDLE)
        sbi = {'current_scan_type': None, 'scan_id': None}
        self._config.update_subarray_sbi(subarray=subarray, sbi=sbi)

    def is_Abort_allowed(self):
        """Check if the Abort command is allowed."""
        commname = 'Abort'
        self._command_allowed_state(commname, [DevState.ON])
        self._command_allowed_obs_state(
            command,
            [ObsState.IDLE, ObsState.CONFIGURING, ObsState.READY,
             ObsState.SCANNING, ObsState.RESETTING]
        )
        return True

    @log_command
    @command
    def Abort(self):
        """Abort the current activity."""
        # Update subarray in the config DB
        subarray = {}
        self._subarray_add_command(subarray, 'Abort', ObsState.ABORTED)
        self._config.update_subarray_sbi(subarray=subarray)

    def is_ObsReset_allowed(self):
        """Check if the ObsReset command is allowed."""
        commname = 'ObsReset'
        self._command_allowed_state(commname, [DevState.ON])
        self._command_allowed_obs_state(commname, [ObsState.ABORTED,
                                                   ObsState.FAULT])
        return True

    @log_command
    @command
    def ObsReset(self):
        """Reset the subarray to the IDLE obsState."""
        # Update subarray and SBI in the config DB
        subarray = {}
        self._subarray_add_command(subarray, 'ObsReset', ObsState.IDLE)
        sbi = {'current_scan_type': None, 'scan_id': None}
        self._config.update_subarray_sbi(subarray=subarray, sbi=sbi)

    def is_Restart_allowed(self):
        """Check if the Restart command is allowed."""
        commname = 'Restart'
        self._command_allowed_state(commname, [DevState.ON])
        self._command_allowed_obs_state(commname, [ObsState.ABORTED,
                                                   ObsState.FAULT])
        return True

    @log_command
    @command
    def Restart(self):
        """Restart the subarray in the EMPTY obsState."""
        # Update subarray and SBI in the config DB
        subarray = {'sbi_id': None}
        self._subarray_add_command(subarray, 'Restart', ObsState.EMPTY)
        sbi = {'subarray_id': None, 'status': 'CANCELLED',
               'current_scan_type': None, 'scan_id': None}
        self._config.update_subarray_sbi(subarray=subarray, sbi=sbi)

    # ----------------------
    # Command allowed method
    # ----------------------

    def _command_allowed_obs_state(self, commname, allowed):
        """Check if command is allowed in current obsState.

        :param commname: name of the command
        :param allowed: list of allowed obsState values

        """
        self._command_allowed(commname, 'obsState', self._obs_state, allowed)

    # --------------------------------------
    # Command validation and parsing methods
    # --------------------------------------

    def _validate_assign_resources(self, config_str):
        """Validate AssignResources command configuration.

        :param config_str:
        :returns: update to subarray, SBI and list of processing blocks

        """
        # Log the configuration string
        log_lines(config_str, MSG_CONFIG_STR)

        # Validate the configuration string against the JSON schema
        config = self._validate_json_config(config_str,
                                            'assign_resources.json')

        if config is None:
            # Validation has failed, so raise an error
            self._raise_command_failed(
                MSG_VALIDATION_FAILED, 'SDPSubarray.AssignResources()'
            )

        # Check IDs against existing IDs in the config DB
        ok = self._validate_check_ids(config)

        if not ok:
            # Duplicate ID found, so raise an error
            self._raise_command_failed(
                MSG_DUPLICATE_ID, 'SDPSubarray.AssignResources()'
            )

        subarray = {'sbi_id': config.get('id')}
        # Parse the configuration to get the SBI and PBs
        sbi, pbs = self._validate_get_sbi_pbs(config)

        return subarray, sbi, pbs

    def _validate_check_ids(self, config):
        """Check IDs in the configuration against existing ones.

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
        existing_sbi_ids, existing_pb_ids = self._config.list_sbis_pbs()

        # Check for duplicates
        ok = True
        if sbi_id in existing_sbi_ids:
            ok = False
            LOG.error('Scheduling block instance %s already exists', sbi_id)
        for pb_id in pb_ids:
            if pb_id in existing_pb_ids:
                ok = False
                LOG.error('Processing block %s already exists', pb_id)

        return ok

    def _validate_get_sbi_pbs(self, config):
        """Parse the configuration to get the SBI and PBs.

        :param config: configuration data
        :returns: SBI and list of PBs

        """
        # Initialise scheduling block instance

        sbi_id = config.get('id')

        sbi = {
            'id': sbi_id,
            'subarray_id': self._config.subarray_id,
            'scan_types': config.get('scan_types'),
            'pb_realtime': [],
            'pb_batch': [],
            'pb_receive_addresses': None,
            'current_scan_type': None,
            'scan_id': None,
            'status': 'ACTIVE'
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
                sbi['pb_realtime'].append(pb_id)
            elif wf_type == 'batch':
                sbi['pb_batch'].append(pb_id)
            else:
                LOG.error('Unknown workflow type: %s', wf_type)

            parameters = pbc.get('parameters')

            dependencies = []
            if 'dependencies' in pbc:
                if wf_type == 'realtime':
                    LOG.error('dependencies attribute must not appear in '
                              'real-time processing block configuration')
                if wf_type == 'batch':
                    dependencies = pbc.get('dependencies')

            # Add processing block to list
            pbs.append(
                ska_sdp_config.ProcessingBlock(
                    pb_id, sbi_id, workflow,
                    parameters=parameters,
                    dependencies=dependencies
                )
            )

        return sbi, pbs

    def _validate_configure(self, config_str):
        """Validate Configure command configuration.

        :param config_str: configuration string
        :returns: update to be applied to SBI

        """
        # Log the configuration string
        log_lines(config_str, MSG_CONFIG_STR)

        # Validate the configuration string against JSON schema
        config = self._validate_json_config(config_str, 'configure.json')

        if config is None:
            # Validation has failed, so raise an error
            self._raise_command_failed(
                MSG_VALIDATION_FAILED, 'SDPSubarray.Configure()'
            )

        # Parse configuration to get scan type
        sbi = self._validate_get_scan_type(config)

        if sbi is None:
            # Validation has failed, so raise an error
            self._raise_command_failed(
                MSG_VALIDATION_FAILED, 'SDPSubarray.Configure()'
            )

        return sbi

    def _validate_get_scan_type(self, config):
        """Parse the configuration to get the scan type.

        If new scan types are supplied, they are appended to the current
        list.

        :param config: configuration data
        :returns: update to be applied to SBI

        """
        new_scan_types = config.get('new_scan_types')
        scan_type = config.get('scan_type')

        # Get the existing scan types from SBI
        sbi = self._config.get_sbi()
        scan_types = sbi.get('scan_types')

        # Extend the list of scan types with new ones, if supplied
        if new_scan_types is not None:
            scan_types.extend(new_scan_types)

        # Check scan type is in the list of scan types
        scan_type_ids = [st.get('id') for st in scan_types]
        if scan_type not in scan_type_ids:
            LOG.error('Unknown scan_type: %s', scan_type)
            return None

        # Set current scan type, and update list of scan types if it has
        # been extended
        sbi = {'current_scan_type': scan_type}
        if new_scan_types is not None:
            sbi.update({'scan_types': scan_types})

        return sbi

    def _validate_scan(self, config_str):
        """Validate Scan command configuration.

        :param config_str: configuration string
        :returns: update to be applied to SBI

        """
        # Log the configuration string
        log_lines(config_str, MSG_CONFIG_STR)

        # Validate the configuration string against the JSON schema
        config = self._validate_json_config(config_str, 'scan.json')

        if config is None:
            # Validation has failed, so raise an error
            self._raise_command_failed(
                MSG_VALIDATION_FAILED, 'SDPSubarray.Scan()'
            )

        sbi = {'scan_id': config.get('id')}

        return sbi

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

    # -------------------------
    # Attribute-setting methods
    # -------------------------

    def _set_state(self, value):
        """Set device state."""
        if self.get_state() != value:
            LOG.debug('Setting device state to %s', value.name)
            self.set_state(value)

    def _set_obs_state(self, value):
        """Set obsState and push a change event."""
        if self._obs_state != value:
            LOG.debug('Setting obsState to %s', value.name)
            self._obs_state = value
            self.push_change_event('obsState', self._obs_state)

    def _set_admin_mode(self, value):
        """Set adminMode and push a change event."""
        if self._admin_mode != value:
            LOG.debug('Setting adminMode to %s', value.name)
            self._admin_mode = value
            self.push_change_event('adminMode', self._admin_mode)

    def _set_health_state(self, value):
        """Set healthState and push a change event."""
        if self._health_state != value:
            LOG.debug('Setting healthState to %s', value.name)
            self._health_state = value
            self.push_change_event('healthState', self._health_state)

    def _set_receive_addresses(self, value):
        """Set receiveAddresses and push a change event."""
        if self._receive_addresses != value:
            if value is None:
                LOG.debug('Clearing receiveAddresses')
            else:
                LOG.debug('Setting receiveAddresses')
            self._receive_addresses = value
            self.push_change_event('receiveAddresses',
                                   json.dumps(self._receive_addresses))

    def _set_scan_type(self, value):
        """Set scanType and push a change event."""
        if self._scan_type != value:
            LOG.debug('Setting scanType to %s', value)
            self._scan_type = value
            self.push_change_event('scanType', self._scan_type)

    def _set_scan_id(self, value):
        """Set scanID and push a change event."""
        if self._scan_id != value:
            LOG.debug('Setting scanID to %d', value)
            self._scan_id = value
            self.push_change_event('scanID', self._scan_id)

    # ------------------
    # Event loop methods
    # ------------------

    def _start_event_loop(self):
        """Start event loop."""
        if FEATURE_EVENT_LOOP.is_active():
            # Start event loop in thread
            thread = threading.Thread(
                target=self._event_loop, name='EventLoop', daemon=True
            )
            thread.start()
        else:
            # Add command to manually update attributes
            thread = None
            cmd = command(f=self.update_attributes)
            self.add_command(cmd, True)
        return thread

    def _event_loop(self):
        """Event loop to update attributes automatically."""
        LOG.info('Starting event loop')
        # Use EnsureOmniThread to make it thread-safe under Tango
        with EnsureOmniThread():
            self._set_attributes()

    def update_attributes(self):
        """Update the device attributes manually."""
        LOG.info('Updating attributes')
        self._set_attributes(loop=False)

    def _set_attributes(self, loop=True):
        """Set attributes based on configuration.

        if `loop` is `True`, it acts as an event loop to watch for changes to
        the configuration. If `loop` is `False` it makes a single pass.

        :param loop: watch for changes to configuration and loop

        """
        for txn in self._config.db_client.txn():

            # Get the following from the config DB:
            #   - subarray
            #   - SBI
            #   - receive addresses
            subarray = txn.get_subarray(self._config.subarray_id)
            sbi_id = subarray.get('sbi_id')
            if sbi_id is None:
                # No SBI, so set values to default
                sbi = {}
                receive_addresses = None
            else:
                # Get SBI
                sbi = txn.get_scheduling_block(sbi_id)
                # Get receive addresses
                pb_receive_addresses = sbi.get('pb_receive_addresses')
                if pb_receive_addresses is None:
                    receive_addresses = None
                else:
                    pb_state = \
                        txn.get_processing_block_state(pb_receive_addresses)
                    receive_addresses = pb_state.get('receive_addresses')

            # Set device state
            state = subarray.get('state')
            self._set_state(DevState.names[state])

            # Set obsState
            obs_state_target = subarray.get('obs_state_target')
            last_command = subarray.get('last_command')
            if obs_state_target == 'IDLE' and \
                    last_command == 'AssignResources':
                if receive_addresses is None:
                    obs_state = ObsState.RESOURCING
                else:
                    obs_state = ObsState.IDLE
            else:
                obs_state = ObsState[obs_state_target]
            self._set_obs_state(obs_state)

            # Set receive addresses
            self._set_receive_addresses(receive_addresses)

            # Set scan type
            scan_type = sbi.get('current_scan_type')
            self._set_scan_type('null' if scan_type is None else scan_type)

            # Set scan ID
            scan_id = sbi.get('scan_id')
            self._set_scan_id(0 if scan_id is None else scan_id)

            if loop:
                # Loop the transaction when the config entries are changed
                txn.loop(wait=True)

    # ---------------
    # Utility methods
    # ---------------

    def _get_subarray_id(self):
        """Get subarray ID.

        The ID is the number of the subarray device, which is extracted from
        the device name.

        :returns: subarray ID

        """
        member = self.get_name().split('/')[2]
        number = member.split('_')[1]
        subarray_id = number.zfill(2)
        return subarray_id

    @staticmethod
    def _subarray_add_command(subarray, commname, obs_state):
        """Add information about command to subarray update.

        :param subarray: dict containing subarray update
        :param commname: command name
        :param obs_state: target obsState

        """
        command_info = {
            'last_command': commname,
            'obs_state_target': obs_state.name
        }
        subarray.update(command_info)


def main(args=None, **kwargs):
    """Run server."""
    # Initialise logging
    log_level = LogLevel.LOG_INFO
    if len(sys.argv) > 2 and '-v' in sys.argv[2]:
        log_level = LogLevel.LOG_DEBUG
    tango_logging.set_level(log_level)

    # Register SIGTERM handler.
    signal.signal(signal.SIGTERM, terminate)

    return run((SDPSubarray,), args=args, **kwargs)
