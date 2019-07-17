"""Tests for sdpcfg command line utility."""

# pylint: disable=missing-docstring

import pytest

from ska_sdp_config import cli

PREFIX = "/__test_cli"


def test_cli_simple(capsys):

    cli.main(['create', PREFIX+'/test', 'asd'])
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
    assert out == "{pre}/foo, {pre}/test\n".format(pre=PREFIX)
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
