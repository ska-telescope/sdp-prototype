# -*- coding: utf-8 -*-
"""Tango SDPSubarray device module."""
# pylint: disable=invalid-name
# pylint: disable=too-many-lines
# pylint: disable=wrong-import-position
# pylint: disable=too-many-public-methods
# pylint: disable=fixme

import os
import sys
import time
import signal
import logging
import json
from enum import IntEnum, unique
import jsonschema

# Use LMC base classes and thus SKA logging
from ska.base import SKASubarray
from ska.base.control_model import AdminMode, ObsState, HealthState

import tango
from tango import AttrWriteType, AttributeProxy, ConnectionFailed, Database, \
    DbDevInfo, DevState
from tango.server import attribute, command, \
    device_property, run

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from release import VERSION as SERVER_VERSION  # noqa

try:
    import ska_sdp_config
except ImportError:
    ska_sdp_config = None

LOG = logging.getLogger()


@unique
class FeatureToggle(IntEnum):
    """Feature Toggles."""

    CONFIG_DB = 1  #: Enable / Disable the Config DB
    CBF_OUTPUT_LINK = 2  #: Enable / Disable use of of the CBF OUTPUT LINK
    AUTO_REGISTER = 3  #: Enable / Disable tango db auto-registration


class SDPSubarray(SKASubarray):
    """SDP Subarray device class.

    .. note::
        Inherits from SKASubArray - and thus will use ska_logging

    """

    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=no-self-use

    # __metaclass__ = DeviceMeta

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
        access=AttrWriteType.READ_WRITE,
        doc='The device obs state.'
    )

    healthState = attribute(
        label='Health state',
        dtype=HealthState,
        access=AttrWriteType.READ,
        doc='The health state reported for this device.',
        polling_period=1000
    )

    receiveAddresses = attribute(
        label='Receive Addresses',
        dtype=str,
        access=AttrWriteType.READ,
        doc='Host addresses for the visibility receive workflow as a '
            'JSON string.',
        polling_period=1000
    )

    processingBlockState = attribute(
        label='State of real-time processing blocks',
        dtype=str,
        access=AttrWriteType.READ,
        doc='Processing block states for real-time workflows as a '
            'JSON string.',
        polling_period=5000
    )

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        """Initialise the device."""
        # Device.init_device(self)
        super().init_device()

        # self.write_loggingLevel(LoggingLevel.DEBUG)
        # LOG.setLevel(logging.DEBUG)
        self.set_state(DevState.INIT)
        LOG.info('Initialising SDP Subarray: %s', self.get_name())

        # Initialise attributes
        self._set_obs_state(ObsState.IDLE)
        self._set_admin_mode(AdminMode.ONLINE)
        self._set_health_state(HealthState.OK)
        self._set_receive_addresses(None)

        # Initialise instance variables
        self._sbi_id = None
        self._cbf_outlink_address = None

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

        if self.is_feature_active(FeatureToggle.CBF_OUTPUT_LINK):
            LOG.debug('CBF output link enabled')
        else:
            LOG.debug('CBF output link disabled')

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
                    pb_state['id'] = pb_id
                    pb_state_list.append(pb_state)

        return json.dumps(pb_state_list)

    def write_obsState(self, obs_state):
        """Set the obsState attribute.

        :param obs_state: An observation state enum value.

        """
        self._set_obs_state(obs_state)

    def write_adminMode(self, admin_mode):
        """Set the adminMode attribute.

        :param admin_mode: An admin mode enum value.

        """
        # pylint: disable=arguments-differ
        self._set_admin_mode(admin_mode)

    # --------
    # Commands
    # --------

    @command(dtype_in=str, doc_in='Resource configuration JSON string')
    def AssignResources(self, config=''):
        """Assign resources to the subarray.

        This is currently a noop for SDP!

        Following the description of the SKA subarray device model,
        resources can only be assigned to the subarray device when the
        obsState attribute is IDLE. Once resources are assigned to the
        subarray device, the device state transitions to ON.

        :param config: Resource specification (currently ignored)

        """
        # pylint: disable=unused-argument
        # pylint: disable=arguments-differ
        # FIXME Look more at these issues
        LOG.info('-------------------------------------------------------')
        LOG.info('AssignResources (%s)', self.get_name())
        LOG.info('AssignResources - currently a NOOP for SDP')
        LOG.info('-------------------------------------------------------')
        self._require_obs_state([ObsState.IDLE])
        self._require_admin_mode([AdminMode.ONLINE, AdminMode.MAINTENANCE,
                                  AdminMode.RESERVED])
        LOG.warning('Assigning resources - calling SKASubarray')
        super().AssignResources(config)
    #   LOG.debug('Setting device state to ON') In SKASubarray?
    #   self.set_state(DevState.ON)
        LOG.info('-------------------------------------------------------')
        LOG.info('AssignResources Successful!')
        LOG.info('-------------------------------------------------------')

    @command(dtype_in=str, doc_in='Resource configuration JSON string')
    def ReleaseResources(self, config=''):
        """Release resources assigned to the subarray.

        This is currently a noop for SDP!

        Following the description of the SKA subarray device model,
        when all resources are released the device state should transition to
        OFF. Releasing resources is only allowed when the obsState is IDLE.

        :param config: Resource specification (currently ignored).

        """
        # pylint: disable=arguments-differ
        # pylint: disable=unused-argument
        # FIXME: Look more at these issues
        LOG.info('-------------------------------------------------------')
        LOG.info('ReleaseResources (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')
        self._require_obs_state([ObsState.IDLE])
        self._require_admin_mode([AdminMode.OFFLINE, AdminMode.NOT_FITTED],
                                 invert=True)
        LOG.warning('Release resources is currently a no-op!')
        LOG.warning('Release resources - calling SKASubarray')
        super().AssignResources(config)
        LOG.debug('Setting device state to OFF')
        self.set_state(DevState.OFF)
        # FIXME: Should this be handled by SKASubarray?
        LOG.info('-------------------------------------------------------')
        LOG.info('ReleaseResources Successful!')
        LOG.info('-------------------------------------------------------')

    @command(dtype_in=str, doc_in='Processing block configuration JSON string')
    def Configure(self, config_str):
        """Configure processing associated with this subarray.

        This is achieved by providing a JSON string containing an array of
        processing block definitions that specify the workflows to
        execute and their parameters. The workflows may be real-time or
        batch.

        :param config_str: Processing block configuration JSON string.

        """
        LOG.info('-------------------------------------------------------')
        LOG.info('Configure (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Check obsState is IDLE, and set to CONFIGURING
        self._require_obs_state([ObsState.IDLE])
        self._set_obs_state(ObsState.CONFIGURING)

        # self.set_state(DevState.ON)

        # Validate the JSON configuration string
        config = self._validate_json_config(config_str, 'configure.json')

        if config is None:
            # Validation has failed, so set obsState back to IDLE and raise
            # an error
            self._set_obs_state(ObsState.IDLE)
            self._raise_command_error('Configuration validation failed')
            return

        # Create the scheduling block and processing blocks in the config DB
        self._create_processing_blocks(config)

        # Set the receive addresses for the first scan
        scan_id = config.get('scanId')
        receive_addresses = self._get_receive_addresses(scan_id)
        self._set_receive_addresses(receive_addresses)

        # Set SB status to READY
        self._update_sb_status('READY')

        # Set the obsState to READY
        self._set_obs_state(ObsState.READY)

        LOG.info('-------------------------------------------------------')
        LOG.info('Configure successful!')
        LOG.info('-------------------------------------------------------')

    @command(dtype_in=str, doc_in='Scan configuration JSON string')
    def ConfigureScan(self, config_str):
        """Configure the subarray device to execute a scan.

        This allows scan specific, late-binding information to be provided
        to the configured real-time workflows.

        ConfigureScan is only allowed in the READY obsState and should
        leave the Subarray device in the READY obsState when configuring
        is complete. While Configuring the Scan the obsState is set to
        CONFIGURING.

        :param config_str: Scan configuration JSON string.

        """
        LOG.info('-------------------------------------------------------')
        LOG.info('ConfigureScan (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Check the obsState is READY and set to CONFIGURING
        self._require_obs_state([ObsState.READY])
        self._set_obs_state(ObsState.CONFIGURING)

        # Validate JSON configuration string
        config = self._validate_json_config(config_str, 'configure_scan.json')

        if config is None:
            # Validation has failed, so set obsState back to READY and raise
            # an error.
            self._set_obs_state(ObsState.READY)
            self._raise_command_error('Configuration validation failed')
            return

        # Update scan parameters
        self._update_scan_parameters(config)

        # Set the receive addresses for the next scan
        scan_id = config.get('scanId')
        receive_addresses = self._get_receive_addresses(scan_id)
        self._set_receive_addresses(receive_addresses)

        # Set the obsState to READY
        self._set_obs_state(ObsState.READY)

        LOG.info('-------------------------------------------------------')
        LOG.info('ConfigureScan Successful!')
        LOG.info('-------------------------------------------------------')

    @command
    def Scan(self):
        """Command issued to start scan."""
        # pylint: disable=arguments-differ
        # FIXME Look more at these issues
        LOG.info('-------------------------------------------------------')
        LOG.info('Scan (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Check obsState is READY
        self._require_obs_state([ObsState.READY])

        # Set SB status to SCANNING
        self._update_sb_status('SCANNING')

        # Set obsState to SCANNING
        self._set_obs_state(ObsState.SCANNING)

        LOG.info('-------------------------------------------------------')
        LOG.info('Scan Successful')
        LOG.info('-------------------------------------------------------')

    @command
    def EndScan(self):
        """Command issued to end scan."""
        LOG.info('-------------------------------------------------------')
        LOG.info('EndScan (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Check obsState is SCANNING
        self._require_obs_state([ObsState.SCANNING])

        # Clear receiveAddresses
        self._set_receive_addresses(None)

        # Set SB status to READY
        self._update_sb_status('READY')

        # Set obsState to READY
        self._set_obs_state(ObsState.READY)

        LOG.info('-------------------------------------------------------')
        LOG.info('EndScan Successful')
        LOG.info('-------------------------------------------------------')

    @command
    def EndSB(self):
        """Command issued to end the scheduling block."""
        LOG.info('-------------------------------------------------------')
        LOG.info('EndSB (%s)', self.get_name())
        LOG.info('-------------------------------------------------------')

        # Check obsState is READY
        self._require_obs_state([ObsState.READY])

        # Set SB status to FINISHED
        self._update_sb_status('FINISHED')

        # End the real-time processing associated with this subarray
        self._end_realtime_processing()

        # Set obsState to IDLE
        self._set_obs_state(ObsState.IDLE)

        LOG.info('-------------------------------------------------------')
        LOG.info('EndSB Successful')
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

    def _require_obs_state(self, allowed_states, invert=False):
        """Require specified obsState values.

        Checks if the current obsState matches the specified allowed values.

        If invert is False (default), throw an exception if the obsState
        is not in the list of specified states.

        If invert is True, throw an exception if the obsState is NOT in the
        list of specified allowed states.

        :param allowed_states: List of allowed obsState values
        :param invert: If True require that the obsState is not in one of
                       specified allowed states

        """
        # Fail if obsState is NOT in one of the allowed_obs_states
        if not invert and self._obs_state not in allowed_states:
            self._set_obs_state(ObsState.FAULT)
            msg = 'obsState ({}) must be in {}'.format(
                self._obs_state, allowed_states)
            self._raise_command_error(msg)

        # Fail if obsState is in one of the allowed_obs_states
        if invert and self._obs_state in allowed_states:
            self._set_obs_state(ObsState.FAULT)
            msg = 'The device must NOT be in one of the ' \
                  'following obsState values: {}'.format(allowed_states)
            self._raise_command_error(msg)

    def _require_admin_mode(self, allowed_modes, invert=False):
        """Require specified adminMode values.

        Checks if the current adminMode matches the specified allowed values.

        If invert is False (default), throw an exception if not in the list
        of specified states / modes.

        If invert is True, throw an exception if the adminMode is NOT in the
        list of specified allowed states.

        :param allowed_modes: List of allowed adminMode values
        :param invert: If True require that the adminMode is not in one of
                       specified allowed states

        """
        # Fail if adminMode is NOT in one of the allowed_modes
        if not invert and self._admin_mode not in allowed_modes:
            msg = 'adminMode ({}) must be in: {}'.format(
                repr(self._admin_mode), allowed_modes)
            LOG.error(msg)
            self._raise_command_error(msg)

        # Fail if obsState is in one of the allowed_obs_states
        if invert and self._admin_mode in allowed_modes:
            msg = 'adminMode ({}) must NOT be in: {}'.format(
                repr(self._admin_mode), allowed_modes)
            LOG.error(msg)
            self._raise_command_error(msg)

    def _raise_command_error(self, desc, origin=''):
        """Raise a command error.

        :param desc: Error message / description.
        :param origin: Error origin (optional).

        """
        self._raise_error(desc, reason='Command error', origin=origin)

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

    def _create_processing_blocks(self, config):
        """Create the SB and PBs in the config DB.

        :param config: dict containing configuration data

        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # Log IDs found in configuration
        sbi_id = config.get('sbiId')
        scan_id = config.get('scanId')
        pb_ids = [pb.get('id') for pb in config.get('processingBlocks')]
        LOG.info('Scheduling block instance %s', sbi_id)
        LOG.info('Processing blocks %s', pb_ids)
        LOG.info('Scan %s', scan_id)

        # Get lists of existing scheduling blocks and processing blocks
        if self._config_db_client is not None:
            for txn in self._config_db_client.txn():
                existing_sb_ids = txn.list_scheduling_blocks()
                existing_pb_ids = txn.list_processing_blocks()
        else:
            existing_sb_ids = []
            existing_pb_ids = []

        # Check for duplicate IDs
        error = False
        if sbi_id in existing_sb_ids:
            error = True
            LOG.error('Scheduling block instance %s already exists', sbi_id)
        pb_dup = [pb_id for pb_id in pb_ids if pb_id in existing_pb_ids]
        if pb_dup != []:
            error = True
            for pb_id in pb_dup:
                LOG.error('Processing block %s already exists', pb_id)
        if error:
            self._set_obs_state(ObsState.READY)
            self._raise_command_error(
                'Duplicate scheduling block instance ID or processing block'
                ' ID in configuration'
            )
            return

        self._sbi_id = sbi_id

        # Scheduling block.

        sb = {
            'scan_id': scan_id,
            'pb_realtime': [],
            'pb_batch': [],
            'pb_receive_addresses': None
        }

        # Loop over the processing block configurations.

        processing_blocks = []
        cbf_outlink_address = None

        for pbc in config.get('processingBlocks'):
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

            if 'cspCbfOutlinkAddress' in pbc:
                if wf_type == 'batch':
                    LOG.error('cspCbfOutlinkAddress attribute must not '
                              'appear in batch processing block '
                              'configuration')
                elif sb['pb_receive_addresses'] is not None:
                    LOG.error('cspCbfOutlinkAddress attribute must not '
                              'appear in more than one real-time processing '
                              'block configuration')
                else:
                    cbf_outlink_address = pbc.get('cspCbfOutlinkAddress')
                    sb['pb_receive_addresses'] = pb_id

            if 'scanParameters' in pbc:
                if wf_type == 'realtime':
                    scan_parameters = pbc.get('scanParameters')
                elif wf_type == 'batch':
                    LOG.error('scanParameters attribute must not appear '
                              'in batch processing block configuration')
                    scan_parameters = {}
            else:
                scan_parameters = {}

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
            processing_blocks.append(
                ska_sdp_config.ProcessingBlock(
                    pb_id=pb_id,
                    sbi_id=sbi_id,
                    workflow=workflow,
                    parameters=pbc.get('parameters'),
                    scan_parameters=scan_parameters,
                    dependencies=dependencies
                )
            )

        # Create scheduling block and processing blocks in the config DB.
        # This is done in a single transaction.
        if self._config_db_client is not None:
            for txn in self._config_db_client.txn():
                txn.create_scheduling_block(sbi_id, sb)
                for pb in processing_blocks:
                    pb_id = pb.pb_id
                    txn.create_processing_block(pb)
                    txn.create_processing_block_state(pb_id, {})

        if self.is_feature_active(FeatureToggle.CBF_OUTPUT_LINK) \
                and self._config_db_client is not None:
            self._cbf_outlink_address = cbf_outlink_address

    def _update_scan_parameters(self, config):
        """Update scan parameters in the SB and real-time PBs.

        :param config: dict containing configuration data

        """
        scan_id = config.get('scanId')
        LOG.info('Scan: %s', scan_id)

        if self._config_db_client is not None:
            for txn in self._config_db_client.txn():

                sb = txn.get_scheduling_block(self._sbi_id)
                pb_realtime = sb.get('pb_realtime')

                for pbc in config.get('processingBlocks'):
                    pb_id = pbc.get('id')
                    if pb_id not in pb_realtime:
                        LOG.error('Processing block %s is not a real-time PB '
                                  'associated with this subarray', pb_id)
                        continue
                    LOG.info('Updating scan parameters in processing block '
                             '%s', pb_id)
                    pb_old = txn.get_processing_block(pb_id)
                    pb_new = ska_sdp_config.ProcessingBlock(
                        pb_id=pb_old.pb_id,
                        sbi_id=pb_old.sbi_id,
                        workflow=pb_old.workflow,
                        parameters=pb_old.parameters,
                        scan_parameters=pbc.get('scanParameters')
                    )
                    txn.update_processing_block(pb_new)

                sb['scan_id'] = scan_id
                txn.update_scheduling_block(self._sbi_id, sb)

    def _get_receive_addresses(self, scan_id):
        """Get the receive addresses for the next scan.

         The channel link map is read from the CSP device attribute and
         passed to the workflow that was configured to provide the receive
         addresses. The workflow responds by generating the addresses.
         This communication happens via the processing block state.

        :param scan_id: scan ID for which to get receive addresses
        :returns: receive address as dict

        """
        if self._cbf_outlink_address is None \
                or self._config_db_client is None:
            return None

        # Get ID of PB that is generating the receive addresses
        for txn in self._config_db_client.txn():
            sb = txn.get_scheduling_block(self._sbi_id)
        pb_id = sb.get('pb_receive_addresses')

        # Get channel link map with the same scan ID from CSP device
        channel_link_map = self._get_channel_link_map(scan_id)

        # Update channel link map in the PB state
        for txn in self._config_db_client.txn():
            pb_state = txn.get_processing_block_state(pb_id)
            pb_state['channel_link_map'] = channel_link_map
            txn.update_processing_block_state(pb_id, pb_state)

        # Wait for receive addresses with same scan ID to be available in the
        # PB state
        for txn in self._config_db_client.txn():
            pb_state = txn.get_processing_block_state(pb_id)
            receive_addresses = pb_state.get('receive_addresses')
            if receive_addresses is None:
                ra_scan_id = None
            else:
                ra_scan_id = receive_addresses.get('scanId')
            if ra_scan_id != scan_id:
                txn.loop(wait=True)

        return receive_addresses

    def _get_channel_link_map(self, scan_id, timeout=30.0):
        """Get channel link map from the CSP Tango device attribute.

        :param scan_id: Scan ID to match
        :param timeout: Timeout in seconds
        :returns: Validated channel link map as dict

        """
        LOG.debug('Reading channel link map from %s',
                  self._cbf_outlink_address)
        attribute_proxy = AttributeProxy(self._cbf_outlink_address)
        attribute_proxy.ping()

        LOG.debug('Waiting for CSP attribute to provide channel link map for '
                  'scan ID %s', scan_id)
        # This is a horrendous hack to poll the CSP device until the scan
        # ID matches. It needs to refactored to use events.
        start_time = time.time()
        while True:
            channel_link_map_str = attribute_proxy.read().value
            channel_link_map = self._validate_json_config(
                channel_link_map_str, 'channel_link_map.json')
            if channel_link_map is None:
                self._set_obs_state(ObsState.FAULT)
                self._raise_command_error('Channel link map validation '
                                          'failed')
                break
            if channel_link_map.get('scanID') == scan_id:
                break
            elapsed = time.time() - start_time
            LOG.debug('Waiting for scan ID on CSP attribute '
                      '(elapsed: %2.4f s)', elapsed)
            if elapsed > timeout:
                self._set_obs_state(ObsState.FAULT)
                self._raise_command_error('Timeout reached while waiting for '
                                          'scan ID on CSP attribute')
                channel_link_map = None
                break
            time.sleep(1.0)

        return channel_link_map

    def _end_realtime_processing(self):
        """End real-time processing associated with this subarray.

        This resets the internal state of the subarray.
        """
        self._sbi_id = None
        self._cbf_outlink_address = None

    def _update_sb_status(self, status):
        """Update scheduling block status field.

        :param status: status
        """
        if self._config_db_client is not None:
            for txn in self._config_db_client.txn():
                sb = txn.get_scheduling_block(self._sbi_id)
                sb['status'] = status
                txn.update_scheduling_block(self._sbi_id, sb)


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
    # log_level = tango.LogLevel.LOG_INFO
    # if len(sys.argv) > 2 and '-v' in sys.argv[2]:
    #     log_level = tango.LogLevel.LOG_DEBUG
    # tango_logging.init(device_name='SDPSubarray', level=log_level)

    # Set default values for feature toggles.
    SDPSubarray.set_feature_toggle_default(FeatureToggle.CONFIG_DB, False)
    SDPSubarray.set_feature_toggle_default(FeatureToggle.CBF_OUTPUT_LINK,
                                           False)
    SDPSubarray.set_feature_toggle_default(FeatureToggle.AUTO_REGISTER, True)

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
