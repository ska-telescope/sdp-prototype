# -*- coding: utf-8 -*-
"""Tests for the core of SDP logging."""
# pylint: disable=redefined-outer-name
# pylint: disable=invalid-name
# pylint: disable-msg=E0611
# pylint: disable-msg=E0401
# pylint: disable-msg=C1801
# pylint: disable-msg=C0111

import logging
import typing

from ska_sdp_logging import core_logging


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.list = []
        self.setFormatter(core_logging.SkaFormatter("test"))

    def emit(self, record: logging.LogRecord) -> None:
        self.list.append(self.format(record))

    def __iter__(self) -> typing.Iterable:
        return self.list.__iter__()


def test_init():
    core_logging.init()
    logging.info("no tags")
    core_logging.init("test")
    logging.info("one tag")
    core_logging.init("test", "another test")
    logging.info("two tags")


def test_record():
    record = core_logging.SkaLogRecord()
    assert str(record) == core_logging.DELIMITER*7

    log = core_logging.init()
    hnd = ListHandler()
    log.addHandler(hnd)
    assert len(hnd.list) == 0
    log.info("info message")
    assert len(hnd.list) == 1
    log.debug("debug message")
    assert len(hnd.list) == 1

    record = core_logging.SkaLogRecord.from_string(hnd.list[0])
    assert str(record) == hnd.list[0]
    assert record.version == core_logging.VERSION
    assert record.msg == "info message"
    assert record.severity == 'INFO'
    assert record.tags[0] == 'test'


def test_verify():
    log = core_logging.init()
    hnd = ListHandler()
    log.addHandler(hnd)
    assert core_logging.verify(hnd)
    log.info("message")
    assert core_logging.verify(hnd)
    assert not core_logging.verify(["this should fail"])
