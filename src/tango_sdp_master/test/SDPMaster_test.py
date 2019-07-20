# -*- coding: utf-8 -*-
"""Tests for the SDP Master Tango Class."""
# pylint: disable=redefined-outer-name, invalid-name

import pytest

from SDPMaster import SDPMaster


# Note:
#
# Since the device uses an inner thread, it is necessary to
# wait during the tests in order the let the device update itself.
# Hence, the sleep calls have to be secured enough not to produce
# any inconsistent behavior. However, the unittests need to run fast.
# Here, we use a factor 3 between the read period and the sleep calls.
#
# Look at devicetest examples for more advanced testing


# Device test case
@pytest.mark.usefixtures("tango_context")
class TestSDPMaster:
    """Test case for packet generation."""

    # pylint: disable=, no-self-use,

    # PROTECTED REGION ID(SDPMaster.test_additionnal_import) ENABLED START #
    # PROTECTED REGION END #    //  SDPMaster.test_additionnal_import
    device = SDPMaster
    properties = {
        'SkaLevel': '4',
        'CentralLoggingTarget': '',
        'ElementLoggingTarget': '',
        'StorageLoggingTarget': 'localhost',
        'GroupDefinitions': '',
        'NrSubarrays': '16',
        'CapabilityTypes': '',
        'MaxCapabilities': ''
    }
    empty = None  # Should be []

    @classmethod
    def mocking(cls):
        """Mock external libraries."""
        # Example : Mock numpy
        # cls.numpy = SDPMaster.numpy = MagicMock()
        # PROTECTED REGION ID(SDPMaster.test_mocking) ENABLED START #
        # PROTECTED REGION END #    //  SDPMaster.test_mocking

    def test_operating_state(self, tango_context):
        """Test for Operating State."""
        # PROTECTED REGION ID(SDPMaster.test_OperatingState) ENABLED START #
        assert tango_context.device.OperatingState == 0
        # PROTECTED REGION END #    //  SDPMaster.test_OperatingState

    def test_on_state(self, tango_context):
        """Test for ON State."""
        tango_context.device.on()
        assert tango_context.device.OperatingState == 1

    def test_standby_state(self, tango_context):
        """Test for STANDBY State."""
        tango_context.device.standby()
        assert tango_context.device.OperatingState == 3

    def test_disable_state(self, tango_context):
        """Test for DISABLE State."""
        tango_context.device.disable()
        assert tango_context.device.OperatingState == 2

    def test_off_state(self, tango_context):
        """Test for OFF State."""
        tango_context.device.off()
        assert tango_context.device.OperatingState == 6

    def test_health_state(self, tango_context):
        """Test for healthState."""
        device = tango_context.device
        device.init()
        assert device.healthState == 0
