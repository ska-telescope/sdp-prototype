#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of the SDPSubarray project
#
#
#
# Distributed under the terms of the none license.
# See LICENSE.txt for more info.
"""Contain the tests for the SDPSubarray."""

# Path
import sys
import os
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(path))

# Imports
from time import sleep
from mock import MagicMock
from PyTango import DevFailed, DevState
from devicetest import DeviceTestCase, main
from SDPSubarray import SDPSubarray

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
class SDPSubarrayDeviceTestCase(DeviceTestCase):
    """Test case for packet generation."""
    # PROTECTED REGION ID(SDPSubarray.test_additionnal_import) ENABLED START #
    # PROTECTED REGION END #    //  SDPSubarray.test_additionnal_import
    device = SDPSubarray
    properties = {'CapabilityTypes': '', 'CentralLoggingTarget': '', 'ElementLoggingTarget': '', 'GroupDefinitions': '', 'SkaLevel': '4', 'StorageLoggingTarget': 'localhost', 'SubID': '', 
                  }
    empty = None  # Should be []

    @classmethod
    def mocking(cls):
        """Mock external libraries."""
        # Example : Mock numpy
        # cls.numpy = SDPSubarray.numpy = MagicMock()
        # PROTECTED REGION ID(SDPSubarray.test_mocking) ENABLED START #
        # PROTECTED REGION END #    //  SDPSubarray.test_mocking

    def test_properties(self):
        # test the properties
        # PROTECTED REGION ID(SDPSubarray.test_properties) ENABLED START #
        # PROTECTED REGION END #    //  SDPSubarray.test_properties
        pass

    def test_Abort(self):
        """Test for Abort"""
        # PROTECTED REGION ID(SDPSubarray.test_Abort) ENABLED START #
        self.device.Abort()
        # PROTECTED REGION END #    //  SDPSubarray.test_Abort

    def test_ConfigureCapability(self):
        """Test for ConfigureCapability"""
        # PROTECTED REGION ID(SDPSubarray.test_ConfigureCapability) ENABLED START #
        self.device.ConfigureCapability([[0], [""]])
        # PROTECTED REGION END #    //  SDPSubarray.test_ConfigureCapability

    def test_DeconfigureAllCapabilities(self):
        """Test for DeconfigureAllCapabilities"""
        # PROTECTED REGION ID(SDPSubarray.test_DeconfigureAllCapabilities) ENABLED START #
        self.device.DeconfigureAllCapabilities("")
        # PROTECTED REGION END #    //  SDPSubarray.test_DeconfigureAllCapabilities

    def test_DeconfigureCapability(self):
        """Test for DeconfigureCapability"""
        # PROTECTED REGION ID(SDPSubarray.test_DeconfigureCapability) ENABLED START #
        self.device.DeconfigureCapability([[0], [""]])
        # PROTECTED REGION END #    //  SDPSubarray.test_DeconfigureCapability

    def test_GetVersionInfo(self):
        """Test for GetVersionInfo"""
        # PROTECTED REGION ID(SDPSubarray.test_GetVersionInfo) ENABLED START #
        self.device.GetVersionInfo()
        # PROTECTED REGION END #    //  SDPSubarray.test_GetVersionInfo

    def test_Status(self):
        """Test for Status"""
        # PROTECTED REGION ID(SDPSubarray.test_Status) ENABLED START #
        self.device.Status()
        # PROTECTED REGION END #    //  SDPSubarray.test_Status

    def test_State(self):
        """Test for State"""
        # PROTECTED REGION ID(SDPSubarray.test_State) ENABLED START #
        self.device.State()
        # PROTECTED REGION END #    //  SDPSubarray.test_State

    def test_AssignResources(self):
        """Test for AssignResources"""
        # PROTECTED REGION ID(SDPSubarray.test_AssignResources) ENABLED START #
        self.device.AssignResources("")
        # PROTECTED REGION END #    //  SDPSubarray.test_AssignResources

    def test_EndSB(self):
        """Test for EndSB"""
        # PROTECTED REGION ID(SDPSubarray.test_EndSB) ENABLED START #
        self.device.EndSB()
        # PROTECTED REGION END #    //  SDPSubarray.test_EndSB

    def test_EndScan(self):
        """Test for EndScan"""
        # PROTECTED REGION ID(SDPSubarray.test_EndScan) ENABLED START #
        self.device.EndScan()
        # PROTECTED REGION END #    //  SDPSubarray.test_EndScan

    def test_ObsState(self):
        """Test for ObsState"""
        # PROTECTED REGION ID(SDPSubarray.test_ObsState) ENABLED START #
        self.device.ObsState()
        # PROTECTED REGION END #    //  SDPSubarray.test_ObsState

    def test_Pause(self):
        """Test for Pause"""
        # PROTECTED REGION ID(SDPSubarray.test_Pause) ENABLED START #
        self.device.Pause()
        # PROTECTED REGION END #    //  SDPSubarray.test_Pause

    def test_ReleaseAllResources(self):
        """Test for ReleaseAllResources"""
        # PROTECTED REGION ID(SDPSubarray.test_ReleaseAllResources) ENABLED START #
        self.device.ReleaseAllResources()
        # PROTECTED REGION END #    //  SDPSubarray.test_ReleaseAllResources

    def test_ReleaseResources(self):
        """Test for ReleaseResources"""
        # PROTECTED REGION ID(SDPSubarray.test_ReleaseResources) ENABLED START #
        self.device.ReleaseResources("")
        # PROTECTED REGION END #    //  SDPSubarray.test_ReleaseResources

    def test_Reset(self):
        """Test for Reset"""
        # PROTECTED REGION ID(SDPSubarray.test_Reset) ENABLED START #
        self.device.Reset()
        # PROTECTED REGION END #    //  SDPSubarray.test_Reset

    def test_Resume(self):
        """Test for Resume"""
        # PROTECTED REGION ID(SDPSubarray.test_Resume) ENABLED START #
        self.device.Resume()
        # PROTECTED REGION END #    //  SDPSubarray.test_Resume

    def test_Scan(self):
        """Test for Scan"""
        # PROTECTED REGION ID(SDPSubarray.test_Scan) ENABLED START #
        self.device.Scan([""])
        # PROTECTED REGION END #    //  SDPSubarray.test_Scan

    def test_activationTime(self):
        """Test for activationTime"""
        # PROTECTED REGION ID(SDPSubarray.test_activationTime) ENABLED START #
        self.device.activationTime
        # PROTECTED REGION END #    //  SDPSubarray.test_activationTime

    def test_adminMode(self):
        """Test for adminMode"""
        # PROTECTED REGION ID(SDPSubarray.test_adminMode) ENABLED START #
        self.device.adminMode
        # PROTECTED REGION END #    //  SDPSubarray.test_adminMode

    def test_buildState(self):
        """Test for buildState"""
        # PROTECTED REGION ID(SDPSubarray.test_buildState) ENABLED START #
        self.device.buildState
        # PROTECTED REGION END #    //  SDPSubarray.test_buildState

    def test_centralLoggingLevel(self):
        """Test for centralLoggingLevel"""
        # PROTECTED REGION ID(SDPSubarray.test_centralLoggingLevel) ENABLED START #
        self.device.centralLoggingLevel
        # PROTECTED REGION END #    //  SDPSubarray.test_centralLoggingLevel

    def test_configurationDelayExpected(self):
        """Test for configurationDelayExpected"""
        # PROTECTED REGION ID(SDPSubarray.test_configurationDelayExpected) ENABLED START #
        self.device.configurationDelayExpected
        # PROTECTED REGION END #    //  SDPSubarray.test_configurationDelayExpected

    def test_configurationProgress(self):
        """Test for configurationProgress"""
        # PROTECTED REGION ID(SDPSubarray.test_configurationProgress) ENABLED START #
        self.device.configurationProgress
        # PROTECTED REGION END #    //  SDPSubarray.test_configurationProgress

    def test_controlMode(self):
        """Test for controlMode"""
        # PROTECTED REGION ID(SDPSubarray.test_controlMode) ENABLED START #
        self.device.controlMode
        # PROTECTED REGION END #    //  SDPSubarray.test_controlMode

    def test_elementLoggingLevel(self):
        """Test for elementLoggingLevel"""
        # PROTECTED REGION ID(SDPSubarray.test_elementLoggingLevel) ENABLED START #
        self.device.elementLoggingLevel
        # PROTECTED REGION END #    //  SDPSubarray.test_elementLoggingLevel

    def test_healthState(self):
        """Test for healthState"""
        # PROTECTED REGION ID(SDPSubarray.test_healthState) ENABLED START #
        self.device.healthState
        # PROTECTED REGION END #    //  SDPSubarray.test_healthState

    def test_obsMode(self):
        """Test for obsMode"""
        # PROTECTED REGION ID(SDPSubarray.test_obsMode) ENABLED START #
        self.device.obsMode
        # PROTECTED REGION END #    //  SDPSubarray.test_obsMode

    def test_obsState(self):
        """Test for obsState"""
        # PROTECTED REGION ID(SDPSubarray.test_obsState) ENABLED START #
        self.device.obsState
        # PROTECTED REGION END #    //  SDPSubarray.test_obsState

    def test_simulationMode(self):
        """Test for simulationMode"""
        # PROTECTED REGION ID(SDPSubarray.test_simulationMode) ENABLED START #
        self.device.simulationMode
        # PROTECTED REGION END #    //  SDPSubarray.test_simulationMode

    def test_storageLoggingLevel(self):
        """Test for storageLoggingLevel"""
        # PROTECTED REGION ID(SDPSubarray.test_storageLoggingLevel) ENABLED START #
        self.device.storageLoggingLevel
        # PROTECTED REGION END #    //  SDPSubarray.test_storageLoggingLevel

    def test_testMode(self):
        """Test for testMode"""
        # PROTECTED REGION ID(SDPSubarray.test_testMode) ENABLED START #
        self.device.testMode
        # PROTECTED REGION END #    //  SDPSubarray.test_testMode

    def test_versionId(self):
        """Test for versionId"""
        # PROTECTED REGION ID(SDPSubarray.test_versionId) ENABLED START #
        self.device.versionId
        # PROTECTED REGION END #    //  SDPSubarray.test_versionId

    def test_assignedResources(self):
        """Test for assignedResources"""
        # PROTECTED REGION ID(SDPSubarray.test_assignedResources) ENABLED START #
        self.device.assignedResources
        # PROTECTED REGION END #    //  SDPSubarray.test_assignedResources

    def test_configuredCapabilities(self):
        """Test for configuredCapabilities"""
        # PROTECTED REGION ID(SDPSubarray.test_configuredCapabilities) ENABLED START #
        self.device.configuredCapabilities
        # PROTECTED REGION END #    //  SDPSubarray.test_configuredCapabilities


# Main execution
if __name__ == "__main__":
    main()
