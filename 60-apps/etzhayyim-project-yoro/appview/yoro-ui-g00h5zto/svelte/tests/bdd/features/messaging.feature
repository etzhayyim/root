Feature: Messaging
  As a yoro user
  I want to send and receive messages
  So that I can chat with channel members

  Scenario: Send a message to a channel
    Given I create a channel named "Messaging Test"
    And I send a message "Hello BDD" to the created channel
    Then the response status should be 200
    And the response should contain a messageId
    And the response should contain a rkey

  Scenario: List messages in a channel
    Given I create a channel named "List Messages Test"
    And I send a message "First message" to the created channel
    And I send a message "Second message" to the created channel
    When I list messages in the created channel
    Then the response status should be 200
    And the message list should contain 2 messages

  Scenario: Send a read receipt
    Given I create a channel named "Receipt Test"
    And I send a message "Read me" to the created channel
    When I send a read receipt for the last message
    Then the response status should be 200

  Scenario: Add a reaction to a message
    Given I create a channel named "Reaction Test"
    And I send a message "React to me" to the created channel
    When I add reaction "thumbsup" to the last message
    Then the response status should be 200
    And the response should contain a reactionId
