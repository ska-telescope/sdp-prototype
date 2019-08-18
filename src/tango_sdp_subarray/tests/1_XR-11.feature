@XR-11
Feature: SDPSubarray device
	#300-000000-029 rev 04 SDP to TM ICD
	#
	#Section 2.4.1 Control, State and Configuration


	@XTP-119 @XTP-118
	Scenario: Device Startup
		Given I have an OFFLINE SDPSubarray device
		When the device is initialised
		Then State should be OFF
		And obsState should be IDLE
		And adminMode should be OFFLINE
		And healthState should be OK


	# When assigning resources to the SDPSubarray device, the device state transitions must follow the [Subarray State Model|https://confluence.skatelescope.org/display/SE/Subarray+State+Model] and behaviour defined for the [Subarray Device interface description|https://confluence.skatelescope.org/pages/viewpage.action?pageId=74716479].
	#
	# This requires that after successful assignment of resources no exceptions are thrown, device state is ON, the obsState remains in IDLE, and the adminMode is ONLINE.
	@XTP-120 @XTP-118 @AssignResources @successful
	Scenario: AssignResources command successful
		Given I have an ONLINE SDPSubarray device
		When I call AssignResources
		Then State should be ON
		And obsState should be IDLE
		And adminMode should be ONLINE



	@XTP-121 @XTP-118 @AssignResources @fail
	Scenario Outline: AssignResources fails when obsState is not IDLE
		Given I have an ONLINE SDPSubarray device
		When obsState is <value>
		Then calling AssignResources raises tango.DevFailed

		Examples:
		| value       |
		| CONFIGURING |
		| READY       |
		| SCANNING    |
		| ABORTED     |
		| FAULT       |



	@XTP-122 @XTP-118 @ReleaseResources @successful
	Scenario: ReleaseResources command successful
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call ReleaseResources
		Then State should be OFF
		And obsState should be IDLE
		And adminMode should be ONLINE or MAINTENANCE



	@XTP-193 @XTP-118 @ReleaseResources @fail
	Scenario Outline: ReleaseResources fails when obsState is not IDLE
		Given I have an ONLINE SDPSubarray device
		When obsState is <value>
		Then calling ReleaseResources raises tango.DevFailed

		Examples:
		| value       |
		| CONFIGURING |
		| READY       |
		| SCANNING    |
		| ABORTED     |
		| FAULT       |


	# Tests successful execution of the SDP Subarray Configure command.
	@XTP-123 @XTP-118 @Configure @successful
	Scenario: Configure command successful
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call Configure
		Then obsState should be READY
		And The receiveAddresses attribute returns expected values



	# Tests SDPSubarray Configure command with invalid JSON.
	@XTP-241 @XTP-118
	Scenario: Configure command with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call Configure with invalid JSON
		Then obsState should be FAULT
		And The receiveAddresses attribute should return an empty JSON object



	#Test that the SDPSubarray {{ConfigureScan}} command executes successfully and updates the obsState attribute as expected.
	@XTP-176 @XTP-118
	Scenario: ConfigureScan command successful
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call ConfigureScan
		Then obsState should be READY



	@XTP-191 @XTP-118
	Scenario: StartScan command successful
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call StartScan
		Then obsState should be SCANNING



	@XTP-192 @XTP-118
	Scenario: EndScan command successful
		Given I have an ONLINE SDPSubarray device
		When obsState is SCANNING
		And I call EndScan
		Then obsState should be READY
		And The receiveAddresses attribute should return an empty JSON object
