"""
Workflow to test generation of receive addresses.

The purpose of this workflow is to test the mechanism for generating SDP
receive addresses from the channel link map published by CSP. The subarray
device reads the channel link map from an attribute on the CSP subarray device
and writes it to the processing block state. The workflow picks it up from
there, uses it to generate the receive addresses, and writes them to the PB
state. The subarray device picks the addresses from there and publishes them
on the appropriate attribute.

This workflow does not generate any deployments.
"""

import sys
import logging
import signal
import ska_sdp_config

logging.basicConfig()
LOG = logging.getLogger('test_receive_addresses')
LOG.setLevel(logging.DEBUG)


def channel_list(channel_link_map):
    """
    Generate flat list of channels from the channel link map.

    :param channel_link_map: channel link map.
    :returns: list of channels, sorted by channel ID.
    """
    channels = []
    for fsp in channel_link_map['fsp']:
        for link in fsp['cbfOutLink']:
            for channel in link['channel']:
                channel = dict(
                    chan_id=channel['chanID'],
                    bw=channel['bw'],
                    cf=channel['cf'],
                    fsp_id=fsp['fspID'],
                    link_id=link['linkID'],
                )
                channels.append(channel)

    # Sort by channel ID.
    channels = sorted(channels, key=lambda chan: chan['chan_id'])

    return channels

def minimal_receive_addresses(scan_id, channels):
    """
    Provide a minimal version of the receive addresses.

    :param scan_id: the scan ID
    :param channels: list of channels
    :returns: receive addresses
    """
    # Get first channel and number of channels for each FSP.
    fsp = {}
    for chan in channels:
        chan_id = chan['chan_id']
        fsp_id = chan['fsp_id']
        if fsp_id not in fsp:
            fsp[fsp_id] = (chan_id, 1)
        else:
            fstchan, numchan = fsp[fsp_id]
            fstchan = min(fstchan, chan_id)
            numchan += 1
            fsp[fsp_id] = (fstchan, numchan)

    # Total number of channels.
    totchan = sum(f[1] for f in fsp.values())

    # Construct receive addresses.
    ralist = []
    for fsp_id, (fstchan, numchan) in fsp.items():
        host = '192.168.0.{}'.format(fsp_id)
        clist = [dict(portOffset=9000, startChannel=fstchan,
                      numChannels=numchan)]
        hlist = [dict(host=host, channels=clist)]
        ralist.append(dict(phaseBinId=0, fspId=fsp_id, hosts=hlist))
    receive_addresses = dict(scanId=scan_id, totalChannels=totchan,
                             receiveAddresses=ralist)

    return receive_addresses


def generate_receive_addresses(channel_link_map):
    """
    Generate receive addresses based on channel link map.

    This function generates a minimal fake response.
    :param channel_link_map: channel link map from CSP
    :return: receive addresses
    """
    scan_id = channel_link_map.get("scanID")
    channels = channel_list(channel_link_map)
    receive_addresses = minimal_receive_addresses(scan_id, channels)
    return receive_addresses


def main(argv):
    """Main loop."""
    # Get processing block ID from first argument
    pb_id = argv[0]

    # Get connection to config DB
    config = ska_sdp_config.Config()

    # Claim processing block
    for txn in config.txn():
        txn.take_processing_block(pb_id, config.client_lease)

    LOG.info('Claimed processing block %s', pb_id)

    # Loop over scans.
    #
    # At the moment there is no way for the workflow to find out if the
    # real-time processing block has ended (i.e. the EndSB command has been
    # called on the subarray device), so there is no exit from this loop.

    LOG.debug("Starting loop over scans")
    scan_id = None

    while True:

        # Wait for change to scan ID in processing block
        LOG.debug("Waiting for new scan ID")
        for txn in config.txn():
            pb = txn.get_processing_block(pb_id)
            if 'scanId' in pb.scan_parameters:
                pb_scan_id = pb.scan_parameters['scanId']
            else:
                pb_scan_id = None
            if pb_scan_id == scan_id:
                txn.loop(wait=True)
        scan_id = pb_scan_id
        LOG.debug("Scan ID set to %d", scan_id)

        # Wait for channel link map with matching scan ID in processing
        # block state
        LOG.debug("Waiting for new channel map")
        for txn in config.txn():
            pb_state = txn.get_processing_block_state(pb_id)
            if pb_state is None or 'channel_link_map' not in pb_state:
                LOG.debug('Channel map not found in PB state')
                txn.loop(wait=True)
                continue
            LOG.debug('Channel map found in PB state')
            channel_link_map = pb_state['channel_link_map']
            clm_scan_id = channel_link_map['scanID']
            LOG.debug('Channel map scan ID: %d', clm_scan_id)
            if clm_scan_id != scan_id:
                txn.loop(wait=True)

        # Generate receive addresses
        LOG.debug("Generating receive addresses")
        receive_addresses = generate_receive_addresses(channel_link_map)

        # Update receive addresses in processing block state
        LOG.debug("Updating receive addresses in processing block state")
        for txn in config.txn():
            pb_state = txn.get_processing_block_state(pb_id)
            pb_state['receive_addresses'] = receive_addresses
            txn.update_processing_block_state(pb_id, pb_state)

    # Close connection to config DB.
    config.close()


def terminate(signal, frame):
    """Terminate the program."""
    LOG.info('Asked to terminate')
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    main(sys.argv[1:])
