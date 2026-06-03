# @capability:email-sync-job-management
# Email Sync Job Management Capability
# メール同期ジョブ管理機能

Feature: Email Sync Job Management
  As a system administrator
  I want to manage email synchronization jobs
  So that I can track progress and retry failed jobs

  Background:
    Given the GraphQL API is available
    And the database is connected

  Scenario: Create a new email sync job
    Given I have Resend API credentials
    When I trigger a manual email sync with limit "100"
    Then a new email sync job should be created
    And the job status should be "pending"
    And the job should have a unique ID

  Scenario: Job progresses from pending to running
    Given an email sync job exists with status "pending"
    When the sync process starts
    Then the job status should change to "running"
    And the job should have a started_at timestamp

  Scenario: Track job progress during execution
    Given an email sync job is running
    When emails are processed in email sync job
    Then the processed count should increase
    And the progress percentage should update
    And the job should be updated every 10 emails

  Scenario: Job completes successfully
    Given an email sync job is running
    When all emails are processed successfully
    Then the job status should change to "completed"
    And the job should have a completed_at timestamp
    And the processed count should equal total emails
    And errors should be zero

  Scenario: Job fails with errors
    Given an email sync job is running
    When errors occur during processing
    Then the job status should change to "failed"
    And the error count should be greater than zero
    And the error message should be recorded

  Scenario: Retry a failed job
    Given a failed email sync job exists
    When I retry the job
    Then a new job should be created
    And the new job should have status "pending"
    And the new job should use the same limit as the original

  Scenario: List all email sync jobs
    Given multiple email sync jobs exist
    When I query the job list
    Then I should receive a list of jobs
    And jobs should be ordered by created_at descending
    And each job should have status, progress, and statistics

  Scenario: Get latest email sync job
    Given multiple email sync jobs exist
    When I query the latest job
    Then I should receive the most recently created job
    And the job should have all required fields

  Scenario: View job details
    Given an email sync job exists
    When I query the job by ID
    Then I should receive the job details
    And the job should include progress, statistics, and timestamps
