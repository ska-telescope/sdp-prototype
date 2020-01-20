@XR-11
Feature: SDPSubarray device

	@XTP-119 @XTP-118 @startup @success
	Scenario: Device Startup
		Given I have an OFFLINE SDPSubarray device
		When the device is initialised
		Then State should be OFF
		And obsState should be IDLE
		And adminMode should be ONLINE
		And healthState should be OK

	@XTP-120 @XTP-118 @AssignResources @success
	Scenario: AssignResources command successful
		Given I have an ONLINE SDPSubarray device
		When I call AssignResources
		Then State should be ON
		And obsState should be IDLE
		And adminMode should be ONLINE

	@XTP-121 @XTP-118 @AssignResources @failure
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

	@XTP-122 @XTP-118 @ReleaseResources @success
	Scenario: ReleaseResources command successful
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call ReleaseResources
		Then State should be OFF
		And obsState should be IDLE
		And adminMode should be ONLINE or MAINTENANCE

	@XTP-193 @XTP-118 @ReleaseResources @failure
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

	@XTP-123 @XTP-118 @Configure @success
	Scenario: Configure command successful
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call Configure
		Then obsState should be READY
		And the configured Processing Blocks should be in the Config DB
		And the receiveAddresses attribute should return the expected value

	@XTP-241 @XTP-118 @Configure @failure
	Scenario: Configure command with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call Configure with invalid JSON
		Then obsState should be IDLE
		And the receiveAddresses attribute should return an empty JSON object

	@XTP-176 @XTP-118 @ConfigureScan @success
	Scenario: ConfigureScan command successful
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call ConfigureScan
		Then obsState should be READY

	@XTP-191 @XTP-118 @Scan @success
	Scenario: Scan command successful
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call Scan
		Then obsState should be SCANNING

	@XTP-192 @XTP-118 @EndScan @success
	Scenario: EndScan command successful
		Given I have an ONLINE SDPSubarray device
		When obsState is SCANNING
		And I call EndScan
		Then obsState should be READY
		And the receiveAddresses attribute should return an empty JSON object

	@XTP-383 @XTP-118 @EndSB @success
	Scenario: EndSB command successful
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call EndSB
		Then obsState should be IDLE
