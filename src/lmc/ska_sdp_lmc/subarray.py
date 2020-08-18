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

import jsonschema

from tango import AttrWriteType, DevState, LogLevel
from tango.server import attribute, command, run

from ska_sdp_logging import tango_logging
import ska_sdp_config

from .attributes import AdminMode, HealthState, ObsState
from .base import SDPDevice
from .util import terminate, log_command, log_lines
from .subarray_config import SubarrayConfig

LOG = logging.getLogger()
CONFIG_MSG = 'Configuration string:'
VALIDATION_MSG = 'Configuration validation failed'


class SDPSubarray(SDPDevice):
    """SDP Subarray device class.

    .. note::
        This should eventually inherit from SKASubarray but these need
        some work before doing so would add any value to this device.

    """

    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=no-self-use

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

        # Initialise attributes
        self._set_obs_state(ObsState.EMPTY)
        self._set_admin_mode(AdminMode.ONLINE)
        self._set_health_state(HealthState.OK)
        self._set_receive_addresses(None)

        # Initialise instance variables
        self._config = SubarrayConfig()

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

    def read_processingBlockState(self):
        """Get the states of the real-time processing blocks.

        :returns: JSON describing real-time processing block states

        """
        return json.dumps(self._config.get_processing_block_state())

    def read_schedulingBlockInstance(self):
        """Get the scheduling block instance.

        :returns: JSON describing scheduling block instance

        """
        return json.dumps(self._config.get_scheduling_block())

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

    @log_command
    @command
    def On(self):
        """Set the subarray device into its Operational state."""
        # Setting device state to ON state
        LOG.debug('Setting device state to ON')
        self.set_state(DevState.ON)

    def is_Off_allowed(self):
        """Check if the Off command is allowed."""
        return self._command_allowed(
            'Off',
            state_allowed=[DevState.ON]
        )

    @log_command
    @command
    def Off(self):
        """Set the subarray device to inactive state."""
        # Setting device state to OFF state
        LOG.debug('Setting device state to OFF')
        self.set_state(DevState.OFF)

        if self._obs_state != ObsState.EMPTY:
            LOG.info('obsState is not EMPTY')

            if self._config.is_sbi_active():
                LOG.info('Cancelling the scheduling block instance')

                # Clear scan type, scan ID and set status to CANCELLED
                self._config.update_sb({'current_scan_type': None,
                                        'scan_id': None,
                                        'status': 'CANCELLED'})

                # Clear the receive addresses
                self._set_receive_addresses(None)

                # Clear the scheduling block instance ID
                self._config.clear_sbi()

            # Set obsState to EMPTY
            self._set_obs_state(ObsState.EMPTY)

    def is_AssignResources_allowed(self):
        """Check if the AssignResources command is allowed."""
        return self._command_allowed(
            'AssignResources',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.EMPTY],
            admin_mode_allowed=[AdminMode.ONLINE, AdminMode.MAINTENANCE,
                                AdminMode.RESERVED]
        )

    @log_command
    @command(dtype_in=str, doc_in='Resource configuration JSON string')
    def AssignResources(self, config_str):
        """Assign resources to the subarray.

        This creates the processing blocks associated with the
        scheduling block instance.

        :param config_str: Resource configuration JSON string

        """
        # Set obsState to RESOURCING
        self._set_obs_state(ObsState.RESOURCING)

        # Log the JSON configuration string
        log_lines(config_str, header=CONFIG_MSG)

        # Validate the JSON configuration string
        config = self._validate_json_config(
            config_str, 'assign_resources.json')

        if config is None:
            # Validation has failed, so set obsState to FAULT and raise
            # an error
            self._set_obs_state(ObsState.FAULT)
            self._raise_command_error(
                VALIDATION_MSG,
                origin='SDPSubarray.AssignResources()'
            )

        # Check IDs against existing IDs in the config DB
        ok = self._config_check_ids(config)

        if not ok:
            # Duplicate scheduling block, so set obsState to FAULT and
            # raise an error
            self._set_obs_state(ObsState.FAULT)
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
            self._set_obs_state(ObsState.FAULT)
            self._raise_command_error(
                'Creation of scheduling block and processing blocks failed',
                origin='SDPSubarray.AssignResources()'
            )

        # Set the scheduling block instance ID
        self._config.sbi_id = config.get('id')

        # Get the receive addresses and publish them on the attribute
        receive_addresses = self._config.get_receive_addresses()
        self._set_receive_addresses(receive_addresses)

        # Set obsState to IDLE
        self._set_obs_state(ObsState.IDLE)

    def is_ReleaseResources_allowed(self):
        """Check if the ReleaseResources command is allowed."""
        return self._command_allowed(
            'ReleaseResources',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.IDLE],
            admin_mode_allowed=[AdminMode.OFFLINE, AdminMode.NOT_FITTED],
            admin_mode_invert=True
        )

    @log_command
    @command
    def ReleaseResources(self):
        """Release resources assigned to the subarray.

        This ends the real-time processing blocks associated with the
        scheduling block instance.

        """
        # Set obsState to RESOURCING
        self._set_obs_state(ObsState.RESOURCING)

        # Set status to FINISHED
        self._config.update_sb({'status': 'FINISHED'})

        # Clear the receive addresses
        self._set_receive_addresses(None)

        # Clear the scheduling block instance ID
        self._config.clear_sbi()

        # Set obsState to EMPTY
        self._set_obs_state(ObsState.EMPTY)

    def is_Configure_allowed(self):
        """Check if the Configure command is allowed."""
        return self._command_allowed(
            'Configure',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.IDLE, ObsState.READY]
        )

    @log_command
    @command(dtype_in=str, doc_in='Scan type configuration JSON string')
    def Configure(self, config_str):
        """Configure SDP scan type.

        :param config_str: Scan type configuration JSON string

        """
        # Set obsState to CONFIGURING
        self._set_obs_state(ObsState.CONFIGURING)

        # Log the JSON configuration string
        log_lines(config_str, header=CONFIG_MSG)

        # Validate the JSON configuration string
        config = self._validate_json_config(config_str, 'configure.json')

        if config is None:
            # Validation has failed, so set obsState to FAULT and raise
            # an error
            self._set_obs_state(ObsState.FAULT)
            self._raise_command_error(
                VALIDATION_MSG,
                origin='SDPSubarray.Configure()'
            )

        # Append new scan types if supplied, and set the scan type
        ok = self._config_set_scan_type(config)

        if not ok:
            # Scan type configuration has failed, so set obsState to FAULT
            # and raise an error
            self._set_obs_state(ObsState.FAULT)
            self._raise_command_error(
                'Scan type configuration failed',
                origin='SDPSubarray.Configure()'
            )

        # Set status to READY
        self._config.update_sb({'status': 'READY'})

        # Set obsState to READY
        self._set_obs_state(ObsState.READY)

    def is_Scan_allowed(self):
        """Check if the Scan command is allowed."""
        return self._command_allowed(
            'Scan',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.READY]
        )

    @log_command
    @command(dtype_in=str, doc_in='Scan ID configuration JSON string')
    def Scan(self, config_str):
        """Start scan.

        :param config_str: Scan ID configuration JSON string

        """
        # Log the JSON configuration string
        log_lines(config_str, header=CONFIG_MSG)

        # Validate the JSON configuration string
        config = self._validate_json_config(config_str, 'scan.json')

        if config is None:
            # Validation has failed, so set obsState to FAULT and raise
            # an error
            self._set_obs_state(ObsState.FAULT)
            self._raise_command_error(
                VALIDATION_MSG,
                origin='SDPSubarray.Scan()'
            )

        # Get the scan ID
        scan_id = config.get('id')

        # Set scan ID and set status to SCANNING
        self._config.update_sb({'scan_id': scan_id, 'status': 'SCANNING'})

        # Set obsState to SCANNING
        self._set_obs_state(ObsState.SCANNING)

    def is_EndScan_allowed(self):
        """Check if the EndScan command is allowed."""
        return self._command_allowed(
            'EndScan',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.SCANNING]
        )

    @log_command
    @command
    def EndScan(self):
        """End scan."""
        # Clear scan ID and set status to READY
        self._config.update_sb({'scan_id': None, 'status': 'READY'})

        # Set obsState to READY
        self._set_obs_state(ObsState.READY)

    def is_End_allowed(self):
        """Check if the Reset command is allowed."""
        return self._command_allowed(
            'End',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.READY]
        )

    @log_command
    @command
    def End(self):
        """End."""
        # Clear scan type and scan ID, and set status to IDLE
        self._config.update_sb({'current_scan_type': None, 'scan_id': None,
                                'status': 'IDLE'})

        # Set obsState to IDLE
        self._set_obs_state(ObsState.IDLE)

    def is_Abort_allowed(self):
        """Check if the Abort command is allowed."""
        return self._command_allowed(
            'Abort',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.IDLE, ObsState.CONFIGURING,
                               ObsState.READY, ObsState.SCANNING,
                               ObsState.RESETTING]
        )

    @log_command
    @command
    def Abort(self):
        """Abort the subarray device."""
        # Set obsState to ABORTING
        self._set_obs_state(ObsState.ABORTING)

        # Set status to ABORTED
        self._config.update_sb({'status': 'ABORTED'})

        # Set obsState to IDLE
        self._set_obs_state(ObsState.ABORTED)

    def is_ObsReset_allowed(self):
        """Check if the ObsReset command is allowed."""
        return self._command_allowed(
            'ObsReset',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.ABORTED, ObsState.FAULT]
        )

    @log_command
    @command
    def ObsReset(self):
        """Set obsState to the last known stable state.

        In the case of the subarray device this is Idle.
        """
        # Set obsState to RESETTING
        self._set_obs_state(ObsState.RESETTING)

        if not self._config.is_sbi_active():
            message = 'Scheduling block instance is not configured, ' + \
                'ObsReset is not permitted'
            LOG.error(message)
            self._set_obs_state(ObsState.FAULT)
            self._raise_command_error(
                message,
                origin='SDPSubarray.ObsReset()'
            )

        # Clear scan type and scan ID, and set status to IDLE
        self._config.update_sb({'current_scan_type': None, 'scan_id': None,
                                'status': 'IDLE'})

        # Set obsState to IDLE
        self._set_obs_state(ObsState.IDLE)

    def is_Restart_allowed(self):
        """Check if the Restart command is allowed."""
        return self._command_allowed(
            'Restart',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.ABORTED, ObsState.FAULT]
        )

    @log_command
    @command
    def Restart(self):
        """Restart the subarray device.

        This is like a "hard" reset
        """
        # Set obsState to RESTARTING
        self._set_obs_state(ObsState.RESTARTING)

        if self._config.is_sbi_active():
            # Clear scan type and scan ID, and set status to CANCELLED
            self._config.update_sb({'current_scan_type': None,
                                    'scan_id': None,
                                    'status': 'CANCELLED'})

            # Clear the receiveAddresses attribute
            self._set_receive_addresses(None)

            # Clear the scheduling block instance ID
            self._config.clear_sbi()

        # Set obsState to EMPTY
        self._set_obs_state(ObsState.EMPTY)

    # -------------------------------------
    # Private methods
    # -------------------------------------

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
        existing_sb_ids, existing_pb_ids = self._config.get_existing_ids()

        # Check for duplicate IDs
        ok = True
        if sbi_id in existing_sb_ids:
            ok = False
            LOG.error('Scheduling block instance %s already exists', sbi_id)
        pb_dup = [pb_id for pb_id in pb_ids if pb_id in existing_pb_ids]
        if pb_dup:
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
            'max_length': config.get('max_length'),
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
        self._config.create_sb_and_pbs(sb, pbs)

        return True

    def _config_set_scan_type(self, config):
        """Parse the configuration and set the scan type.

        If new scan types are supplied, they are appended to the current
        list.

        :param config: configuration data
        :returns: True if the configuration is good, False if there is an
            error

        """
        new_scan_types = config.get('new_scan_types')
        scan_type = config.get('scan_type')
        return self._config.set_scan_type(new_scan_types, scan_type)


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
