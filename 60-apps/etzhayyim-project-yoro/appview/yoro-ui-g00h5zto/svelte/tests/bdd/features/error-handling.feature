Feature: Error Handling
  Verify graceful error responses for invalid inputs

  Scenario: Send message with empty channel ID returns error
    When I send a message to channel "" with body "hello"
    Then the response status should be 400 or 500

  Scenario: Create channel with empty name returns error
    When I create a channel with name "" and kind "public"
    Then the response status should be 400 or 500

  Scenario: Get thread with nonexistent root returns empty
    When I get thread "nonexistent-root-id" in channel "ch1"
    Then the thread should be empty

  Scenario: Search with empty query returns results
    When I search for "" in all channels
    Then the response should be valid JSON

  Scenario: List members of nonexistent channel returns empty
    When I list members of channel "nonexistent-channel"
    Then the member list should be empty
