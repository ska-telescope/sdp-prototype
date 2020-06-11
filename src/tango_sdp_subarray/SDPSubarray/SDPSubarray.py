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
from enum import IntEnum, unique

from ska_sdp_logging import tango_logging

import tango
from tango import AttrWriteType, ConnectionFailed, Database, \
    DbDevInfo, DevState
from tango.server import Device, DeviceMeta, attribute, command, \
    device_property, run

import jsonschema

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from release import VERSION as SERVER_VERSION   # noqa

try:
    import ska_sdp_config
except ImportError:
    ska_sdp_config = None

LOG = logging.getLogger()


# https://pytango.readthedocs.io/en/stable/data_types.html#devenum-pythonic-usage
@unique
class AdminMode(IntEnum):
    """AdminMode enum."""

    OFFLINE = 0
    ONLINE = 1
    MAINTENANCE = 2
    NOT_FITTED = 3
    RESERVED = 4


@unique
class HealthState(IntEnum):
    """HealthState enum."""

    OK = 0
    DEGRADED = 1
    FAILED = 2
    UNKNOWN = 3


@unique
class ObsState(IntEnum):
    """ObsState enum."""

    IDLE = 0
    CONFIGURING = 1
    READY = 2
    SCANNING = 3
    PAUSED = 4
    ABORTED = 5
    FAULT = 6


@unique
class FeatureToggle(IntEnum):
    """Feature Toggles."""

    CONFIG_DB = 1  #: Enable / Disable the Config DB
    AUTO_REGISTER = 2  #: Enable / Disable Tango DB auto-registration
    RECEIVE_ADDRESSES = 3  # Enable / Disable Receive Addresses from file


# class SDPSubarray(SKASubarray):
class SDPSubarray(Device):
    """SDP Subarray device class.

    .. note::
        This should eventually inherit from SKASubarray but these need
        some work before doing so would add any value to this device.

    """

    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=no-self-use

    __metaclass__ = DeviceMeta

    # -----------------
    # Device Properties
    # -----------------

    SdpMasterAddress = device_property(
        dtype='str',
        doc='FQDN of the SDP Master',
        default_value='mid_sdp/elt/master'
    )

    # ----------
    # Attributes
    # ----------

    serverVersion = attribute(
        label='Server Version',
        dtype=str,
        access=AttrWriteType.READ,
        doc='The version of the SDP Subarray device'
    )

    obsState = attribute(
        label='Obs State',
        dtype=ObsState,
        access=AttrWriteType.READ,
        doc='The device obs state.'
        # polling_period=1000
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
        # SKASubarray.init_device(self)
        Device.init_device(self)

        self.set_state(DevState.INIT)
        LOG.info('Initialising SDP Subarray: %s', self.get_name())

        # These attributes are updated with push_change_event
        self.set_change_event('obsState', True)
        self.set_change_event('adminMode', True)
        self.set_change_event('healthState', True)
        self.set_change_event('receiveAddresses', True, False)

        # Initialise attributes
        self._set_obs_state(ObsState.IDLE)
        self._set_admin_mode(AdminMode.ONLINE)
        self._set_health_state(HealthState.OK)
        self._set_receive_addresses(None)

        # Initialise instance variables
        self._sbi_id = None

        if ska_sdp_config is not None \
                and self.is_feature_active(FeatureToggle.CONFIG_DB):
            self._config_db_client = ska_sdp_config.Config()
            LOG.debug('SDP Config DB enabled')
        else:
            self._config_db_client = None
            LOG.warning('SDP Config DB disabled %s',
                        '(ska_sdp_config package not found)'
                        if ska_sdp_config is None
                        else 'by feature toggle')

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

    def read_serverVersion(self):
        """Get the SDPSubarray device server version attribute.

        :returns: The SDP subarray device server version.

        """
        return SERVER_VERSION

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

    def is_AssignResources_allowed(self):
        """Check if the AssignResources command is allowed."""
        return self._command_allowed(
            'AssignResources',
            state_allowed=[DevState.OFF],
            obs_state_allowed=[ObsState.IDLE],
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

        # Log the JSON configuration string
        LOG.info('Configuration string:')
        for line in config_str.splitlines():
            LOG.info(line)

        # Validate the JSON configuration string
        config = self._validate_json_config(
            config_str, 'assign_resources.json')

        if config is None:
            # Validation has failed, so raise error
            self._raise_command_error(
                'Configuration validation failed',
                origin='SDPSubarray.AssignResources()'
            )
            return

        # Check IDs against existing IDs in the config DB
        ok = self._config_check_ids(config)

        if not ok:
            self._raise_command_error(
                'Duplicate scheduling block instance ID or processing block'
                ' ID in configuration',
                origin='SDPSubarray.AssignResources()'
            )
            return

        # Create SB and PBs in config DB
        ok = self._config_create_sb_and_pbs(config)

        if not ok:
            self._raise_command_error(
                'Creation of scheduling block and processing blocks failed',
                origin='SDPSubarray.AssignResources()'
            )
            return

        # Set the scheduling block instance ID
        self._sbi_id = config.get('id')

        # Get the receive addresses and publish them on the attribute
        receive_addresses = self._get_receive_addresses()
        self._set_receive_addresses(receive_addresses)

        LOG.debug('Setting device state to ON')
        self.set_state(DevState.ON)

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

        # Set status to FINISHED
        self._update_sb({'status': 'FINISHED'})

        # Clear the scheduling block instance ID
        self._sbi_id = None

        LOG.debug('Setting device state to OFF')
        self.set_state(DevState.OFF)

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

        # Log the JSON configuration string
        LOG.info('Configuration string:')
        for line in config_str.splitlines():
            LOG.info(line)

        # Validate the JSON configuration string
        config = self._validate_json_config(config_str, 'configure.json')

        if config is None:
            # Validation has failed, so set obsState to IDLE and raise
            # an error
            self._set_obs_state(ObsState.IDLE)
            self._raise_command_error(
                'Configuration validation failed',
                origin='SDPSubarray.Configure()'
            )
            return

        # Append new scan types if supplied, and set the scan type
        ok = self._config_set_scan_type(config)

        if not ok:
            # Scan type configuration has failed, so set obsState to IDLE
            # and raise an error
            self._set_obs_state(ObsState.IDLE)
            self._raise_command_error(
                'Scan type configuration failed',
                origin='SDPSubarray.Configure()'
            )
            return

        # Set status to READY
        self._update_sb({'status': 'READY'})

        # Set the obsState to READY
        self._set_obs_state(ObsState.READY)

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

        # Log the JSON configuration string
        LOG.info('Configuration string:')
        for line in config_str.splitlines():
            LOG.info(line)

        # Validate the JSON configuration string
        config = self._validate_json_config(config_str, 'scan.json')

        if config is None:
            # Validation has failed, so set obsState back to IDLE and raise
            # an error
            self._raise_command_error(
                'Configuration validation failed',
                origin='SDPSubarray.Scan()'
            )
            return

        # Get the scan ID
        scan_id = config.get('id')

        # Set scan ID and set status to SCANNING
        self._update_sb({'scan_id': scan_id, 'status': 'SCANNING'})

        # Set obsState to SCANNING
        self._set_obs_state(ObsState.SCANNING)

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

        # Clear scan ID and set status to READY
        self._update_sb({'scan_id': None, 'status': 'READY'})

        # Set obsState to READY
        self._set_obs_state(ObsState.READY)

        LOG.info('-------------------------------------------------------')
        LOG.info('EndScan Successful')
        LOG.info('-------------------------------------------------------')

    def is_Reset_allowed(self):
        """Check if the Reset command is allowed."""
        return self._command_allowed(
            'Reset',
            state_allowed=[DevState.ON],
            obs_state_allowed=[ObsState.READY, ObsState.FAULT]
        )

    @command
    def Reset(self):
        """Reset to IDLE."""
        LOG.info('-------------------------------------------------------')
        LOG.info('Reset (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Clear scan type and scan ID, and set status to 'IDLE'
        self._update_sb({'current_scan_type': None, 'scan_id': None,
                         'status': 'IDLE'})

        # Clear receive addresses
        self._set_receive_addresses(None)

        # Set obsState to IDLE
        self._set_obs_state(ObsState.IDLE)

        LOG.info('-------------------------------------------------------')
        LOG.info('Reset Successful')
        LOG.info('-------------------------------------------------------')

    # -------------------------------------
    # Public methods
    # -------------------------------------

    @staticmethod
    def set_feature_toggle_default(feature_name, default):
        """Set the default value of a feature toggle.

        :param feature_name: Name of the feature
        :param default: Default for the feature toggle (if it is not set)

        """
        env_var = SDPSubarray._get_feature_toggle_env_var(feature_name)
        if not os.environ.get(env_var):
            LOG.debug('Setting default for toggle: %s = %s', env_var, default)
            os.environ[env_var] = str(int(default))

    @staticmethod
    def is_feature_active(feature_name):
        """Check if feature is active.

        :param feature_name: Name of the feature.
        :returns: True if the feature toggle is enabled.

        """
        env_var = SDPSubarray._get_feature_toggle_env_var(feature_name)
        env_var_value = os.environ.get(env_var)
        return env_var_value == '1'

    # -------------------------------------
    # Private methods
    # -------------------------------------

    @staticmethod
    def _get_feature_toggle_env_var(feature_name):
        """Get the env var associated with the feature toggle.

        :param feature_name: Name of the feature.
        :returns: environment variable name for feature toggle.

        """
        if isinstance(feature_name, FeatureToggle):
            feature_name = feature_name.name
        env_var = str('toggle_' + feature_name).upper()
        allowed = ['TOGGLE_' + toggle.name for toggle in FeatureToggle]
        if env_var not in allowed:
            message = 'Unknown feature toggle: {} (allowed: {})' \
                .format(env_var, allowed)
            LOG.error(message)
            raise ValueError(message)
        return env_var

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

    def _raise_command_error(self, desc, origin=''):
        """Raise a command error.

        :param desc: Error message / description.
        :param origin: Error origin (optional).

        """
        self._raise_error(desc, reason='API_CommandFailed', origin=origin)

    def _raise_error(self, desc, reason='', origin=''):
        """Raise an error.

        :param desc: Error message / description.
        :param reason: Reason for the error.
        :param origin: Error origin (optional).

        """
        if reason != '':
            LOG.error(reason)
        LOG.error(desc)
        if origin != '':
            LOG.error(origin)
        tango.Except.throw_exception(reason, desc, origin,
                                     tango.ErrSeverity.ERR)

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
        # Utility function for composing the error message
        def compose_message(message_inp, name, state, value):
            if message_inp == '':
                message_out = 'Command {} not allowed when {} is {}' \
                              ''.format(name, state, value)
            else:
                message_out = '{}, or when {} is {}' \
                              ''.format(message_inp, state, value)
            return message_out

        allowed = True
        message = ''

        # Tango device state
        if state_allowed is not None:
            if self.get_state() not in state_allowed:
                allowed = False
                message = compose_message(message, name, 'the device',
                                          self.get_state())

        # Observing state
        if obs_state_allowed is not None:
            if self._obs_state not in obs_state_allowed:
                allowed = False
                message = compose_message(message, name, 'obsState',
                                          self._obs_state.name)

        # Administration mode
        if admin_mode_allowed is not None:
            condition = self._admin_mode not in admin_mode_allowed
            if admin_mode_invert:
                condition = not condition
            if condition:
                allowed = False
                message = compose_message(message, name, 'adminMode',
                                          self._admin_mode.name)

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

    def _get_receive_addresses(self):
        """Get the receive addresses for the current scan type.

        The channel link map for each scan type is contained in the list of
        scan types in the SB. The ingest workflow uses them to generate the
        receive addresses for each scan type and writes them to the processing
        block state. This function retrieves them from the processing block
        state and extracts the set for the current scan type.

        If the feature toggle is true
        This version returns a fixed set of receive addresses read from
        a JSON file.

        :returns: receive address as dict

        """

        if not SDPSubarray.is_feature_active(FeatureToggle.RECEIVE_ADDRESSES):
            if self._config_db_client is None:
                return None

            # Get ID of PB that is generating the receive addresses and scan type
            for txn in self._config_db_client.txn():
                sb = txn.get_scheduling_block(self._sbi_id)
            pb_id = sb.get('pb_receive_addresses')
            scan_type = sb.get('current_scan_type')

            # If no PB is configured to generate the receive addresses, return None
            if pb_id is None:
                return None

            # Get the list of receive address configurations for all scan types
            # and pick out the right one
            for txn in self._config_db_client.txn():
                pb_state = txn.get_processing_block_state(pb_id)
                if pb_state is None:
                    return None
            receive_addresses_list = pb_state.get('receive_addresses')
            if receive_addresses_list is None:
                return None
            receive_addresses = receive_addresses_list
            
            # for ra in receive_addresses_list:
            #     receive_addresses = ra
                # if ra.get('scanType') == scan_type:
                #     receive_addresses = ra
                #     break
        else:
            ra_file = os.path.join(os.path.dirname(__file__),
                                   'receive_addresses.json')
            with open(ra_file, 'r') as file:
                receive_addresses = json.load(file)

        return receive_addresses


def delete_device_server(instance_name='*'):
    """Delete (unregister) SDPSubarray device server instance(s).

    :param instance_name: Optional, name of the device server instance to
                          remove. If not specified all service instances will
                          be removed.

    """
    try:
        tango_db = Database()
        class_name = 'SDPSubarray'
        server_name = '{}/{}'.format(class_name, instance_name)
        for server_name in list(tango_db.get_server_list(server_name)):
            LOG.info('Removing device server: %s', server_name)
            tango_db.delete_server(server_name)
    except ConnectionFailed:
        pass


def register(instance_name, *device_names):
    """Register device with a SDPSubarray device server instance.

    If the device is already registered, do nothing.

    :param instance_name: Instance name SDPSubarray device server
    :param device_names: Subarray device names to register

    """
    # pylint: disable=protected-access
    try:
        tango_db = Database()
        class_name = 'SDPSubarray'
        server_name = '{}/{}'.format(class_name, instance_name)
        devices = list(tango_db.get_device_name(server_name, class_name))
        device_info = DbDevInfo()
        device_info._class = class_name
        device_info.server = server_name
        for device_name in device_names:
            device_info.name = device_name
            if device_name in devices:
                LOG.debug("Device '%s' already registered", device_name)
                continue
            LOG.info('Registering device: %s (server: %s, class: %s)',
                     device_info.name, server_name, class_name)
            tango_db.add_device(device_info)
    except ConnectionFailed:
        pass


def main(args=None, **kwargs):
    """Run server."""
    # Initialise logging
    log_level = tango.LogLevel.LOG_INFO
    if len(sys.argv) > 2 and '-v' in sys.argv[2]:
        log_level = tango.LogLevel.LOG_DEBUG
    tango_logging.init(device_name='SDPSubarray', level=log_level)

    # Set default values for feature toggles.
    SDPSubarray.set_feature_toggle_default(FeatureToggle.CONFIG_DB, False)
    SDPSubarray.set_feature_toggle_default(FeatureToggle.AUTO_REGISTER, True)
    SDPSubarray.set_feature_toggle_default(FeatureToggle.RECEIVE_ADDRESSES, False)

    # If the feature is enabled, attempt to auto-register the device
    # with the tango db.
    if SDPSubarray.is_feature_active(FeatureToggle.AUTO_REGISTER):
        if len(sys.argv) > 1:
            # delete_device_server('*')
            devices = ['mid_sdp/elt/subarray_{:d}'.format(i + 1)
                       for i in range(1)]
            register(sys.argv[1], *devices)

    return run((SDPSubarray,), args=args, **kwargs)


def terminate(_sig, _frame):
    """Terminate the program."""
    LOG.info('Asked to terminate')
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, terminate)
    main()
