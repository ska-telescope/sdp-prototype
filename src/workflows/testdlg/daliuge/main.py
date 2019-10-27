#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2019
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
import logging
import os
import socket
import sys
import time

import ska_sdp_config
from . import common


SDP_HELM_NAMESPACE = os.environ.get('SDP_HELM_NAMESPACE', 'sdp')

logger = logging.getLogger(__name__)

def get_pb(config, pb_id):
    for txn in config.txn():
        txn.take_processing_block(pb_id, config.client_lease)
        pb = txn.get_processing_block(pb_id)
    logger.info("Claimed processing block %s", pb)
    return pb


def create_deployment(config, pb):
    logger.info("Deploying DALiuGE...")
    deploy_id = pb.pb_id + "-daliuge"
    deployment = ska_sdp_config.Deployment(
        deploy_id, "helm", {
            'chart': 'daliuge',
        })
    for txn in config.txn():
        txn.create_deployment(deployment)
    return deployment


def idle_for_some_obscure_reason(config, pb):
    logger.info("Done, now idling...")
    for txn in config.txn():
        if not txn.is_processing_block_owner(pb.pb_id):
            break
        txn.loop(True)


def cleanup(config, deployment):
    for txn in config.txn():
        txn.delete_deployment(deployment)
    config.close()


def resolve_dim_host(deployment_id):
    tries = 1
    max_tries = 200
    dlg_dim_host = deployment_id + '-dlg-dim.' + SDP_HELM_NAMESPACE
    logger.info("Resolving IP for DIM located at %s", dlg_dim_host)
    for _ in range(max_tries):
        try:
            dlg_dim_ip = socket.gethostbyname(dlg_dim_host)
            logger.info("Resolved %s to %s", dlg_dim_host, dlg_dim_ip)
            break
        except socket.gaierror:
            logger.warning("Cannot resolve %s yet, trying again (%d/%d)",
                    dlg_dim_host, tries, max_tries)
            tries += 1
            time.sleep(1)
    if dlg_dim_ip is None:
        raise RuntimeError("Couldn't resolve %s, cannot continue", dlg_dim_host)
    return dlg_dim_ip


def main():
    logging.basicConfig(level=logging.INFO)
    config = ska_sdp_config.Config()
    pb = get_pb(config, sys.argv[1])
    deployment = create_deployment(config, pb)
    try:
        dlg_dim_ip = resolve_dim_host(deployment.deploy_id)
        common.run_processing_block(pb, lambda _: None,
                host=dlg_dim_ip, port=8001)
        idle_for_some_obscure_reason(config, pb)
    finally:
        cleanup(config, deployment)

if __name__ == '__main__':
    main()
