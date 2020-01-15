# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable-msg=E0611
# pylint: disable-msg=E0401
# pylint: disable-msg=R0201
# pylint: disable-msg=E1120
# pylint: disable-msg=C0111
# pylint: disable-msg=W0621
# pylint: disable-msg=W0613
# pylint: disable=fixme

import logging
import pytest

from ska_sdp_logging import core_logging, tango_logging
import core_test


class FakeDevice:
    def info_stream(self, _: str, *args) -> None:
        print("info stream should not be called")

    def get_logger(self) -> logging.Logger:
        return None


@pytest.fixture
def init():
    log = tango_logging.init(device_name="tango test", device_class=FakeDevice)
    hnd = core_test.ListHandler()
    log.addHandler(hnd)
    FakeDevice.get_logger = lambda self: log
    return log, hnd


def test_tango_logging(init):
    log, hnd = init
    dev = FakeDevice()
    assert dev.get_logger() is log
    dev.info_stream("Running tango test")
    dev.info_stream("Running %s test", "tango")
    assert len(hnd.list) == 2
    for log_entry in hnd.list:
        record = core_logging.SkaLogRecord.from_string(log_entry)
        assert record.msg == "Running tango test"
