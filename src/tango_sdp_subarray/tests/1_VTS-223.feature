@VTS-223
Feature: SDP Subarray Device
	#300-000000-029 rev 04 SDP to TM ICD
	#
	#Section 2.4.1 Control, State and Configuration

	
	@XTP-119 @XTP-118
	Scenario: Device startup
		Given I have an OFFLINE SDPSubarray device
		When the device is initialised
		Then State should be OFF
		And obsState should be IDLE
		And adminMode should be ONLINE
		And healthState should be OK
			

	
	@XTP-120 @XTP-118
	Scenario: AssignResources command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call AssignResources
		Then State should be ON
		And obsState should be IDLE
		And adminMode should be ONLINE
		And the configured Processing Blocks should be in the Config DB
			

	
	@XTP-121 @XTP-118
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
			

	
	@XTP-737 @XTP-118
	Scenario: AssignResources command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call AssignResources with invalid JSON
		Then obsState should be IDLE
			

	
	@XTP-122 @XTP-118
	Scenario: ReleaseResources command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call ReleaseResources
		Then State should be OFF
		And obsState should be IDLE
		And adminMode should be ONLINE
			

	
	@XTP-193 @XTP-118
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
			

	
	@XTP-123 @XTP-118
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
			

	
	@XTP-738 @XTP-118
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
			

	
	@XTP-241 @XTP-118
	Scenario: Configure command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When obsState is IDLE
		And I call Configure with invalid JSON
		Then obsState should be IDLE
		And the receiveAddresses attribute should return an empty JSON object
			

	
	@XTP-739 @XTP-118
	Scenario: Reset command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call Reset
		Then obsState should be IDLE
		And the receiveAddresses attribute should return an empty JSON object
			

	
	@XTP-740 @XTP-118
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
			

	
	@XTP-191 @XTP-118
	Scenario: Scan command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call Scan
		Then obsState should be SCANNING
			

	
	@XTP-741 @XTP-118
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
			

	
	@XTP-742 @XTP-118
	Scenario: Scan command fails with invalid JSON
		Given I have an ONLINE SDPSubarray device
		When obsState is READY
		And I call Scan with invalid JSON
		Then obsState should be READY
			

	
	@XTP-192 @XTP-118
	Scenario: EndScan command succeeds
		Given I have an ONLINE SDPSubarray device
		When obsState is SCANNING
		And I call EndScan
		Then obsState should be READY
		
			

	
	@XTP-743 @XTP-118
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
		