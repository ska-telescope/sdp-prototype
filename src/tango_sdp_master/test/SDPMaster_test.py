# -*- coding: utf-8 -*-
"""Tests for the SDP Master Tango Class."""
# pylint: disable=redefined-outer-name, invalid-name

import pytest

from SDPMaster import (SDPMaster, OperatingState, HealthState)


@pytest.mark.usefixtures("tango_context")
class TestSDPMaster:
    """Test for SDPMaster."""

    # pylint: disable=no-self-use

    device = SDPMaster

    def test_on_state(self, tango_context):
        """Test for ON State."""
        tango_context.device.On()
        assert tango_context.device.operatingState == OperatingState.ON

    def test_standby_state(self, tango_context):
        """Test for STANDBY State."""
        tango_context.device.Standby()
        assert tango_context.device.operatingState == OperatingState.STANDBY

    def test_disable_state(self, tango_context):
        """Test for DISABLE State."""
        tango_context.device.Disable()
        assert tango_context.device.operatingState == OperatingState.DISABLE

    def test_off_state(self, tango_context):
        """Test for OFF State."""
        tango_context.device.Off()
        assert tango_context.device.operatingState == OperatingState.OFF

    def test_health_state(self, tango_context):
        """Test for healthState."""
        device = tango_context.device
        device.init()
        assert device.healthState == HealthState.OK
