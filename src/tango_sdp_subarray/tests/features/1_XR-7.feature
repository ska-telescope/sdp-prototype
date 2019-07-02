#@XR-7
#Feature: ICD SDP-TM section 2.4.1.2.2 SDP Subarray State
#	#Document Number: 300-000000-029
#	#
#	#Revision & Date: Rev 04, 2019-03-15
#	#
#	#Requirement Text: 
#	#
#	#The SDP Subarray Devices follows the same ObsState states as the standard Subarray state model in [RD01]. Figure 8 is similar to the State Model in [RD01]. Reference [RD01] for detail descriptions of each state. A difference between the Subarray State Model and the SDP Subarray Node State Model is that the _configure_ transition from _READY_ to _CONFIGURING_ does not occur since SDP does not need to reconfigure between scans.
#	#
#	#All 16 SDP Subarray Devices are instantiated on startup of SDP with obsState = IDLE and adminMode = OFFLINE.
#	#
#	# 
#
#
#	@XTP-116 @XTP-115
#	Scenario: SDP Subarray device State transition from ready to scanning
#		Feature: transition the state
#
#		#this is a very bare-bones scenario and may be wrong. It is intended to provide simple proof of concept
#		Scenario: Scanning
#		    Given a Ready SDP State Device
#		    When the SDP State Device recieves the Run command
#		    Then the SDP State Device will transition to the Scanning State
#
#	#Test of the state transition for the AssignReources method
#	@XTP-117 @XTP-115
#	Scenario: SDP Subarray state transition for AssignReources
#		Given a ready SDPSubarray device
#		When the AssignResources command is called
#		Then The device state transitions to ON

Feature: SDPSubarray device
	The SDPSubarray Tango device

	Scenario: Assign Resources
		Given I have a subarray device
		When I call the command assign resources
		Then The obsState should be IDLE
		And The state should be ON


