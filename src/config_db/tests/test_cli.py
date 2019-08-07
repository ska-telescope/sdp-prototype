"""Tests for sdpcfg command line utility."""

# pylint: disable=missing-docstring

import os
from datetime import date
import pytest

from ska_sdp_config import cli

PREFIX = "/__test_cli"


def test_cli_simple(capsys):

    if os.getenv("SDP_TEST_HOST") is not None:
        os.environ["SDP_CONFIG_HOST"] = os.getenv("SDP_TEST_HOST")

    cli.main(['delete', '-R', PREFIX])
    out, err = capsys.readouterr()

    cli.main(['get', PREFIX+'/test'])
    out, err = capsys.readouterr()
    assert out == PREFIX+"/test = None\n"
    assert err == ""

    cli.main(['create', PREFIX+'/test', 'asdf'])
    out, err = capsys.readouterr()
    assert out == "OK\n"
    assert err == ""

    cli.main(['get', PREFIX+'/test'])
    out, err = capsys.readouterr()
    assert out == PREFIX+"/test = asdf\n"
    assert err == ""

    cli.main(['update', PREFIX+'/test', 'asd'])
    out, err = capsys.readouterr()
    assert out == "OK\n"
    assert err == ""

    cli.main(['get', PREFIX+'/test'])
    out, err = capsys.readouterr()
    assert out == PREFIX+"/test = asd\n"
    assert err == ""

    cli.main(['-q', 'get', PREFIX+'/test'])
    out, err = capsys.readouterr()
    assert out == "asd\n"
    assert err == ""

    cli.main(['create', PREFIX+'/foo', 'bar'])
    out, err = capsys.readouterr()
    assert out == "OK\n"
    assert err == ""

    cli.main(['ls', PREFIX+'/'])
    out, err = capsys.readouterr()
    assert out == "Keys with {pre}/ prefix: {pre}/foo, {pre}/test\n".format(
        pre=PREFIX)
    assert err == ""

    cli.main(['-q', 'list', PREFIX+'/'])
    out, err = capsys.readouterr()
    assert out == "{pre}/foo {pre}/test\n".format(pre=PREFIX)
    assert err == ""

    cli.main(['--prefix', PREFIX, 'process', 'realtime:test:0.1'])
    out, err = capsys.readouterr()
    assert out == "OK, pb_id = realtime-{}-0000\n".format(
        date.today().strftime('%Y%m%d'))
    assert err == ""

    cli.main(['delete', PREFIX+'/test'])
    out, err = capsys.readouterr()
    assert out == "OK\n"
    assert err == ""

    cli.main(['delete', PREFIX+'/foo'])
    out, err = capsys.readouterr()
    assert out == "OK\n"
    assert err == ""


if __name__ == '__main__':
    pytest.main()
