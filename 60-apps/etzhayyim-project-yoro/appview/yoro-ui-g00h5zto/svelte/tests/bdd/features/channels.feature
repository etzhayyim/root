Feature: Channel Management
  As a yoro user
  I want to create and browse channels
  So that I can communicate with others

  Scenario: Create a public channel via API
    Given I create a channel named "BDD Test Channel"
    Then the response status should be 200
    And the response should contain channelType "public"

  Scenario: List channels via API
    Given I create a channel named "List Test Channel"
    When I list all channels
    Then the response status should be 200
    And the channel list should be an array

  Scenario: Join and leave a channel
    Given I create a channel named "Join Leave Test"
    When I join the created channel
    Then the response status should be 200
    When I leave the created channel
    Then the response status should be 200
