@VTS-223
Feature: SDP Subarray Device
	#300-000000-029 rev 04 SDP to TM ICD
	#
	#Section 2.4.1 Control, State and Configuration
	#
	#Note that this has been updated by ADR-3.


	@XTP-119 @XTP-118 @Current
	Scenario: Device is initialised in the correct state
		Given I have an OFFLINE SDPSubarray device
		When the device is initialised
		Then the state should be OFF
		And obsState should be EMPTY
		And adminMode should be ONLINE
		And healthState should be OK


	#Required commands are present and they have the correct argument type and return type.
	@XTP-969 @XTP-118 @Current
	Scenario Outline: Command is present and has correct input and output types
		Given I have an OFFLINE SDPSubarray Device
		When the device is initialised
		Then the input type of <command> should be <input_type>
		And the output type of <command> should be <output_type>

		Examples:
		|command         |input_type|output_type|
		|On              |DevVoid   |DevVoid    |
		|Off             |DevVoid   |DevVoid    |
		|AssignResources |DevString |DevVoid    |
		|ReleaseResources|DevVoid   |DevVoid    |
		|Configure       |DevString |DevVoid    |
		|End             |DevVoid   |DevVoid    |
		|Scan            |DevString |DevVoid    |
		|EndScan         |DevVoid   |DevVoid    |
		|Abort           |DevVoid   |DevVoid    |
		|ObsReset        |DevVoid   |DevVoid    |
		|Restart         |DevVoid   |DevVoid    |


	#All commands, apart from On, are rejected when the state is OFF.
	@XTP-949 @XTP-118 @Current
	Scenario Outline: Command is rejected when the state is OFF
		Given I have an ONLINE SDPSubarray device
		When the state is OFF
		Then calling <command> should raise tango.DevFailed

		Examples:
		|command         |
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


	#On command succeeds when the state is OFF.
	@XTP-917 @XTP-118 @Current
	Scenario: On command succeeds
		Given I have an ONLINE SDPSubarray device
		When the state is OFF
		And I call On
		Then the state should be ON
		And obsState should be EMPTY


	#Off command succeeds in any obsState.
	@XTP-918 @XTP-118 @Current
	Scenario Outline: Off command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is <initial_obs_state>
		And I call Off
		Then the state should be OFF
		And obsState should be EMPTY

		Examples:
		|initial_obs_state|
		|EMPTY            |
		|IDLE             |
		|READY            |
		|SCANNING         |
		|ABORTED          |
		|FAULT            |


	#Commands succeed in obsStates where they are allowed and transition to the correct final obsState.
	@XTP-971 @XTP-118 @Current
	Scenario Outline: Command succeeds in allowed obsState
		Given I have an ONLINE SDPSubarray device
		When obsState is <initial_obs_state>
		And I call <command>
		Then obsState should be <final_obs_state>

		Examples:
		|command         |initial_obs_state|final_obs_state|
		|AssignResources |EMPTY            |IDLE           |
		|ReleaseResources|IDLE             |EMPTY          |
		|Configure       |IDLE             |READY          |
		|Configure       |READY            |READY          |
		|End             |READY            |IDLE           |
		|Scan            |READY            |SCANNING       |
		|EndScan         |SCANNING         |READY          |
		|Abort           |IDLE             |ABORTED        |
		|Abort           |SCANNING         |ABORTED        |
		|Abort           |READY            |ABORTED        |
		|ObsReset        |ABORTED          |IDLE           |
		|ObsReset        |FAULT            |IDLE           |
		|Restart         |ABORTED          |EMPTY          |
		|Restart         |FAULT            |EMPTY          |


	#Commands are rejected when called in obsStates where they are not allowed.
	@XTP-972 @XTP-118 @Current
	Scenario Outline: Command is rejected in disallowed obsState
		Given I have an ONLINE SDPSubarray device
		When obsState is <initial_obs_state>
		Then calling <command> should raise tango.DevFailed

		Examples:
		|command         |initial_obs_state|
		|AssignResources |IDLE             |
		|AssignResources |READY            |
		|AssignResources |SCANNING         |
		|AssignResources |ABORTED          |
		|AssignResources |FAULT            |
		|ReleaseResources|EMPTY            |
		|ReleaseResources|READY            |
		|ReleaseResources|SCANNING         |
		|ReleaseResources|ABORTED          |
		|ReleaseResources|FAULT            |
		|Configure       |EMPTY            |
		|Configure       |SCANNING         |
		|Configure       |ABORTED          |
		|Configure       |FAULT            |
		|End             |EMPTY            |
		|End             |IDLE             |
		|End             |SCANNING         |
		|End             |ABORTED          |
		|End             |FAULT            |
		|Scan            |EMPTY            |
		|Scan            |IDLE             |
		|Scan            |SCANNING         |
		|Scan            |ABORTED          |
		|Scan            |FAULT            |
		|EndScan         |EMPTY            |
		|EndScan         |IDLE             |
		|EndScan         |READY            |
		|EndScan         |ABORTED          |
		|EndScan         |FAULT            |
		|Abort           |EMPTY            |
		|Abort           |ABORTED          |
		|Abort           |FAULT            |
		|ObsReset        |EMPTY            |
		|ObsReset        |IDLE             |
		|ObsReset        |READY            |
		|ObsReset        |SCANNING         |
		|Restart         |EMPTY            |
		|Restart         |IDLE             |
		|Restart         |READY            |
		|Restart         |SCANNING         |


	#Commands that take a JSON configuration string fail when it is invalid and transition to obsState = FAULT.
	@XTP-965 @XTP-118 @Current
	Scenario Outline: Command fails with an invalid JSON configuration
		Given I have an ONLINE SDPSubarray device
		When obsState is <initial_obs_state>
		And I call <command> with an invalid JSON configuration
		Then obsState should be FAULT

		Examples:
		|command        |initial_obs_state|
		|AssignResources|EMPTY            |
		|Configure      |IDLE             |
		|Configure      |READY            |
		|Scan           |READY            |



	@XTP-120 @XTP-118 @Current
	Scenario: AssignResources command configures processing blocks and sets receive addresses
		Given I have an ONLINE SDPSubarray device
		When obsState is EMPTY
		And I call AssignResources
		Then the processing blocks should be in the config DB
		And the receiveAddresses attribute should return the expected value



	@XTP-122 @XTP-118 @Current
	Scenario: ReleaseResources command clears receive addresses
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call ReleaseResources
		Then the receiveAddresses attribute should return an empty JSON object


	#This tests a corner case of the state model for SDP. The state model allows ObsReset to start a transition from FAULT to IDLE, but this is impossible is the subarray does not have a scheduling block instance. This situation can arise if AssignResources fails. In this case the subarray transitions to RESETTING then goes back to FAULT.
	@XTP-950 @XTP-118 @Current
	Scenario: ObsReset command fails if an SBI is not configured
		Given I have an ONLINE SDPSubarray device
		When obsState is EMPTY
		And I call AssignResources with an invalid JSON configuration
		Then calling ObsReset should raise tango.DevFailed
		And obsState should be FAULT
