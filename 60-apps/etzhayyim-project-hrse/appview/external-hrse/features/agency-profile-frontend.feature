# @etzhayyimcojp/cyber-freelance#AgencyProfileCapabilityFrontend
# Capability: Agency Profile Management Capability (Frontend)
# Description: Manages agency profile creation and updates through the frontend UI
# Activity: CreateAgencyProfileActivity, UpdateAgencyProfileActivity
# Implementation: src/app/agency/profile/page.tsx, src/app/agency/profile/actions.ts

@agency-profile @frontend
Feature: Agency Profile Management (Frontend)
  As a user
  I want to create and update my agency profile through the web interface
  So that I can manage my agency information using the UI

  Background:
    Given the system is running
    And the user is authenticated
    And I am on the "/agency/profile" page

  Scenario: Successfully create a new agency profile through the UI
    Given no agency profile exists for user "test_user_frontend_123"
    When I create an agency profile with:
      | field           | value                |
      | userId          | test_user_frontend_123 |
      | name            | Test Agency Frontend |
      | contactEmail    | contact@example.com  |
      | contactPhone    | 03-1234-5678        |
    Then the agency profile should be created successfully
    And I should see a success message
    And the profile should have the correct information
    And no database errors should occur

  Scenario: Display validation error when creating duplicate agency profile
    Given an agency profile already exists for user "test_user_frontend_456"
    When I attempt to create another agency profile with the same userId "test_user_frontend_456"
    Then the system should return a validation error
    And I should see a validation error
    And the error message should indicate that the profile already exists
    And no duplicate key database error should occur

  Scenario: Update existing agency profile through the UI
    Given an agency profile exists for user "test_user_frontend_789" with name "Original Agency Frontend"
    And I am on the "/agency/profile" page
    When I update the agency profile with:
      | field        | value                    |
      | name         | Updated Agency Frontend  |
      | contactEmail | updated@example.com     |
    Then the agency profile should be updated successfully
    And I should see a success message
    And the profile should reflect the new information
    And no database errors should occur
