@VTS-223
Feature: SDP Subarray Device
	#300-000000-029 rev 04 SDP to TM ICD
	#
	#Section 2.4.1 Control, State and Configuration
	#
	#Note that this has been updated by ADR-3.


	@XTP-119 @XTP-118 @Current @tests_sdp_tango_interface
	Scenario: Device startup
		Given I have an OFFLINE SDPSubarray device
		When the device is initialised
		Then the device should be OFF
		And obsState should be IDLE
		And adminMode should be ONLINE
		And healthState should be OK



	@XTP-120 @XTP-118 @Current @tests_sdp_tango_interface
	Scenario: AssignResources command succeeds
		Given I have an ONLINE SDPSubarray device
		When the device is OFF and obsState is IDLE
		And I call AssignResources
		Then the device should be ON
		And obsState should be IDLE
		And the configured Processing Blocks should be in the Config DB
		And the receiveAddresses attribute should return the expected value


	@XTP-121 @XTP-118 @Current @tests_sdp_tango_interface
	Scenario Outline: AssignResources command fails when device is not OFF
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		Then calling AssignResources raises tango.DevFailed

		Examples:
		|state_value|obs_state_value|
		|ON         |IDLE           |
		|ON         |READY          |
		|ON         |SCANNING       |


#
	@XTP-737 @XTP-118 @Current @tests_sdp_tango_interface
	Scenario: AssignResources command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When the device is OFF and obsState is IDLE
		And I call AssignResources with invalid JSON
		Then the device should be OFF
		And obsState should be IDLE



	@XTP-122 @XTP-118 @Current @tests_sdp_tango_interface
	Scenario: ReleaseResources command succeeds
		Given I have an ONLINE SDPSubarray device
		When the device is ON and obsState is IDLE
		And I call ReleaseResources
		Then the device should be OFF
		And obsState should be IDLE
		And the receiveAddresses attribute should return an empty JSON object



	@XTP-193 @XTP-118 @Current @tests_sdp_tango_interface
	Scenario Outline: ReleaseResources command fails when device is not ON or obsState is not IDLE
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		Then calling ReleaseResources raises tango.DevFailed

		Examples:
		|state_value|obs_state_value|
		|OFF        |IDLE           |
		|ON         |SCANNING       |
		|ON         |READY          |



	@XTP-123 @XTP-118 @Current @tests_sdp_tango_interface
	Scenario Outline: Configure command succeeds
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		And I call Configure
		Then obsState should be READY

		Examples:
		|state_value|obs_state_value|
		|ON         |IDLE           |
		|ON         |READY          |



	@XTP-738 @XTP-118 @Current @tests_sdp_tango_interface
	Scenario Outline: Configure command fails when device is not ON or obsState is not IDLE or READY
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		Then calling Configure raises tango.DevFailed

		Examples:
		|state_value|obs_state_value|
		|OFF        |IDLE           |
		|ON         |SCANNING       |



	@XTP-241 @XTP-118 @Current @tests_sdp_tango_interface
	Scenario Outline: Configure command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		And I call Configure with invalid JSON
		Then obsState should be IDLE

		Examples:
		|state_value|obs_state_value|
		|ON         |IDLE           |
		|ON         |READY          |



	@XTP-739 @XTP-118 @Current @tests_sdp_tango_interface
	Scenario: Reset command succeeds
		Given I have an ONLINE SDPSubarray device
		When the device is ON and obsState is READY
		And I call Reset
		Then obsState should be IDLE


	@XTP-740 @XTP-118 @Current
	Scenario Outline: Reset command fails when obsState is not READY
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		Then calling Reset raises tango.DevFailed

		Examples:
		|state_value|obs_state_value|
		|OFF        |IDLE           |
		|ON         |IDLE           |
		|ON         |SCANNING       |



	@XTP-191 @XTP-118 @Current
	Scenario: Scan command succeeds
		Given I have an ONLINE SDPSubarray device
		When the device is ON and obsState is READY
		And I call Scan
		Then obsState should be SCANNING



	@XTP-741 @XTP-118 @Current
	Scenario Outline: Scan command fails when obsState is not READY
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		Then calling Scan raises tango.DevFailed

		Examples:
		|state_value|obs_state_value|
		|OFF        |IDLE           |
		|ON         |IDLE           |
		|ON         |SCANNING       |



	@XTP-742 @XTP-118 @Current
	Scenario: Scan command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When the device is ON and obsState is READY
		And I call Scan with invalid JSON
		Then obsState should be READY



	@XTP-192 @XTP-118 @Current
	Scenario: EndScan command succeeds
		Given I have an ONLINE SDPSubarray device
		When the device is ON and obsState is SCANNING
		And I call EndScan
		Then obsState should be READY



	@XTP-743 @XTP-118 @Current
	Scenario Outline: EndScan command fails when obsState is not SCANNING
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		Then calling EndScan raises tango.DevFailed

		Examples:
		|state_value|obs_state_value|
		|OFF        |IDLE           |
		|ON         |IDLE           |
		|ON         |READY          |
