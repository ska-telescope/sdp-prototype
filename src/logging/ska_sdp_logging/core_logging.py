"""
Core logging functionality.

This module depends only on the Python standard library.
"""
# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes
# pylint: disable=broad-except
# pylint: disable=fixme

import logging
import sys
import time
from typing import Iterable

# Logging standard version.
VERSION = '1'

# Default field delimiter.
DELIMITER = '|'

# Delimiter splitting tag fields.
TAG_SPLIT = ','

# Force times to UTC.
logging.Formatter.converter = time.gmtime


class SkaLogRecord:
    """
    Defines the fields of a log record.

    The main use of this class is to be verification of correct log format.
    However, it could also be used to construct correctly formatted records
    with fine-grained control of the field values.
    """

    def __init__(self):
        """Initialise the log record."""
        self.version = ""
        self.utc = ""
        self.severity = ""
        self.thread = ""
        self.function = ""
        self.line_loc = ""
        self.tags = ()
        self.msg = ""

    @staticmethod
    def from_string(log: str, delimiter=DELIMITER) -> 'SkaLogRecord':
        """Parse a log string into its component fields.

        :param log: log string
        :param delimiter: of fields. default: '|'
        :returns: a record object
        """
        record = SkaLogRecord()
        fields = log.split(delimiter)
        record.version = fields[0]
        record.utc = fields[1]
        record.severity = fields[2]
        record.thread = fields[3]
        record.function = fields[4]
        record.line_loc = fields[5]
        record.tags = fields[6].split(',')
        record.msg = fields[7]
        return record

    def __repr__(self) -> str:
        # Build string representation.
        return DELIMITER.join((self.version, self.utc, self.severity,
                               self.thread, self.function, self.line_loc,
                               TAG_SPLIT.join(self.tags), self.msg))


class SkaFormatter(logging.Formatter):
    """Standard logging formatter."""

    def __init__(self, *tags: str, delimiter=DELIMITER):
        """Initialise the formatter.

        :param tags: to insert into tag field
        :param delimiter: of fields. default: '|'
        """
        super().__init__(
            fmt=delimiter.join((
                VERSION,
                "%(asctime)s.%(msecs)03dZ",
                "%(levelname)s",
                "%(threadName)s",
                "%(funcName)s",
                "%(filename)s#%(lineno)d",
                TAG_SPLIT.join(tags),
                "%(message)s")),
            datefmt='%Y-%m-%dT%H:%M:%S')


class SkaStreamHandler(logging.StreamHandler):
    """Standard handler for logging to stdout."""

    def __init__(self, stream=sys.stdout):
        """Initialise the stream handler.

        :param stream: to write to default: stdout
        """
        super().__init__(stream=stream)

def init(*tags: str, name=None, level=logging.INFO,
         formatter=None) -> logging.Logger:
    """
    Initialise standard logging.

    :param tags: to insert into tag field.
    :param name: of logger, top-level if None. default: None
    :param formatter to use, default is SkaFormatter
    :param level: to log. default: INFO
    :returns: logger object
    """
    log = logging.getLogger(name)
    log.setLevel(level)

    # This stops messages being propagated to higher level loggers.
    log.propagate = False
    log.handlers.clear()

    # Add a handler to stdout with correct formatting.
    handler = SkaStreamHandler()
    if formatter is None:
        formatter = SkaFormatter(*tags)
    handler.setFormatter(formatter)
    log.addHandler(handler)
    logging.info("Logging initialised")
    return log


def verify(stream: Iterable[str]) -> bool:
    """Verify the correct formatting of a log.

    :param stream: text stream of log, iterable object of string
    :returns True if correctly formatted, False otherwise.
    """
    ok: bool = True
    for line in stream:
        try:
            SkaLogRecord.from_string(line)
            # TODO: check more stuff (should be in the class method?)
        except Exception as e:
            logging.error(str(e))
            ok = False
            break
    return ok
