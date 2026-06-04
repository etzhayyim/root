Feature: Performance & Resilience
  Verify API performance and error resilience

  Scenario: Channel creation is fast
    When I time creating a channel named "Perf Test"
    Then the response time should be less than 5000ms

  Scenario: Message sending is fast
    Given I create a channel named "Send Perf Test"
    When I time sending a message "perf test msg" to the created channel
    Then the response time should be less than 5000ms

  Scenario: List channels handles pagination
    Given I create a channel named "Pagination A"
    And I create a channel named "Pagination B"
    When I list channels with limit 1
    Then the channel list should have at most 1 channel

  Scenario: Health endpoint under load
    When I request the health endpoint 10 times concurrently
    Then all responses should be 200
