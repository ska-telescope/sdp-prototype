# -*- coding: utf-8 -*-
"""Tango SDPSubarray device module."""
# pylint: disable=invalid-name,fixme

import json
import logging
import sys
from enum import IntEnum
from inspect import currentframe, getframeinfo
from math import ceil
from os.path import dirname, join

from jsonschema import exceptions, validate
from tango import AttrWriteType, AttributeProxy, ConnectionFailed, Database, \
    DbDevInfo, DebugIt, DevState, Except
from tango.server import Device, DeviceMeta, attribute, command, run

from ska_sdp_config import config as db_config, entity

# from skabase.SKASubarray import SKASubarray

LOG = logging.getLogger('ska.sdp.subarray_ds')


# https://pytango.readthedocs.io/en/stable/data_types.html#devenum-pythonic-usage
class AdminMode(IntEnum):
    """AdminMode enum."""

    OFFLINE = 0
    ONLINE = 1
    MAINTENANCE = 2
    NOT_FITTED = 3
    RESERVED = 4


class HealthState(IntEnum):
    """HealthState enum."""

    OK = 0
    DEGRADED = 1
    FAILED = 2
    UNKNOWN = 3


class ObsState(IntEnum):
    """ObsState enum."""

    IDLE = 0  #: Idle state
    CONFIGURING = 1  #: Configuring state
    READY = 2  #: Ready state
    SCANNING = 3  #: Scanning state
    PAUSED = 4  #: Paused state
    ABORTED = 5  #: Aborted state
    FAULT = 6  #: Fault state


# class SDPSubarray(SKASubarray):
class SDPSubarray(Device):
    """SDP Subarray device class.

    .. note::
        This should eventually inherit from SKASubarray but these need
        some work before doing so would add any value to this device.

    """

    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=too-many-instance-attributes

    __metaclass__ = DeviceMeta

    # -----------------
    # Device Properties
    # -----------------

    # version = device_property(dtype=str, default_value=VERSION)

    # ----------
    # Attributes
    # ----------

    obsState = attribute(dtype=ObsState, access=AttrWriteType.READ_WRITE)

    adminMode = attribute(dtype=AdminMode, access=AttrWriteType.READ_WRITE)

    healthState = attribute(dtype=HealthState,
                            doc='The health state reported for this device. '
                                'It interprets the current device condition '
                                'and condition of all managed devices to set '
                                'this. Most possibly an aggregate attribute.',
                            access=AttrWriteType.READ)

    receiveAddresses = attribute(dtype=str, access=AttrWriteType.READ)

    toggleReadCbfOutLink = attribute(dtype=bool,
                                     access=AttrWriteType.READ_WRITE,
                                     doc='Feature toggle to read '
                                         'the CSP CBF output link map when '
                                         'evaluating receiveAddresses.')

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        """Initialise the device."""
        # SKASubarray.init_device(self)
        Device.init_device(self)
        LOG.debug('Initialising SDP subarray device %s',
                  self.get_name())
        LOG.debug('XXX %s', sys.argv)
        self.set_state(DevState.OFF)
        self._obs_state = ObsState.IDLE
        self._admin_mode = AdminMode.OFFLINE
        self._health_state = HealthState.OK
        self.db_client = db_config.Config()
        self._pb_config = None   # PB config dictionary.
        self._channel_link_map = None  # CSP channel - FSP link map
        self._recv_hosts = None   # Map of receive hosts <-> channels
        self._recv_addresses = None  # receiveAddresses attribute dict
        self._toggle_read_cbf_out_link = True

    def always_executed_hook(self):
        """Run for on each call."""

    def delete_device(self):
        """Device destructor."""

    # ------------------
    # Attributes methods
    # ------------------

    def write_obsState(self, obs_state):
        """Set the obsState attribute.

        :param obs_state: An observation state enum value.
        """
        self._obs_state = obs_state

    def read_obsState(self):
        """Get the obsState attribute.

        :returns: The current obsState attribute value.
        """
        return self._obs_state

    def write_adminMode(self, admin_mode):
        """Set the adminMode attribute.

        :param admin_mode: An admin mode enum value.
        """
        self._admin_mode = admin_mode

    def read_adminMode(self):
        """Get the adminMode attribute.

        :return: The current adminMode attribute value.
        """
        return self._admin_mode

    def read_receiveAddresses(self):
        """Get the list of receive addresses encoded as a JSON string.

        More details are provided on SKA confluence at the address:
        http://bit.ly/2Gad55Q

        :return: JSON String describing receive addresses
        """
        return json.dumps(self._recv_addresses)

    def read_healthState(self):
        """Read Health State of the device.

        :return: Health State of the device
        """
        return self._health_state

    def write_toggleReadCbfOutLink(self, value):
        """Write value of feature toggle for the cbfOutLink behaviour.

        If true (default), the cbfOutLink CSP Subarray attribute is read when
        generating the receiveAddresses mapping.
        If false, the cbfOutLink attribute is not read and a dummy response is
        given when generating receiveAddresses

        :param value: Value of the toggle.
        :type value: bool

        """
        self._toggle_read_cbf_out_link = value

    def read_toggleReadCbfOutLink(self):
        """Read value of feature toggle for the cbfOutLink behaviour."""
        return self._toggle_read_cbf_out_link

    # --------
    # Commands
    # --------

    @command(dtype_in=str)
    @DebugIt()
    def AssignResources(self, config=''):
        """Assign Resources assigned to the subarray device.

        This is currently a noop for SDP!

        Following the description of the SKA subarray device model,
        resources can only be assigned to the subarray device when the
        obsState attribute is IDLE. Once resources are assigned to the
        subarray device, the device state transitions to ON.

        :param config: Resource specification (currently ignored)
        """
        # pylint: disable=unused-argument
        if self._obs_state != ObsState.IDLE:
            frame_info = getframeinfo(currentframe())
            Except.throw_exception(
                'Command: AssignReources failed',
                'AssignResources requires obsState == IDLE',
                '{}:{}'.format(frame_info.filename, frame_info.lineno))
        self.set_state(DevState.ON)

    @command(dtype_in=str)
    @DebugIt()
    def ReleaseResources(self, config=''):
        """Release resources assigned to the subarray device.

        This is currently a noop for SDP!

        Following the description of the SKA subarray device model,
        when all resources are released the device state should transition to
        OFF. Releasing resources is only allowed when the obsState is IDLE.

        :param config: Resource specification (currently ignored).
        """
        # pylint: disable=unused-argument
        if self._obs_state != ObsState.IDLE:
            frame_info = getframeinfo(currentframe())
            Except.throw_exception(
                'Command: ReleaseResources failed',
                'ReleaseResources requires obsState == IDLE',
                '{}:{}'.format(frame_info.filename, frame_info.lineno))

        self.set_state(DevState.OFF)

    @command(dtype_in=str)
    @DebugIt()
    def Configure(self, pb_config):
        """Configure the device to execute a real-time Processing Block (PB).

        Provides PB configuration and parameters needed to execute the first
        scan in the form of a JSON string.

        :param pb_config: JSON string wth Processing Block configuration.
        """
        LOG.info('Command: Configure (%s)', self.get_name())

        LOG.debug('Setting ObsState to CONFIGURING.')
        self._obs_state = ObsState.CONFIGURING

        LOG.debug('Validating PB configuration.')
        try:
            pb_config = json.loads(pb_config)
        except json.JSONDecodeError as error:
            LOG.error('Unable to load JSON PB configuration: %s', error.msg)
            raise
        schema_path = join(dirname(__file__), 'schema', 'configure_pb.json')
        with open(schema_path, 'r') as file:
            schema = json.loads(file.read())
        try:
            validate(pb_config, schema)
        except exceptions.ValidationError as error:
            LOG.error('PB configuration failed to validate: %s', error.message)
            frame_info = getframeinfo(currentframe())
            error_message = '{} : {} : {}'.format(
                str(error.absolute_path),
                str(error.schema_path),
                error.message
            )
            Except.throw_exception(
                'Command: Configure failed', error_message,
                '{}:{}'.format(frame_info.filename, frame_info.lineno))

        # Add the PB configuration to the database.
        for txn in self.db_client.txn():
            confdata = pb_config['configure']
            pb = entity.ProcessingBlock(confdata['id'], None,
                                        confdata['workflow'],
                                        confdata['parameters'],
                                        confdata['scanParameters'])
            txn.create_processing_block(pb)

        # Cache a local copy of the PB configuration.
        self._pb_config = pb_config['configure']

        # Evaluate the receive hosts <-> channel mapping.
        self._evaluate_receive_host_channel_map()

        # Evaluate the receive addresses.
        # NOTE(BMo) Depending on the deployment model this may need to be \
        # delayed until EE containers are started.
        self._evaluate_receive_addresses()

        LOG.debug('Setting ObsState to READY.')
        self._obs_state = ObsState.READY

        LOG.info('Command: Configure successful (%s)', self.get_name())

    @command(dtype_in=str)
    @DebugIt()
    def ConfigureScan(self, scan_config, schema_path=None):
        """Configure the subarray device to execute a scan.

        This allows scan specific, late-binding information to be provided
        to the configured PB workflow.

        :param scan_config: JSON Scan configuration.
        :param schema_path: Path to the Scan config schema (optional).
        """
        LOG.debug('Setting ObsState to CONFIGURING.')
        self._obs_state = ObsState.CONFIGURING

        # # Validate the SBI config schema
        if schema_path is None:
            schema_path = join(dirname(__file__), 'schema',
                               'configure_scan.json')
        with open(schema_path, 'r') as file:
            schema = json.loads(file.read())
        pb_config = json.loads(scan_config)
        validate(pb_config, schema)

        # Update receive addresses (if required) for the new scan configuration
        # self._update_receive_addresses()

        LOG.debug('Setting ObsState to READY.')
        self._obs_state = ObsState.READY

    @command
    @DebugIt()
    def StartScan(self):
        """Command issued when a scan is started."""
        self._obs_state = ObsState.SCANNING

    @command
    @DebugIt()
    def EndScan(self):
        """Command issued when the scan is ended."""
        self._obs_state = ObsState.READY

    @command
    @DebugIt()
    def EndSB(self):
        """Command issued to end the scheduling block."""
        self._obs_state = ObsState.IDLE

    def _scan_complete(self):
        """Update the obsState to READY when a scan is complete.

        Internal state transition.

        """
        self._obs_state = ObsState.READY

    def _evaluate_receive_host_channel_map(self):
        """Evaluate channel map for receive hosts.

        NOTE(BMo) This is a placeholder function and will need completely
                  reworking at some point!

        This function should generate a map of receive hosts to
        channels. This will eventually need to depend on the deployment
        of the receive EE processes.

        At the moment the PB config parameters for the vis_ingest
        example are not sufficient to do this property.

        """
        if self._pb_config['workflow']['id'] != 'vis_ingest':
            return

        LOG.debug('Evaluating receive host channel map.')
        self._recv_hosts = list()

        # FIXME(BMo) Validate against expected PB parameters!

        pb_params = self._pb_config['parameters']
        num_channels = pb_params['numChannels']

        # FIXME(BMo) parameter does not yet exist... default is always used!
        max_channels_per_host = pb_params.get('maxChannelsPerHost', 400)
        num_hosts = ceil(num_channels / max_channels_per_host)

        LOG.debug('No. channels: %d', num_channels)
        LOG.debug('Max channels per host: %d', max_channels_per_host)
        LOG.debug('No. hosts: %d', num_hosts)

        # FIXME(BMo) complete hack until we have a way of getting actual
        #            receive hosts!
        for host_index in range(num_hosts):
            host_ip = '192.168.{}.{}'.format(
                host_index//256,
                host_index - ((host_index//256) * 256) + 1)
            host_num_channels = min(
                num_channels - (max_channels_per_host * host_index),
                max_channels_per_host)
            # Note(BMo): Assume that a host does not care about which channels
            #            it processes only a number (for now)...
            #            this is almost certainly a bad assumption.
            host = dict(ip=host_ip,
                        num_channels=host_num_channels)
            LOG.debug('Host: %s', host)
            self._recv_hosts.append(host)

    def _update_host_recv_map(self, channels):
        """Update the host receive map with channel link information.

        :param channels: Map (list of dicts) of channels <-> FSPs derived
                         from the CSP channel link map.

        """
        channel_start = 0
        for host in self._recv_hosts:
            channel_end = channel_start + host['num_channels']
            host_channel_ids = [channel['id'] for channel
                                in channels[channel_start:channel_end]]
            host_channel_fsp_ids = [channel['fspID'] for channel
                                    in channels[channel_start:channel_end]]
            host_channel_fsp_ids = list(set(host_channel_fsp_ids))
            host_channels = channels[channel_start:channel_end]
            host['num_channels'] = len(host_channels)
            host['channels'] = host_channels
            host['channel_ids'] = host_channel_ids
            host['fsp_ids'] = host_channel_fsp_ids
            channel_start += host['num_channels']
        # LOG.debug('RECV HOSTS:\n%s', json.dumps(self._recv_hosts, indent=2))

    def _evaluate_channels_fsp_map(self, channel_link_map):
        """Evaluate a map of channels <-> FSPs.

        This is used as an intermediate data structure for generating
        receiveAddresses.

        :param channel_link_map: Channel link map (from CSP)

        :returns: map of channels to FSPs

        """
        # Build map of channels <-> FSP's
        channels = list()
        for fsp in channel_link_map['fsp']:
            for link in fsp['cbfOutLink']:
                for channel in link['channel']:
                    channel = dict(id=channel['chanID'], bw=channel['bw'],
                                   cf=channel['cf'], fspID=fsp['fspID'],
                                   linkID=link['linkID'])
                    channels.append(channel)

        # Sort the channels by Id and fspID
        channels = sorted(channels, key=lambda key: key['id'])
        channels = sorted(channels, key=lambda key: key['fspID'])

        # The number of channels in the channel link map should be <= number
        # of channels in the receive parameters.
        pb_params = self._pb_config['parameters']
        pb_num_channels = pb_params['numChannels']
        if len(channels) > pb_num_channels:
            raise ValueError('Vis Receive configured for fewer channels than'
                             'defined in the CSP channel link map! '
                             '(link map: {}, workflow: {})'
                             .format(len(channels), pb_num_channels))
        if len(channels) < pb_num_channels:
            LOG.warning('Vis receive workflow configured for more channels '
                        'than defined in the CSP channel link map! '
                        '(link map: %d, workflow: %d)',
                        len(channels), pb_num_channels)
        return channels

    def _evaluate_receive_addresses(self):
        """Evaluate receive addresses map.

        Expected to be called by Configure when first evaluating the
        receiveAddress map.

        This would be very easy if the channel link map metadata matched
        that of / was reflected in the receive workflow parameters!

        NOTE(BMo) This is a placeholder function and will need completely
                  reworking at some point!

        """
        # pylint: disable=too-many-locals
        if self._pb_config['workflow']['id'] != 'vis_ingest':
            return

        if not self._toggle_read_cbf_out_link:
            self._recv_addresses = \
                dict(scanId=12345, receiveAddresses=[
                    dict(fspId=1, hosts=[])])
            return

        LOG.debug('Evaluating receive addresses.')

        channel_link_map, channels = self._get_channel_link_map()
        LOG.debug('Obtained channel link map from CSP')

        fsp_ids = list({channel['fspID'] for channel in channels})
        LOG.debug('Channel link map active FSP IDs: %s', fsp_ids)

        LOG.debug('Parsing channel link map for scan: %d',
                  channel_link_map['scanID'])
        LOG.debug('%s', self._pb_config['scanParameters'])
        configured_scans = [int(scan_id)
                            for scan_id in
                            self._pb_config['scanParameters'].keys()]
        LOG.debug('Configured scans: %s', configured_scans)

        if channel_link_map['scanID'] not in configured_scans:
            LOG.error('Unknown scanID. Channel Link map scan ')
            raise RuntimeError('Unknown Scan ID')

        # Build channel map for each host.
        self._update_host_recv_map(channels)

        # Create receive address + channels <-> FSP map
        recv_addr = dict(scanId=channel_link_map['scanID'],
                         totalChannels=len(channels),
                         receiveAddresses=list())
        # Create (empty) top level FSP mapping
        for fsp_id in fsp_ids:
            recv_addr['receiveAddresses'].append(
                dict(phaseBinId=0, fspId=fsp_id, hosts=list()))

        # Create (empty) host map for each FSP.
        for host in self._recv_hosts:
            for fsp_id in host['fsp_ids']:
                fsp_addrs = next(item for item
                                 in recv_addr['receiveAddresses']
                                 if item['fspId'] == fsp_id)
                fsp_addrs['hosts'].append(dict(host=host['ip'],
                                               channels=list()))

        # LOG.debug('Recv. addresses\n%s', json.dumps(recv_addr, indent=2))

        pb_params = self._pb_config['parameters']
        chan_ave_factor = pb_params.get('channelAveragingFactor', 1)
        recv_port_offset = pb_params.get('portOffset', 9000)

        # Loop over hosts and add channels to each host up to the number
        # of channels allocatable to each host.
        for host in self._recv_hosts:
            host_ip = host['ip']

            for channel in host['channels']:
                fsp_id = channel.get('fspID')
                channel_id = channel.get('id')
                LOG.debug('Adding channel: %d (fsp id: %d link id: %d) to '
                          'receive addresses map.',
                          channel_id, fsp_id, channel.get('linkID'))
                fsp_addrs = next(item for item
                                 in recv_addr['receiveAddresses']
                                 if item['fspId'] == fsp_id)
                if not fsp_addrs['hosts']:
                    fsp_addrs['hosts'].append(dict(host=host_ip,
                                                   channels=list()))

                # LOG.debug('\n%s', json.dumps(recv_addr, indent=2))
                host_config = next(item for item in fsp_addrs['hosts']
                                   if item['host'] == host_ip)

                # Find out if this channel can be added to a channel block
                # ie. if it belongs to an existing list with stride
                #     chan_ave_factor
                # if so, update the channel block.
                channel_config = None
                for host_channels in host_config['channels']:
                    start_chan = host_channels['startChannel']
                    next_chan = (start_chan +
                                 host_channels['numChannels'] *
                                 chan_ave_factor)
                    if next_chan == channel_id:
                        LOG.debug('Channel %d added to existing block with '
                                  'channel start id %d', channel_id,
                                  start_chan)
                        channel_config = next(item for item
                                              in host_config['channels']
                                              if item['startChannel'] ==
                                              start_chan)
                        channel_config['numChannels'] += 1

                # Otherwise, start a new channel block.
                if channel_config is None:
                    start_channel = channel_id
                    port_offset = recv_port_offset + channel_id
                    num_channels = 1
                    channel_config = dict(portOffset=port_offset,
                                          startChannel=start_channel,
                                          numChannels=num_channels)
                    host_config['channels'].append(channel_config)

        # LOG.debug('Recv. addresses\n%s', json.dumps(recv_addr, indent=2))

        self._recv_addresses = recv_addr

    def _update_receive_addresses(self):
        """Update receive addresses map (private method).

        Expected to be called by ConfigureScan when there is a new
        channel link map from CSP.

        NOTE(BMo) This is a placeholder function and will need completely
          reworking at some point!

        """
        raise NotImplementedError()

    def _read_channel_link_map(self):
        """Get the channel link map from the CSP subarray device.

        :return: Channel link map string as read from CSP.

        """
        # Obtain the FQDN of the CSP cbfOutLink attribute address from the
        # PB configuration.
        attr_name = self._pb_config.get('cspCbfOutlinkAddress', None)
        if attr_name is None:
            error_str = "'cspCbfOutlinkAddress' not found in PB configuration"
            LOG.error(error_str)
            raise RuntimeError(error_str)
        LOG.debug('Reading cbfOutLink from: %s', attr_name)
        attr = AttributeProxy(attr_name)
        channel_link_map = attr.read()
        return channel_link_map

    def _get_channel_link_map(self):
        """Get and validate the channel link map (from CSP).

        :return: CSP Channel - FSP link map dictionary.

        """
        channel_link_map_str = self._read_channel_link_map()

        LOG.debug('Validating cbfOutLink (CSP channel-link-map).')

        # Convert string to dictionary.
        try:
            channel_link_map = json.loads(channel_link_map_str)
        except json.JSONDecodeError as error:
            LOG.error('Channel link map JSON load error: %s '
                      '(line %s, column: %s)', error.msg, error.lineno,
                      error.colno)
            raise

        # Validate schema.
        schema_path = join(dirname(__file__), 'schema', 'channel-links.json')
        with open(schema_path, 'r') as file:
            schema = json.loads(file.read())
        try:
            validate(channel_link_map, schema)
        except exceptions.ValidationError as error:
            LOG.error('Channel link map failed to validate: %s (%s)',
                      error.message, error.schema_path)
            frame_info = getframeinfo(currentframe())
            error_message = '{} : {} : {}'.format(
                str(error.absolute_path),
                str(error.schema_path),
                error.message
            )
            Except.throw_exception(
                'Invalid channel link map schema! {}'.format(error_message),
                error_message, '{}:{}'.format(frame_info.filename,
                                              frame_info.lineno))

        # Build map of channels <-> FSP's
        channels = self._evaluate_channels_fsp_map(channel_link_map)

        return channel_link_map, channels


def delete_device_server(instance_name="*"):
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
    try:
        tango_db = Database()
        class_name = 'SDPSubarray'
        server_name = '{}/{}'.format(class_name, instance_name)
        devices = list(tango_db.get_device_name(server_name, class_name))
        device_info = DbDevInfo()
        # pylint: disable=protected-access
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


def init_logger(level='DEBUG', name='ska.sdp'):
    """Initialise stdout logger for the ska.sdp logger.

    :param level: Logging level, default: 'DEBUG'
    :param name: Logger name to initialise. default: 'ska.sdp'.

    """
    log = logging.getLogger(name)
    log.propagate = False
    # make sure there are no duplicate handlers.
    for handler in log.handlers:
        log.removeHandler(handler)
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-6s | %(message)s')
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(level)


def main(args=None, **kwargs):
    """Run server."""
    log_level = 'INFO'
    if len(sys.argv) > 2 and '-v' in sys.argv[2]:
        log_level = 'DEBUG'
    init_logger(log_level)
    if len(sys.argv) > 1:
        # delete_device_server("*")
        devices = ['mid_sdp/elt/subarray_{:d}'.format(i+1) for i in range(1)]
        register(sys.argv[1], *devices)
    return run((SDPSubarray,), args=args, **kwargs)


if __name__ == '__main__':
    main()
