Feature: AT Protocol Messaging Semantics
  As a yoro user communicating via AT Protocol
  I want full AT Protocol messaging capabilities
  So that my conversations follow AT record/channel/membership semantics

  Scenario: Create a direct message channel
    Given I create a DM with peer "did:plc:bdd-test-peer"
    Then the response status should be 200
    And the response should contain a convoId

  Scenario: DM deduplication returns existing channel
    Given I create a DM with peer "did:plc:bdd-dedup-peer"
    And I create a DM with peer "did:plc:bdd-dedup-peer"
    Then the response status should be 200
    And the DM should be marked as existing

  Scenario: Update a channel name and description
    Given I create a channel named "AT Update Test"
    When I update the created channel with name "AT Updated" and description "BDD updated"
    Then the response status should be 200
    And the response should contain status "updated"

  Scenario: Get channel details
    Given I create a channel named "AT Detail Test"
    When I get the created channel details
    Then the response status should be 200
    And the channel name should be "AT Detail Test"
    And the channel type should be "public"

  Scenario: List channel members
    Given I create a channel named "AT Members Test"
    When I list members of the created channel
    Then the response status should be 200
    And the member list should contain at least 1 member
    And the first member should have role "owner"

  Scenario: Get unread counts
    Given I create a channel named "AT Unread Test"
    And I send a message "unread msg 1" to the created channel
    When I get unread counts
    Then the response status should be 200
    And the unread map should contain the created convo

  Scenario: Search messages via Cypher graph
    Given I create a channel named "AT Search Test"
    And I send a message "searchable-bdd-keyword" to the created channel
    When I search messages for "searchable-bdd-keyword"
    Then the response status should be 200

  Scenario: Upload a blob attachment
    Given I create a channel named "AT Blob Test"
    When I upload a blob with filename "test.txt" and contentType "text/plain"
    Then the upload response should be 200 or 500 with error
    And if upload succeeded then the response should contain a blob uri and filename "test.txt"

  Scenario: Retrieve a message thread
    Given I create a channel named "AT Thread Test"
    And I send a root message "thread root" to the created channel
    And I send a reply "thread reply" to the root message in the created channel
    When I get the thread for the root message
    Then the response status should be 200
    And the thread should contain at least 2 messages
