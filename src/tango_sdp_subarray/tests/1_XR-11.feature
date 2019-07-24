@XR-11
Feature: SDPSubarray device
	#TODO - link to ICD etc here. 


	@XTP-119 @XTP-118
	Scenario: Device Startup
		Given I have a SDPSubarray device
		When The device is initialised
		Then State == OFF
		And obsState == IDLE
		And adminMode == OFFLINE
		And healthState == OK


	@XTP-120 @XTP-118
	Scenario: Assign Resources successfully
		Given I have a SDPSubarray device
		When I set adminMode to ONLINE
		When I call AssignResources
		Then State == ON
		And obsState == IDLE
		And adminMode == ONLINE


	@XTP-121 @XTP-118
	Scenario: Assign Resources fails when ObsState != IDLE
		Given I have a SDPSubarray device
		When The obsState != IDLE
		Then Calling AssignResources raises tango.DevFailed


	@XTP-122 @XTP-118
	Scenario: Release Resources successfully
		Given I have a SDPSubarray device
		When obsState == IDLE
		And I call ReleaseResources
		Then State == OFF
		And obsState == IDLE
		And adminMode either ONLINE or MAINTENANCE


	@XTP-123 @XTP-118
	Scenario: Configure command successful
		Given I have a SDPSubarray device
		When obsState == IDLE
		And I call Configure
		Then obsState == READY


	@XTP-176 @XTP-118
	Scenario: ConfigureScan command successful
		Given I have a SDPSubarray device
		When obsState == IDLE
		And I call ConfigureScan
		Then obsState == READY
