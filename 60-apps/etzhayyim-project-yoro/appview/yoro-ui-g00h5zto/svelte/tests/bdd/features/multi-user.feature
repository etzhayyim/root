Feature: Multi-User Messaging
  Verify messaging between different users

  Scenario: Send message and verify in channel listing
    Given I create a channel named "Multi User Test"
    And I send a message "sync test" to the created channel
    When I list messages in the created channel
    Then the message list should contain "sync test"

  Scenario: Create DM and send initial message
    Given I create a DM with peer "did:plc:multiuser-test"
    Then the response status should be 200
    And the response should contain a firstMessage

  Scenario: Thread with multiple replies
    Given I create a channel named "Thread Depth Test"
    And I send a root message "root msg" to the created channel
    And I send a reply "reply 1" to the root message in the created channel
    And I send a reply "reply 2" to the root message in the created channel
    When I get the thread for the root message
    Then the thread should contain at least 3 messages

  Scenario: Channel update preserves members
    Given I create a channel named "Update Members Test"
    When I update the created channel with name "Updated Name" and description "Updated"
    And I list members of the created channel
    Then the member list should contain at least 1 member
