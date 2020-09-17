Feature: SDP Master Device

    Scenario: Device startup
        Given I have an SDPMaster device
        When the device is initialised
        Then the state should be STANDBY
        And healthState should be OK

    Scenario Outline: Command succeeds
        Given I have an SDPMaster device
        When the state is <initial_state>
        And I call <command>
        Then the state should be <final_state>

        Examples:
        | command | initial_state | final_state |
        | Off     | STANDBY       | OFF         |
        | Off     | DISABLE       | OFF         |
        | Off     | ON            | OFF         |
        | Standby | OFF           | STANDBY     |
        | Standby | DISABLE       | STANDBY     |
        | Standby | ON            | STANDBY     |
        | Disable | OFF           | DISABLE     |
        | Disable | STANDBY       | DISABLE     |
        | Disable | ON            | DISABLE     |
        | On      | OFF           | ON          |
        | On      | STANDBY       | ON          |
        | On      | DISABLE       | ON          |

    Scenario Outline: Command is rejected in disallowed state
        Given I have an SDPMaster device
        When the state is <initial_state>
        Then calling <command> should raise tango.DevFailed

        Examples:
        | command | initial_state |
        | Off     | OFF           |
        | Standby | STANDBY       |
        | Disable | DISABLE       |
        | On      | ON            |
