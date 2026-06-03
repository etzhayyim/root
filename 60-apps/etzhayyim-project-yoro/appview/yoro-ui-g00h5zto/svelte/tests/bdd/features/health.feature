Feature: Health Check
  As a platform operator
  I want to verify the yoro service is running
  So that I can confirm deployments succeed

  Scenario: API health endpoint returns OK
    When I request the health endpoint
    Then the response status should be 200
    And the response should contain app "yoro"
    And the response should contain status "ok"

  Scenario: Health endpoint is fast
    When I request the health endpoint
    Then the response time should be less than 3000ms
