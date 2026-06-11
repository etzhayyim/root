# @etzhayyimcojp/cyber-freelance#AgencyProfileCapability
# Capability: Agency Profile Management Capability
# Description: Manages agency profile creation and updates, preventing duplicate key violations
# Activity: CreateAgencyProfileActivity, UpdateAgencyProfileActivity
# Implementation: performers/services/graphql/src/resolvers_async/mutation.rs, src/app/agency/profile/actions.ts

@agency-profile
Feature: Agency Profile Management
  As a user
  I want to create and update my agency profile
  So that I can manage my agency information without duplicate key errors

  Background:
    Given the system is running
    And the user is authenticated

  Scenario: Successfully create a new agency profile
    Given no agency profile exists for user "test_user_123"
    When I create an agency profile with:
      | field           | value                |
      | userId          | test_user_123         |
      | name            | Test Agency          |
      | contactEmail    | contact@example.com  |
      | contactPhone    | 03-1234-5678        |
    Then the agency profile should be created successfully
    And the profile should have the correct information
    And no database errors should occur

  Scenario: Prevent duplicate agency profile creation
    Given an agency profile already exists for user "test_user_456"
    When I attempt to create another agency profile with the same userId "test_user_456"
    Then the system should return a validation error
    And the error message should indicate that the profile already exists
    And no duplicate key database error should occur
    And the existing profile should remain unchanged

  Scenario: Update existing agency profile
    Given an agency profile exists for user "test_user_789" with name "Original Agency"
    When I update the agency profile with:
      | field        | value              |
      | name         | Updated Agency     |
      | contactEmail | updated@example.com|
    Then the agency profile should be updated successfully
    And the profile should reflect the new information
    And no database errors should occur

  Scenario: Handle duplicate key error gracefully in record router
    Given extracted information contains an agency with userId "test_user_router"
    And an agency profile already exists for user "test_user_router"
    When the record router processes the extracted information
    Then the router should detect the existing agency
    And the router should return the existing agency with action "skipped"
    And no duplicate key database error should occur

  Scenario: Create agency profile with Clerk organization
    Given no agency profile exists for user "test_user_clerk"
    When I create an agency profile with Clerk organization support
    Then a Clerk organization should be created for the agency profile
    And the agency profile should be linked to the Clerk organization
    And the agency profile should be created successfully

  @agency-profile @authentication
  Scenario: Require authentication for agency profile creation
    Given the system is running
    And the user is not authenticated
    When I attempt to create an agency profile without authentication
    Then the system should return an authentication error
    And the error message should indicate that authentication is required
    And no agency profile should be created
