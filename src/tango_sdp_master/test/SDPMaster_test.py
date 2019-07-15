#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the SDP Master Tango Class."""
# pylint: disable=redefined-outer-name, invalid-name


# Imports
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
    properties = {'SkaLevel': '4', 'CentralLoggingTarget': '',
                  'ElementLoggingTarget': '',
                  'StorageLoggingTarget': 'localhost', 'GroupDefinitions': '',
                  'NrSubarrays': '16', 'CapabilityTypes': '',
                  'MaxCapabilities': '',
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

    # def test_properties(self):
    #     # test the properties
    #     # PROTECTED REGION ID(SDPMaster.test_properties) ENABLED START #
    #     # PROTECTED REGION END #    //  SDPMaster.test_properties
    #     pass
    #
    # def test_State(self):
    #     """Test for State"""
    #     # PROTECTED REGION ID(SDPMaster.test_State) ENABLED START #
    #     self.device.State()
    #     # PROTECTED REGION END #    //  SDPMaster.test_State
    #
    # def test_Status(self):
    #     """Test for Status"""
    #     # PROTECTED REGION ID(SDPMaster.test_Status) ENABLED START #
    #     self.device.Status()
    #     # PROTECTED REGION END #    //  SDPMaster.test_Status
    #
    # def test_isCapabilityAchievable(self):
    #     """Test for isCapabilityAchievable"""
    #     # PROTECTED REGION ID(SDPMaster.test_isCapabilityAchievable)
    #     ENABLED START #
    #     self.device.isCapabilityAchievable([[0], [""]])
    #     # PROTECTED REGION END #   //  SDPMaster.test_isCapabilityAchievable
    #
    # def test_Reset(self):
    #     """Test for Reset"""
    #     # PROTECTED REGION ID(SDPMaster.test_Reset) ENABLED START #
    #     self.device.Reset()
    #     # PROTECTED REGION END #    //  SDPMaster.test_Reset
    #
    # def test_on(self):
    #     """Test for on"""
    #     # PROTECTED REGION ID(SDPMaster.test_on) ENABLED START #
    #     self.device.on()
    #     # PROTECTED REGION END #    //  SDPMaster.test_on
    #
    # def test_disable(self):
    #     """Test for disable"""
    #     # PROTECTED REGION ID(SDPMaster.test_disable) ENABLED START #
    #     self.device.disable()
    #     # PROTECTED REGION END #    //  SDPMaster.test_disable
    #
    # def test_standby(self):
    #     """Test for standby"""
    #     # PROTECTED REGION ID(SDPMaster.test_standby) ENABLED START #
    #     self.device.standby()
    #     # PROTECTED REGION END #    //  SDPMaster.test_standby
    #
    # def test_off(self):
    #     """Test for off"""
    #     # PROTECTED REGION ID(SDPMaster.test_off) ENABLED START #
    #     self.device.off()
    #     # PROTECTED REGION END #    //  SDPMaster.test_off
    #
    # def test_GetVersionInfo(self):
    #     """Test for GetVersionInfo"""
    #     # PROTECTED REGION ID(SDPMaster.test_GetVersionInfo) ENABLED START #
    #     self.device.GetVersionInfo()
    #     # PROTECTED REGION END #    //  SDPMaster.test_GetVersionInfo
    #
    # def test_elementLoggerAddress(self):
    #     """Test for elementLoggerAddress"""
    #     # PROTECTED REGION ID(SDPMaster.test_elementLoggerAddress)
    #     ENABLED START #
    #     self.device.elementLoggerAddress
    #     # PROTECTED REGION END #    //  SDPMaster.test_elementLoggerAddress
    #
    # def test_elementAlarmAddress(self):
    #     """Test for elementAlarmAddress"""
    #     # PROTECTED REGION ID(SDPMaster.test_elementAlarmAddress)
    #     ENABLED START #
    #     self.device.elementAlarmAddress
    #     # PROTECTED REGION END #    //  SDPMaster.test_elementAlarmAddress
    #
    # def test_elementTelStateAddress(self):
    #     """Test for elementTelStateAddress"""
    #     # PROTECTED REGION ID(SDPMaster.test_elementTelStateAddress)
    #     ENABLED START #
    #     self.device.elementTelStateAddress
    #     # PROTECTED REGION END #    //  SDPMaster.test_elementTelStateAddress
    #
    # def test_elementDatabaseAddress(self):
    #     """Test for elementDatabaseAddress"""
    #     # PROTECTED REGION ID(SDPMaster.test_elementDatabaseAddress)
    #     ENABLED START #
    #     self.device.elementDatabaseAddress
    #     # PROTECTED REGION END #    //  SDPMaster.test_elementDatabaseAddress
    #
    # def test_buildState(self):
    #     """Test for buildState"""
    #     # PROTECTED REGION ID(SDPMaster.test_buildState) ENABLED START #
    #     self.device.buildState
    #     # PROTECTED REGION END #    //  SDPMaster.test_buildState
    #
    # def test_versionId(self):
    #     """Test for versionId"""
    #     # PROTECTED REGION ID(SDPMaster.test_versionId) ENABLED START #
    #     self.device.versionId
    #     # PROTECTED REGION END #    //  SDPMaster.test_versionId
    #
    # def test_centralLoggingLevel(self):
    #     """Test for centralLoggingLevel"""
    #     # PROTECTED REGION ID(SDPMaster.test_centralLoggingLevel)
    #     ENABLED START #
    #     self.device.centralLoggingLevel
    #     # PROTECTED REGION END #    //  SDPMaster.test_centralLoggingLevel
    #
    # def test_elementLoggingLevel(self):
    #     """Test for elementLoggingLevel"""
    #     # PROTECTED REGION ID(SDPMaster.test_elementLoggingLevel)
    #     ENABLED START #
    #     self.device.elementLoggingLevel
    #     # PROTECTED REGION END #    //  SDPMaster.test_elementLoggingLevel
    #
    # def test_storageLoggingLevel(self):
    #     """Test for storageLoggingLevel"""
    #     # PROTECTED REGION ID(SDPMaster.test_storageLoggingLevel)
    #     ENABLED START #
    #     self.device.storageLoggingLevel
    #     # PROTECTED REGION END #    //  SDPMaster.test_storageLoggingLevel
    #
    # def test_healthState(self):
    #     """Test for healthState"""
    #     # PROTECTED REGION ID(SDPMaster.test_healthState) ENABLED START #
    #     self.device.healthState
    #     # PROTECTED REGION END #    //  SDPMaster.test_healthState
    #
    # def test_adminMode(self):
    #     """Test for adminMode"""
    #     # PROTECTED REGION ID(SDPMaster.test_adminMode) ENABLED START #
    #     self.device.adminMode
    #     # PROTECTED REGION END #    //  SDPMaster.test_adminMode
    #
    # def test_controlMode(self):
    #     """Test for controlMode"""
    #     # PROTECTED REGION ID(SDPMaster.test_controlMode) ENABLED START #
    #     self.device.controlMode
    #     # PROTECTED REGION END #    //  SDPMaster.test_controlMode
    #
    # def test_simulationMode(self):
    #     """Test for simulationMode"""
    #     # PROTECTED REGION ID(SDPMaster.test_simulationMode) ENABLED START #
    #     self.device.simulationMode
    #     # PROTECTED REGION END #    //  SDPMaster.test_simulationMode
    #
    # def test_testMode(self):
    #     """Test for testMode"""
    #     # PROTECTED REGION ID(SDPMaster.test_testMode) ENABLED START #
    #     self.device.testMode
    #     # PROTECTED REGION END #    //  SDPMaster.test_testMode
    #
    # def test_maxCapabilities(self):
    #     """Test for maxCapabilities"""
    #     # PROTECTED REGION ID(SDPMaster.test_maxCapabilities) ENABLED START
    #     self.device.maxCapabilities
    #     # PROTECTED REGION END #    //  SDPMaster.test_maxCapabilities
    #
    # def test_availableCapabilities(self):
    #     """Test for availableCapabilities"""
    #     # PROTECTED REGION ID(SDPMaster.test_availableCapabilities)
    #     ENABLED START #
    #     self.device.availableCapabilities
    #     # PROTECTED REGION END #    //  SDPMaster.test_availableCapabilities


# # Main execution
# if __name__ == "__main__":
#     main()
