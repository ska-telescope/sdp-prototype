@VTS-223
Feature: SDP Subarray Device
	#300-000000-029 rev 04 SDP to TM ICD
	#
	#Section 2.4.1 Control, State and Configuration
	#
	#Note that this has been updated by ADR-3.


	@XTP-119 @XTP-118 @Current
	Scenario: Device is initialised in the correct state
		Given I have an SDPSubarray device
		When the device is initialised
		Then the state should be OFF
		And obsState should be EMPTY
		And adminMode should be ONLINE
		And healthState should be OK


	#Required commands are present and they have the correct argument type and return type.
	@XTP-969 @XTP-118 @Current
	Scenario Outline: Command is present and has correct input and output types
		Given I have an SDPSubarray device
		When the device is initialised
		Then the input type of <command> should be <input_type>
		And the output type of <command> should be <output_type>

		Examples:
		| command          | input_type | output_type |
		| On               | DevVoid    | DevVoid     |
		| Off              | DevVoid    | DevVoid     |
		| AssignResources  | DevString  | DevVoid     |
		| ReleaseResources | DevVoid    | DevVoid     |
		| Configure        | DevString  | DevVoid     |
		| End              | DevVoid    | DevVoid     |
		| Scan             | DevString  | DevVoid     |
		| EndScan          | DevVoid    | DevVoid     |
		| Abort            | DevVoid    | DevVoid     |
		| ObsReset         | DevVoid    | DevVoid     |
		| Restart          | DevVoid    | DevVoid     |


	#All commands, apart from On, are rejected when the state is OFF.
	@XTP-949 @XTP-118 @Current
	Scenario Outline: Command is rejected when the state is OFF
		Given I have an SDPSubarray device
		When the state is OFF
		Then calling <command> should raise tango.DevFailed

		Examples:
		| command          |
		| Off              |
		| AssignResources  |
		| ReleaseResources |
		| Configure        |
		| End              |
		| Scan             |
		| EndScan          |
		| Abort            |
		| ObsReset         |
		| Restart          |


	#On command succeeds when the state is OFF.
	@XTP-917 @XTP-118 @Current
	Scenario: On command succeeds
		Given I have an SDPSubarray device
		When the state is OFF
		And I call On
		Then the state should be ON
		And obsState should be EMPTY


	#Off command succeeds in any obsState.
	@XTP-918 @XTP-118 @Current
	Scenario Outline: Off command succeeds
		Given I have an SDPSubarray device
		When obsState is <initial_obs_state>
		And I call Off
		Then the state should be OFF
		And obsState should be EMPTY

		Examples:
		| initial_obs_state |
		| EMPTY             |
		| RESOURCING        |
		| IDLE              |
		| CONFIGURING       |
		| READY             |
		| SCANNING          |
		| ABORTING          |
		| ABORTED           |
		| FAULT             |
		| RESETTING         |
		| RESTARTING        |


	#Commands succeed in obsStates where they are allowed and transition to the correct final obsState.
	@XTP-971 @XTP-118 @Current
	Scenario Outline: Command succeeds in allowed obsState
		Given I have an SDPSubarray device
		When obsState is <initial_obs_state>
		And I call <command>
		Then obsState should be <final_obs_state>

		Examples:
		| command          | initial_obs_state | final_obs_state |
		| AssignResources  | EMPTY             | IDLE            |
		| ReleaseResources | IDLE              | EMPTY           |
		| Configure        | IDLE              | READY           |
		| Configure        | READY             | READY           |
		| End              | READY             | IDLE            |
		| Scan             | READY             | SCANNING        |
		| EndScan          | SCANNING          | READY           |
		| Abort            | IDLE              | ABORTED         |
		| Abort            | CONFIGURING       | ABORTED         |
		| Abort            | READY             | ABORTED         |
		| Abort            | SCANNING          | ABORTED         |
		| Abort            | RESETTING         | ABORTED         |
		| ObsReset         | ABORTED           | IDLE            |
		| ObsReset         | FAULT             | IDLE            |
		| Restart          | ABORTED           | EMPTY           |
		| Restart          | FAULT             | EMPTY           |


	#Commands are rejected when called in obsStates where they are not allowed.
	@XTP-972 @XTP-118 @Current
	Scenario Outline: Command is rejected in disallowed obsState
		Given I have an SDPSubarray device
		When obsState is <initial_obs_state>
		Then calling <command> should raise tango.DevFailed

		Examples:
		| command          | initial_obs_state |
		| AssignResources  | RESOURCING        |
		| AssignResources  | IDLE              |
		| AssignResources  | CONFIGURING       |
		| AssignResources  | READY             |
		| AssignResources  | SCANNING          |
		| AssignResources  | ABORTING          |
		| AssignResources  | ABORTED           |
		| AssignResources  | FAULT             |
		| AssignResources  | RESETTING         |
		| AssignResources  | RESTARTING        |
		| ReleaseResources | EMPTY             |
		| ReleaseResources | RESOURCING        |
		| ReleaseResources | CONFIGURING       |
		| ReleaseResources | READY             |
		| ReleaseResources | SCANNING          |
		| ReleaseResources | ABORTING          |
		| ReleaseResources | ABORTED           |
		| ReleaseResources | FAULT             |
		| ReleaseResources | RESETTING         |
		| ReleaseResources | RESTARTING        |
		| Configure        | EMPTY             |
		| Configure        | RESOURCING        |
		| Configure        | CONFIGURING       |
		| Configure        | SCANNING          |
		| Configure        | ABORTING          |
		| Configure        | ABORTED           |
		| Configure        | FAULT             |
		| Configure        | RESETTING         |
		| Configure        | RESTARTING        |
		| End              | EMPTY             |
		| End              | RESOURCING        |
		| End              | IDLE              |
		| End              | CONFIGURING       |
		| End              | SCANNING          |
		| End              | ABORTING          |
		| End              | ABORTED           |
		| End              | FAULT             |
		| End              | RESETTING         |
		| End              | RESTARTING        |
		| Scan             | EMPTY             |
		| Scan             | RESOURCING        |
		| Scan             | IDLE              |
		| Scan             | CONFIGURING       |
		| Scan             | SCANNING          |
		| Scan             | ABORTING          |
		| Scan             | ABORTED           |
		| Scan             | FAULT             |
		| Scan             | RESETTING         |
		| Scan             | RESTARTING        |
		| EndScan          | EMPTY             |
		| EndScan          | RESOURCING        |
		| EndScan          | IDLE              |
		| EndScan          | CONFIGURING       |
		| EndScan          | READY             |
		| EndScan          | ABORTING          |
		| EndScan          | ABORTED           |
		| EndScan          | FAULT             |
		| EndScan          | RESETTING         |
		| EndScan          | RESTARTING        |
		| Abort            | EMPTY             |
		| Abort            | RESOURCING        |
		| Abort            | ABORTING          |
		| Abort            | ABORTED           |
		| Abort            | FAULT             |
		| Abort            | RESTARTING        |
		| ObsReset         | EMPTY             |
		| ObsReset         | RESOURCING        |
		| ObsReset         | IDLE              |
		| ObsReset         | CONFIGURING       |
		| ObsReset         | READY             |
		| ObsReset         | SCANNING          |
		| ObsReset         | ABORTING          |
		| ObsReset         | RESETTING         |
		| ObsReset         | RESTARTING        |
		| Restart          | EMPTY             |
		| Restart          | RESOURCING        |
		| Restart          | IDLE              |
		| Restart          | CONFIGURING       |
		| Restart          | READY             |
		| Restart          | SCANNING          |
		| Restart          | ABORTING          |
		| Restart          | RESETTING         |
		| Restart          | RESTARTING        |


	#Commands that take a JSON configuration string are rejected when it is invalid.
	@XTP-965 @XTP-118 @Current
	Scenario Outline: Command is rejected with an invalid JSON configuration
		Given I have an SDPSubarray device
		When obsState is <initial_obs_state>
		Then calling <command> with an invalid JSON configuration should raise tango.DevFailed

		Examples:
		| command         | initial_obs_state |
		| AssignResources | EMPTY             |
		| Configure       | IDLE              |
		| Configure       | READY             |
		| Scan            | READY             |



	@XTP-120 @XTP-118 @Current
	Scenario: AssignResources command configures processing blocks and sets receive addresses
		Given I have an SDPSubarray device
		When obsState is EMPTY
		And I call AssignResources
		Then the processing blocks should be in the config DB
		And receiveAddresses should have the expected value



	@XTP-122 @XTP-118 @Current
	Scenario: ReleaseResources command clears receive addresses
		Given I have an SDPSubarray device
		When obsState is IDLE
		And I call ReleaseResources
		Then receiveAddresses should be an empty JSON object
