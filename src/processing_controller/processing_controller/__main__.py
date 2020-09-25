"""
SDP Processing Controller main
"""
import os
import sys
import signal
import logging
from ska.logging import configure_logging
from . import ProcessingController

LOG_LEVEL = os.getenv('SDP_LOG_LEVEL', 'DEBUG')
WORKFLOWS_URL = os.getenv('SDP_WORKFLOWS_URL',
                          'https://gitlab.com/ska-telescope/sdp-prototype/-/raw/master/src/workflows/workflows.json')
WORKFLOWS_REFRESH = int(os.getenv('SDP_WORKFLOWS_REFRESH', '300'))

WORKFLOWS_SCHEMA = os.path.join(os.path.dirname(__file__), 'schema',
                                'workflows.json')

configure_logging(level=LOG_LEVEL)
LOG = logging.getLogger(__name__)


def terminate(signal, frame):
    """Terminate the program."""
    LOG.info("Asked to terminate")
    # Note that this will likely send SIGKILL to child processes -
    # not exactly how this is supposed to work. But all of this is
    # temporary anyway.
    sys.exit(0)

# Register SIGTERM handler
signal.signal(signal.SIGTERM, terminate)

# Initialise processing controller
pc = ProcessingController(WORKFLOWS_SCHEMA, WORKFLOWS_URL, WORKFLOWS_REFRESH)

# Enter main loop
pc.main()
