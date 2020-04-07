Feature: SDPSubarray device

	# Startup scenario

	@startup @success
	Scenario: Device startup
		Given I have an OFFLINE SDPSubarray device
		When the device is initialised
		Then State should be OFF
		And obsState should be IDLE
		And adminMode should be ONLINE
		And healthState should be OK

	# AssignResources scenarios

	@AssignResources @success
	Scenario: AssignResources command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call AssignResources
		Then State should be ON
		And obsState should be IDLE
		And adminMode should be ONLINE
		And the configured Processing Blocks should be in the Config DB


	@AssignResources @failure
	Scenario Outline: AssignResources command fails when obsState is not IDLE
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


	@AssignResources @failure
	Scenario: AssignResources command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call AssignResources with invalid JSON
		Then obsState should be IDLE

	# ReleaseResources scenarios

	@ReleaseResources @success
	Scenario: ReleaseResources command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call ReleaseResources
		Then State should be OFF
		And obsState should be IDLE
		And adminMode should be ONLINE


	@ReleaseResources @failure
	Scenario Outline: ReleaseResources command fails when obsState is not IDLE
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

	# Configure scenarios

	@Configure @success
	Scenario Outline: Configure command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is <value>
		And I call Configure
		Then obsState should be READY
		And the receiveAddresses attribute should return the expected value

		Examples:
		| value |
		| IDLE  |
		| READY |


	@Configure @failure
	Scenario Outline: Configure command fails when obsState is not IDLE or READY
		Given I have an ONLINE SDPSubarray device
		When obsState is <value>
		Then calling Configure raises tango.DevFailed

		Examples:
		| value       |
		| CONFIGURING |
		| SCANNING    |
		| ABORTED     |
		| FAULT       |


	@Configure @failure
	Scenario: Configure command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call Configure with invalid JSON
		Then obsState should be IDLE
		And the receiveAddresses attribute should return an empty JSON object

	# Reset scenarios

	@Reset @success
	Scenario: Reset command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call Reset
		Then obsState should be IDLE
		And the receiveAddresses attribute should return an empty JSON object


	@Reset @failure
	Scenario Outline: Reset command fails when obsState is not READY
		Given I have an ONLINE SDPSubarray device
		When obsState is <value>
		Then calling Scan raises tango.DevFailed

		Examples:
		| value       |
		| CONFIGURING |
		| SCANNING    |
		| IDLE        |
		| ABORTED     |
		| FAULT       |

	# Scan scenarios

	@Scan @success
	Scenario: Scan command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call Scan
		Then obsState should be SCANNING


	@Scan @failure
	Scenario Outline: Scan command fails when obsState is not READY
		Given I have an ONLINE SDPSubarray device
		When obsState is <value>
		Then calling Scan raises tango.DevFailed

		Examples:
		| value       |
		| CONFIGURING |
		| IDLE        |
		| SCANNING    |
		| ABORTED     |
		| FAULT       |


	@Scan @failure
	Scenario: Scan command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call Scan with invalid JSON
		Then obsState should be READY

	# EndScan scenarios

	@EndScan @success
	Scenario: EndScan command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is SCANNING
		And I call EndScan
		Then obsState should be READY


	@EndScan @failure
	Scenario Outline: EndScan command fails when obsState is not SCANNING
		Given I have an ONLINE SDPSubarray device
		When obsState is <value>
		Then calling EndScan raises tango.DevFailed

		Examples:
		| value       |
		| CONFIGURING |
		| IDLE        |
		| READY       |
		| ABORTED     |
		| FAULT       |
