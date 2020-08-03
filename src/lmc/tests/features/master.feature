#Feature: SDP Master Device
#
#    Scenario: Device startup
#        Given I have an SDPMaster device
#        When the device is initialised
#        Then the state should be ON
#        And healthState should be OK
#
#    Scenario Outline: On command succeeds
#        Given I have an SDPMaster device
#        When the state is <state_value>
#        And I call On
#        Then the state should be ON
#
#        Examples:
#        |state_value|
#        |OFF        |
#        |STANDBY    |
#        |DISABLE    |
#
#    Scenario Outline: Disable command succeeds
#        Given I have an SDPMaster device
#        When the state is <state_value>
#        And I call Disable
#        Then the state should be DISABLE
#
#        Examples:
#        |state_value|
#        |OFF        |
#        |STANDBY    |
#        |ON         |
#
#    Scenario Outline: Standby command succeeds
#        Given I have an SDPMaster device
#        When the state is <state_value>
#        And I call Standby
#        Then the state should be STANDBY
#
#        Examples:
#        |state_value|
#        |OFF        |
#        |DISABLE    |
#        |ON         |
#
#    Scenario Outline: Off command succeeds
#        Given I have an SDPMaster device
#        When the state is <state_value>
#        And I call Off
#        Then the state should be OFF
#
#        Examples:
#        |state_value|
#        |STANDBY    |
#        |DISABLE    |
#        |ON         |
