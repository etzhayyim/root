# @etzhayyimcojp/cyber-freelance#IntegrationCapability
# Capability: Integration Capability
# Description: Integration testing scenarios for multiple feature interactions
# Activity: IntegrationTestActivity
# Implementation: features/step_definitions/common.steps.ts

Feature: Integration Capability
  As a system
  I want to ensure features work together correctly
  So that the system provides a cohesive user experience

  Background:
    Given the system is running
    And the user is authenticated

  Scenario: Email sync job triggers email analysis
    Given an email sync job is running
    When emails are processed
    Then email analysis should be triggered for each email
    And extracted data should be routed to appropriate records
    And the entire workflow should complete successfully

  Scenario: Email analysis triggers record routing
    Given an email is received
    And the email is analyzed using LLM
    When structured information is extracted
    Then record routing should be triggered
    And appropriate database records should be created or updated
    And the routing should complete successfully

  Scenario: Record routing triggers semantic matching
    Given job seeker and job records are created
    When semantic matching is performed
    Then matching results should be generated
    And notifications should be sent if matches are found
    And the entire workflow should complete successfully

  Scenario: Agency profile creation with Clerk organization
    Given no agency profile exists for user "test_user_clerk"
    When I create an agency profile with Clerk organization support
    Then a Clerk organization should be created
    And the agency profile should be linked to the organization
    And the user should have appropriate permissions

  Scenario: End-to-end email processing workflow
    Given an email is received
    When the email is processed through the entire workflow
    Then email analysis should extract structured information
    And record routing should create or update records
    And semantic matching should evaluate similarity
    And notifications should be sent if applicable
    And the entire workflow should complete successfully


