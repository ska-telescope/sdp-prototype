@XR-11
Feature: SDPSubarray device
	#300-000000-029 rev 04 SDP to TM ICD
	#
	#Section 2.4.1 Control, State and Configuration

	
	@XTP-119 @XTP-118
	Scenario: Device Startup
		Given I have a SDPSubarray device
		When the device is initialised
		Then State should be OFF
		And obsState should be IDLE
		And adminMode should be OFFLINE
		And healthState should be OK	

	
	@XTP-120 @XTP-118
	Scenario: Assign Resources successfully
		Given I have a SDPSubarray device
		When I set adminMode to ONLINE
		And I call AssignResources
		Then State should be ON
		And obsState should be IDLE
		And adminMode should be ONLINE
			

	
	@XTP-121 @XTP-118
	Scenario: Assign Resources fails when obsState is not IDLE
		Given I have a SDPSubarray device
		When obsState is not IDLE
		Then calling AssignResources raises tango.DevFailed
			

	
	@XTP-122 @XTP-118
	Scenario: Release Resources successfully
		Given I have a SDPSubarray device
		When obsState is IDLE
		And I call ReleaseResources
		Then State should be OFF
		And obsState should be IDLE
		And adminMode should be ONLINE or MAINTENANCE
			

	#Tests successful execution of the SDP Subarray Configure command.
	@XTP-123 @XTP-118
	Scenario: Configure command successful
		Given I have a SDPSubarray device
		When obsState is IDLE
		And I call Configure
		Then obsState should be READY
			

	#Test that the SDPSubarray {{ConfigureScan}} command executes successfully and updates the obsState attribute as expected.
	@XTP-176 @XTP-118
	Scenario: ConfigureScan command successful
		Given I have a SDPSubarray device
		When obsState is IDLE
		And I call ConfigureScan
		Then obsState should be READY


	Scenario: StartScan command successful
		Given I have a SDPSubarray device
		When obsState is READY
		And I call StartScan
		Then obsState should be SCANNING


     	Scenario: EndScan command successful
		Given I have a SDPSubarray device
		When obsState is SCANNING
		And I call EndScan
		Then obsState should be READY
