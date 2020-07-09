@VTS-223
Feature: SDP Subarray Device
	#300-000000-029 rev 04 SDP to TM ICD
	#
	#Section 2.4.1 Control, State and Configuration
	#
	#Note that this has been updated by ADR-3.

	#Revised test to incorporate state transitions from ADR-8
	@XTP-916 @XTP-895 @Current
	Scenario: Device startup
		Given I have an OFFLINE SDPSubarray device
		When the device is initialised
		Then the state should be OFF
		And obsState should be EMPTY
		And adminMode should be ONLINE
		And healthState should be OK


	#New test for ADR-8.
	@XTP-949 @XTP-895
	Scenario Outline: Commands fail when the state is OFF
		Given I have an ONLINE SDPSubarray device
		When the state is OFF
		Then calling <command_name> raises tango.DevFailed

		Examples:
		|command_name    |
		|Off             |
		|AssignResources |
		|ReleaseResources|
		|Configure       |
		|End             |
		|Scan            |
		|EndScan         |
		|Abort           |
		|ObsReset        |
		|Restart         |


	#New test conforming to ADR-8
	@XTP-917 @XTP-895
	Scenario: On command succeeds
		Given I have an ONLINE SDPSubarray device
		When the state is OFF
		And I call On
		Then the state should be ON
		And obsState should be EMPTY


	#New test conforming to ADR-8
	@XTP-918 @XTP-895
	Scenario Outline: Off command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is <obs_state_value>
		And I call Off
		Then the state should be OFF
		And obsState should be EMPTY

		Examples:
		|obs_state_value|
		|EMPTY          |
		|IDLE           |
		|READY          |
		|SCANNING       |
		|ABORTED        |
		|FAULT          |


	#This is a revised version of the test following the implementation of --ADR-4-- and --ADR-10--. The check on the value of the receiveAddresses attribute has been added to this test.
	#
	#Revised to include state transitions agreed in -ADR-8-
	@XTP-896 @XTP-895 @Current
	Scenario: AssignResources command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is EMPTY
		And I call AssignResources
		Then obsState should be IDLE
		And the configured Processing Blocks should be in the Config DB
		And the receiveAddresses attribute should return the expected value


	#Updated to include ADR-8 state model
	@XTP-926 @XTP-895 @Current
	Scenario Outline: AssignResources command fails when obsState is not EMPTY
		Given I have an ONLINE SDPSubarray device
		When obsState is <obs_state_value>
		Then calling AssignResources raises tango.DevFailed

		Examples:
		|obs_state_value|
		|IDLE           |
		|READY          |
		|SCANNING       |
		|ABORTED        |
		|FAULT          |


	#Revised for state transitions from ADR-8
	@XTP-923 @XTP-895 @Current
	Scenario: AssignResources command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When obsState is EMPTY
		And I call AssignResources with invalid JSON
		Then obsState should be FAULT


	#This is a revised version of the test following the implementation of -ADR-4- and and -ADR-10-. The check on the value of the receiveAddresses attribute has been added to this test.
	#
	#Revised to include state model from ADR-8
	@XTP-904 @XTP-895 @Current
	Scenario: ReleaseResources command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call ReleaseResources
		Then obsState should be EMPTY
		And the receiveAddresses attribute should return an empty JSON object


	#Revised for state model from ADR-8
	@XTP-928 @XTP-895 @Current
	Scenario Outline: ReleaseResources command fails when obsState is not IDLE
		Given I have an ONLINE SDPSubarray device
		When obsState is <obs_state_value>
		Then calling ReleaseResources raises tango.DevFailed

		Examples:
		|obs_state_value|
		|EMPTY          |
		|READY          |
		|SCANNING       |
		|ABORTED        |
		|FAULT          |


	#This is a revised version of the test following the implementation of ADR-4 and ADR-10. It no longer contains a check on the value of the receiveAddresses attribute.
	@XTP-897 @XTP-895 @Current
	Scenario Outline: Configure command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is <obs_state_value>
		And I call Configure
		Then obsState should be READY

		Examples:
		|obs_state_value|
		|IDLE           |
		|READY          |



	#Revised to match state model from ADR-8
	@XTP-930 @XTP-895 @Current
	Scenario Outline: Configure command fails when obsState is not IDLE or READY
		Given I have an ONLINE SDPSubarray device
		When obsState is <obs_state_value>
		Then calling Configure raises tango.DevFailed

		Examples:
		|obs_state_value|
		|EMPTY          |
		|SCANNING       |
		|ABORTED        |
		|FAULT          |



	@XTP-241 @XTP-895 @XTP-118 @Current
	Scenario Outline: Configure command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When obsState is <obs_state_value>
		And I call Configure with invalid JSON
		Then obsState should be FAULT

		Examples:
		|obs_state_value|
		|IDLE           |
		|READY          |


	#This is a revised version of the test following the implementation of -ADR-4- and -ADR-10-. It no longer contains a check on the value of the receiveAddresses attribute.
	#
	#Revised from previous Reset command to follow ADR-8
	@XTP-905 @XTP-895 @Current
	Scenario: End command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call End
		Then obsState should be IDLE


	#New End command with states conforming to ADR-8
	@XTP-931 @XTP-895 @Current
	Scenario Outline: End command fails when obsState is not READY
		Given I have an ONLINE SDPSubarray device
		When obsState is <obs_state_value>
		Then calling End raises tango.DevFailed

		Examples:
		|obs_state_value|
		|EMPTY          |
		|IDLE           |
		|SCANNING       |
		|ABORTED        |
		|FAULT          |



	@XTP-191 @XTP-895 @XTP-118 @Current
	Scenario: Scan command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call Scan
		Then obsState should be SCANNING


	#Revised to match states from ADR-8
	@XTP-932 @XTP-895 @Current
	Scenario Outline: Scan command fails when obsState is not READY
		Given I have an ONLINE SDPSubarray device
		When obsState is <obs_state_value>
		Then calling Scan raises tango.DevFailed

		Examples:
		|obs_state_value|
		|EMPTY          |
		|IDLE           |
		|SCANNING       |
		|ABORTED        |
		|FAULT          |



	@XTP-742 @XTP-895 @XTP-118 @Current
	Scenario: Scan command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call Scan with invalid JSON
		Then obsState should be FAULT



	@XTP-192 @XTP-895 @XTP-118 @Current
	Scenario: EndScan command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is SCANNING
		And I call EndScan
		Then obsState should be READY



	#Revised for state model conforming to ADR-8
	@XTP-934 @XTP-895 @Current
	Scenario Outline: EndScan command fails when obsState is not SCANNING
		Given I have an ONLINE SDPSubarray device
		When obsState is <obs_state_value>
		Then calling EndScan raises tango.DevFailed

		Examples:
		|obs_state_value|
		|EMPTY          |
		|IDLE           |
		|READY          |
		|ABORTED        |
		|FAULT          |


	#New command conforming to ADR-8
	@XTP-935 @XTP-895
	Scenario Outline: Abort command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is <obs_state_value>
		And I call Abort
		Then obsState should be ABORTED

		Examples:
		|obs_state_value|
		|IDLE           |
		|SCANNING       |
		|READY          |


	#New command conforming to ADR-8
	@XTP-936 @XTP-895
	Scenario Outline: ObsReset command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is <obs_state_value>
		And I call ObsReset
		Then obsState should be IDLE

		Examples:
		|obs_state_value|
		|ABORTED        |
		|FAULT          |


	#New for ADR-8.
	#
	#This tests a corner case of the state model for SDP. The state model allows ObsReset to start a transition from FAULT to IDLE, but this is impossible is the subarray does not have a scheduling block instance. This situation can arise if AssignResources fails. In this case the subarray transitions to RESETTING then goes back to FAULT.
	@XTP-950 @XTP-895
	Scenario: ObsReset command fails if an SBI is not configured
		Given I have an ONLINE SDPSubarray device
		When obsState is EMPTY
		And I call AssignResources with invalid JSON
		Then calling ObsReset raises tango.DevFailed
		And obsState should be FAULT


	#New command conforming to ADR-8
	@XTP-937 @XTP-895
	Scenario Outline: Restart command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is <obs_state_value>
		And I call Restart
		Then obsState should be EMPTY

		Examples:
		|obs_state_value|
		|ABORTED        |
		|FAULT          |



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
#
#	#{color:#205081}*Given* {color}I have an{color:#707070} <device_type>{color} device
#	# {color:#205081}*And* {color}The device is configured to publish a {color:#707070}<attribute_type>{color} attribute
#	# {color:#205081}*And* {color}The configuration database does not have the value for the {color:#707070}<attribute_type>{color} attribute
#	# {color:#205081}*When* {color}I query the value of the{color:#707070} <attribute_type>{color} attribute from the {color:#707070}<device_type>{color} device using TANGO
#	# {color:#205081}*Then* {color}the result is a standard fall-back {color:#707070}<attribute_type>{color} value
#	#
#	#{color:#205081}*Examples*{color}:
#	#|device_type|attribute_type|
#	#|ONLINE SDPSubarray|string|
#	#|ONLINE SDPSubarray|int|
#	#|ONLINE SDPSubarray|float|
#	#|ONLINE SDPSubarray|float array|
#	#|SDPMaster|string|
#	#|SDPMaster|int|
#	#|SDPMaster|float|
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
#
#
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
#
#
#	@XTP-872 @XTP-895 @XTP-118
#	Scenario: Receive addresses map set after AssignResources
#		Given I have an ONLINE SDPSubarray device implementing interface version 3
#		And The device is ON and obsState is EMPTY
#		When I call AssignResources with a scheduling block
#		And Wait for the obsState to be IDLE
#		Then The receive addresses map is set, with entries for every scan type
#
#
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
#	@XTP-878 @XTP-895 @XTP-118
#	Scenario: SDP utilises channel map
#		Given An idle SDP subarray with a scheduling block including a channel map for every scan type
#		When A scan type gets configured
#		And The scan gets started
#		Then Received visibilites are associated with the frequencies given in the channel map for the configured scan type