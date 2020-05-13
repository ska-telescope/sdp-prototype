# -*- coding: utf-8 -*-
import importlib
import logging
import sys

import unittest.mock as mock
import pytest

from ska_sdp_logging import core_logging, tango_logging
import core_test

MSG = "Running tango test"


class FakeDevice:
    def info_stream(self, _: str, *args) -> None:
        print("info stream should not be called")

    def get_logger(self) -> logging.Logger:
        return None


def init_tango(with_device=True):
    kwargs = {'device_name': 'tango test'}
    if with_device:
        kwargs['device_class'] = FakeDevice
    log = tango_logging.init(**kwargs)
    hnd = core_test.ListHandler()
    log.addHandler(hnd)
    FakeDevice.get_logger = lambda self: log
    return log, hnd, FakeDevice()


@pytest.fixture
def init():
    return init_tango()


def test_tango_logging(init):
    log, hnd, dev = init
    assert dev.get_logger() is log
    dev.info_stream(MSG)
    dev.info_stream("Running %s test", "tango")
    assert len(hnd.list) == 2
    for log_entry in hnd.list:
        record = core_logging.SkaLogRecord.from_string(log_entry)
        assert record.msg == MSG


def test_no_tango_logging():
    with mock.patch.dict(sys.modules, {'tango': None}):
        importlib.reload(tango_logging)
        log, hnd, dev = init_tango(with_device=False)
        assert dev.get_logger() is log
        dev.info_stream(MSG)
        assert len(hnd.list) == 1
