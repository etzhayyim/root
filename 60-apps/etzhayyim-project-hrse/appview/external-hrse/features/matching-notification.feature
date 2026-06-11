# @etzhayyimcojp/cyber-freelance#MatchingNotificationCapability
# Capability: Matching Notification Capability
# Description: Sends email and in-app notifications when matching results are found
# Activity: SendMatchingNotificationActivity
# Implementation: performers/services/graphql/src/services/matching_notification.rs
# Generated from capabilities.jsonld

Feature: Matching Notification Capability
  Sends email and in-app notifications when matching results are found

  Scenario: Matching Notification Capability should be available
    Given the system is running
    When the "Matching Notification Capability" capability is invoked
    Then it should perform the expected behavior
    And the result should be successful

  Scenario: Matching Notification Capability should handle errors gracefully
    Given the system is running
    When an error occurs in "Matching Notification Capability" capability
    Then it should handle the error appropriately
    And the error should be logged

  Scenario: Matching Notification Capability should validate input
    Given the system is running
    When invalid input is provided to "Matching Notification Capability" capability
    Then it should reject the input
    And an appropriate error message should be returned

  Scenario: Matching notification should be sent when match is found
    Given matching results are available
    When a matching result is found
    Then a notification should be sent
    And the notification should include match details
    And the notification should be sent via email and in-app

  Scenario: Matching notification should not be sent when no match is found
    Given no matching results are available
    When matching is performed
    Then no notification should be sent
    And the system should continue normally
