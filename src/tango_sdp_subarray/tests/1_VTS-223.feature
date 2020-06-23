@VTS-223
Feature: SDP Subarray Device
	#300-000000-029 rev 04 SDP to TM ICD
	#
	#Section 2.4.1 Control, State and Configuration
	#
	#Note that this has been updated by ADR-3.


	@XTP-119 @XTP-118 @XTP-895 @Current
	Scenario: Device startup
		Given I have an OFFLINE SDPSubarray device
		When the device is initialised
		Then the device should be OFF
		And obsState should be IDLE
		And adminMode should be ONLINE
		And healthState should be OK


	#This is a revised version of the test following the implementation of ADR-4 and ADR-10.
    # The check on the value of the receiveAddresses attribute has been added to this test.
	@XTP-896 @XTP-895 @Current
	Scenario: AssignResources command succeeds
		Given I have an ONLINE SDPSubarray device
		When the device is OFF and obsState is IDLE
		And I call AssignResources
		Then the device should be ON
		And obsState should be IDLE
		And the configured Processing Blocks should be in the Config DB
		And the receiveAddresses attribute should return the expected value


	@XTP-121 @XTP-118 @XTP-895 @Current
	Scenario Outline: AssignResources command fails when device is not OFF
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		Then calling AssignResources raises tango.DevFailed

		Examples:
		|state_value|obs_state_value|
		|ON         |IDLE           |
		|ON         |READY          |
		|ON         |SCANNING       |



	@XTP-737 @XTP-118 @XTP-895 @Current
	Scenario: AssignResources command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When the device is OFF and obsState is IDLE
		And I call AssignResources with invalid JSON
		Then the device should be OFF
		And obsState should be IDLE


	#This is a revised version of the test following the implementation of ADR-4 and and ADR-10.
   # The check on the value of the receiveAddresses attribute has been added to this test.
	@XTP-904 @XTP-895 @Current
	Scenario: ReleaseResources command succeeds
		Given I have an ONLINE SDPSubarray device
		When the device is ON and obsState is IDLE
		And I call ReleaseResources
		Then the device should be OFF
		And obsState should be IDLE
		And the receiveAddresses attribute should return an empty JSON object



	@XTP-193 @XTP-895 @XTP-118 @Current
	Scenario Outline: ReleaseResources command fails when device is not ON or obsState is not IDLE
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		Then calling ReleaseResources raises tango.DevFailed

		Examples:
		|state_value|obs_state_value|
		|OFF        |IDLE           |
		|ON         |SCANNING       |
		|ON         |READY          |


	#This is a revised version of the test following the implementation of ADR-4 and ADR-10.
    # It no longer contains a check on the value of the receiveAddresses attribute.
	@XTP-897 @XTP-895 @Current
	Scenario Outline: Configure command succeeds
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		And I call Configure
		Then obsState should be READY

		Examples:
		|state_value|obs_state_value|
		|ON         |IDLE           |
		|ON         |READY          |



	@XTP-738 @XTP-895 @XTP-118 @Current
	Scenario Outline: Configure command fails when device is not ON or obsState is not IDLE or READY
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		Then calling Configure raises tango.DevFailed

		Examples:
		|state_value|obs_state_value|
		|OFF        |IDLE           |
		|ON         |SCANNING       |



	@XTP-241 @XTP-895 @XTP-118 @Current
	Scenario Outline: Configure command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		And I call Configure with invalid JSON
		Then obsState should be IDLE
		And the receiveAddresses attribute should return an empty JSON object

		Examples:
		|state_value|obs_state_value|
		|ON         |IDLE           |
		|ON         |READY          |


	#This is a revised version of the test following the implementation of ADR-4 and ADR-10.
    # It no longer contains a check on the value of the receiveAddresses attribute.
	@XTP-905 @XTP-895 @Current
	Scenario: Reset command succeeds
		Given I have an ONLINE SDPSubarray device
		When the device is ON and obsState is READY
		And I call Reset
		Then obsState should be IDLE



	@XTP-740 @XTP-118 @XTP-895 @Current
	Scenario Outline: Reset command fails when obsState is not READY
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		Then calling Reset raises tango.DevFailed

		Examples:
		|state_value|obs_state_value|
		|OFF        |IDLE           |
		|ON         |IDLE           |
		|ON         |SCANNING       |



	@XTP-191 @XTP-118 @XTP-895 @Current
	Scenario: Scan command succeeds
		Given I have an ONLINE SDPSubarray device
		When the device is ON and obsState is READY
		And I call Scan
		Then obsState should be SCANNING



	@XTP-741 @XTP-118 @XTP-895 @Current
	Scenario Outline: Scan command fails when obsState is not READY
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		Then calling Scan raises tango.DevFailed

		Examples:
		|state_value|obs_state_value|
		|OFF        |IDLE           |
		|ON         |IDLE           |
		|ON         |SCANNING       |



	@XTP-742 @XTP-118 @XTP-895 @Current
	Scenario: Scan command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When the device is ON and obsState is READY
		And I call Scan with invalid JSON
		Then obsState should be READY



	@XTP-192 @XTP-895 @XTP-118 @Current
	Scenario: EndScan command succeeds
		Given I have an ONLINE SDPSubarray device
		When the device is ON and obsState is SCANNING
		And I call EndScan
		Then obsState should be READY



	@XTP-743 @XTP-895 @XTP-118 @Current
	Scenario Outline: EndScan command fails when obsState is not SCANNING
		Given I have an ONLINE SDPSubarray device
		When the device is <state_value> and obsState is <obs_state_value>
		Then calling EndScan raises tango.DevFailed

		Examples:
		|state_value|obs_state_value|
		|OFF        |IDLE           |
		|ON         |IDLE           |
		|ON         |READY          |



#	@XTP-842 @XTP-895 @XTP-118
#	Scenario: Tango device publishes custom attribute
#		Given I have an <device_type> device
#		And The device is configured to publish a <attribute_type> attribute
#		And The configuration database has a <attribute_type> value for the attribute
#		When I query the value of the <attribute_type> attribute from the <device_type> device using TANGO
#		Then The result is the same value as in the configuration database
#
#		Examples:
#		|device_type|attribute_type|
#		|ONLINE SDPSubarray |string|
#		|ONLINE SDPSubarray |int|
#		|ONLINE SDPSubarray |float|
#		|ONLINE SDPSubarray |float array|
#		|SDPMaster |string|
#		|SDPMaster |int|
#		|SDPMaster |float|


#	@XTP-843 @XTP-895 @XTP-118
#	Scenario: Tango device falls back for custom attribute
#		Given I have an <device_type> device
#		And The device is configured to publish a <attribute_type> attribute
#		And The configuration database does not have the value for the <attribute_type> attribute
#		When I query the value of the <attribute_type> attribute from the <device_type> device using TANGO
#		Then the result is a standard fall-back <attribute_type> value
#
#		Examples:
#		|device_type|attribute_type|
#		|ONLINE SDPSubarray |string|
#		|ONLINE SDPSubarray |int|
#		|ONLINE SDPSubarray |float|
#		|ONLINE SDPSubarray |float array|
#		|SDPMaster |string|
#		|SDPMaster |int|
#		|SDPMaster |float|


#	@XTP-844 @XTP-895 @XTP-118
#	Scenario: Tango device publishes changes to custom attribute
#		Given I have an <device_type> device
#		And The device is configured to publish a <attribute_type> attribute
#		And The configuration database has a <attribute_type> value for the attribute
#		When I change the value of the <attribute_type> attribute in the configuration database
#		And I query the value of the <attribute_type> attribute from the <device_type> device using TANGO
#		Then The result is the new <attribute_type> value as changed in the configuration database
#
#		Examples:
#		|device_type|attribute_type|
#		|ONLINE SDPSubarray |string|
#		|ONLINE SDPSubarray |int|
#		|ONLINE SDPSubarray |float|
#		|ONLINE SDPSubarray |float array|
#		|SDPMaster |string|
#		|SDPMaster |int|
#		|SDPMaster |float|


#	@XTP-872 @XTP-895 @XTP-118
#	Scenario: Receive addresses map set after AssignResources
#		Given I have an ONLINE SDPSubarray device implementing interface version 3
#		And The device is ON and obsState is EMPTY
#		When I call AssignResources with a scheduling block
#		And Wait for the obsState to be IDLE
#		Then The receive addresses map is set, with entries for every scan type


#	@XTP-877 @XTP-895 @XTP-118
#	Scenario: SDP utilises link map
#		Given An offline SDP subarray
#		And An AssignResources request for a scheduling block that has a link and channel map for every scan type
#		When The AssignRessources request is sent to SDP
#		Then SDP determines destination hosts and routes for every channel
#		And Configures networking as required
#		And Starts up and configures ingest processes for all scan types at the determined hosts
#
#
#	@XTP-878 @XTP-118 @XTP-895
#	Scenario: SDP utilises channel map
#		Given An idle SDP subarray with a scheduling block including a channel map for every scan type
#		When A scan type gets configured
#		And The scan gets started
#		Then Received visibilites are associated with the frequencies given in the channel map for the configured scan type