"""
Helm deployment controller.

Applies/updates/deletes Helm releases depending on information from
the SDP configuration.
"""

# pylint: disable=C0103

import os
import time
import subprocess
import shutil
import logging
#import json
# from dotenv import load_dotenv
# load_dotenv()

from ska_sdp_config.config import Config as ConfigDbClient
from ska_sdp_config.entity import ProcessingBlock

HELM = shutil.which(os.getenv('SDP_HELM', 'helm'))
HELM_TIMEOUT = int(os.getenv('SDP_HELM_TIMEOUT', str(300)))
NAMESPACE = os.getenv('SDP_HELM_NAMESPACE', 'sdp-helm')
LOGGER = os.getenv('SDP_LOGGER', 'main')
LOG_LEVEL = int(os.getenv('SDP_LOG_LEVEL', str(logging.DEBUG)))
CHART_REPO_REFRESH = int(os.getenv('SDP_CHART_REFRESH', '300'))
# CHART_REPO_PATH = os.getenv('SDP_CHART_REPO_PATH', 'deploy/charts')

# Initialise logger
logging.basicConfig()
log = logging.getLogger(LOGGER)
log.setLevel(LOG_LEVEL)

# # Where we are going to check out the charts
# chart_base_path = 'chart-repo'
# chart_path = os.path.join(chart_base_path, CHART_REPO_PATH)

# Initialise logger
logging.basicConfig()
log = logging.getLogger(LOGGER)
log.setLevel(LOG_LEVEL)


def main():
    """Main loop Processing block."""

    if ConfigDbClient:
        config_db_client = ConfigDbClient()  # SDP Config db client.
        log.debug('Config Db enabled!')
    else:
        log.error("No Config Db")

    next_chart_refresh = time.time() + CHART_REPO_REFRESH

    # Wait for something to happen
    for txn in config_db_client.txn():

        # Refresh charts?
        if time.time() > next_chart_refresh:
            next_chart_refresh = time.time() + CHART_REPO_REFRESH

        log.info("Waiting for processing block...")
        # List processing blocks
        target_pb_blocks = txn.list_processing_blocks()


        # Check for pb we should add
        for pb_id in target_pb_blocks:
            log.info(pb_id)
            log.info()
            # with open('workflow_list.json', 'w') as workflow_list:
            #     w_list = json.load(workflow_list)
            #     log.info(w_list)

            # if find the appropriate workflow start it


            # Deploy appropriate workflow
            log.info("Deploying Vis Receive Workflow...")
            deploy_id = pb_id + "-vis-receive"
            deploy = txn.Deployment(
                deploy_id, "helm", {
                    'chart': 'workflow-visreceive',  # Helm chart deploy/charts/workflow-visreceive
                })
            txn.create_deployment(deploy)

                # if txn.get_processing_block_owner(pb_id) is None:
                #     # Take ownership
                #     txn.take_processing_block(pb_id, txn.client_lease)


        # Loop around, wait if we made no change
        timeout = next_chart_refresh
        txn.loop(wait=True, timeout=next_chart_refresh - time.time())


main()
