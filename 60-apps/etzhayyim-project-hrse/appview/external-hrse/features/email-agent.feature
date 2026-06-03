# @etzhayyimcojp/etzhayyim-hrse#EmailAgentCapability
# Capability: Email Agent Capability
# Description: LLM-powered email generation and management for matching notifications
# Activity: GenerateMatchingEmailActivity, AnalyzeEmailReplyActivity
# Implementation: pkg/service/email_agent.go, src/lib/services/email-sender.ts

Feature: Email Agent Capability
  LLM-powered email generation and management for matching notifications

  Background:
    Given the system is running
    And a matching result exists

  Scenario: Generate matching notification email for job seeker
    Given a matching result with job seeker participant
    When LLM generates a matching email
    Then a personalized email should be generated
    And the email should include match score and key points
    And the email should include a secure link placeholder

  Scenario: Generate matching notification email for recruiter
    Given a matching result with recruiter participant
    When LLM generates a matching email
    Then a personalized email should be generated
    And the email should highlight job seeker strengths
    And the email should include a secure link placeholder

  Scenario: Email review queue workflow
    Given a generated email is pending review
    When the email is viewed in the review queue
    Then the email preview should be displayed
    When the email is approved
    Then the email should be sent via Resend API
    And the email status should be updated to "sent"
    And the Resend email ID should be stored
    And the sent_at timestamp should be recorded

  Scenario: Email approval triggers Resend API call
    Given a generated email is pending review
    And Resend API is configured
    When the email is approved
    Then Resend API should be called with correct parameters
    And the email should be sent to the recipient
    And the email status should be updated to "sent"
    And the Resend email ID should be stored in the database

  Scenario: Email rejection workflow
    Given a generated email is pending review
    When the email is rejected with a reason
    Then the email status should be updated to "rejected"
    And the rejection reason should be stored

  Scenario: Email editing workflow
    Given a generated email is pending review
    When the email is edited
    And the edited email is approved
    Then the edited email should be sent via Resend
    And the original email should be replaced

  Scenario: Secure link creation and access
    Given a matching email is sent
    When a secure link is created for the job
    Then a secure token should be generated
    And the link should expire in 30 days by default
    When an allowed email accesses the secure link
    Then access should be granted
    And access log should be recorded

  Scenario: Secure link email verification
    Given a secure link exists
    When an unauthorized email tries to access
    Then access should be denied
    When an allowed email accesses the link
    Then access should be granted

  Scenario: Comprehensive analytics tracking
    Given a user accesses a secure link
    When the user views the page
    Then page view should be tracked
    And time on page should be tracked
    And scroll depth should be tracked
    When the user clicks elements
    Then click events should be tracked
    When the user moves the mouse
    Then mouse movements should be sampled and tracked
    When the user leaves the page
    Then exit point should be recorded
    And final analytics data should be sent

  Scenario: Access log is saved to database
    Given a user accesses a secure link
    And analytics data is collected
    When the user leaves the page
    Then SaveAccessLog RPC should be called
    And the access log should be saved to access_logs table
    And the access log should include time_on_page
    And the access log should include scroll_depth
    And the access log should include clicks
    And the access log should include mouse_movements
    And the access log should include focus_time
    And the access log should include exit_point
    And the access log should include sections_viewed

  Scenario: Email reply analysis
    Given an email reply is received
    When LLM analyzes the reply
    Then the intent should be determined
    And extracted data should include meeting dates if scheduling
    And extracted data should include negotiation points if negotiating
    And extracted data should include decline reason if declining

  Scenario: Resend webhook processes email reply
    Given a Resend webhook receives an email reply
    And the email is a reply to an existing conversation
    When the webhook processes the email
    Then EmailAgentService should analyze the reply
    And the reply intent should be determined
    And the reply should be saved to email_messages table
    And the reply status should be "pending_review"

  Scenario: Generate reply email
    Given an analyzed email reply
    When LLM generates a reply email
    Then an appropriate reply should be generated
    And the reply should address the intent
    And the reply should be added to review queue

  Scenario: Generate meeting proposal email
    Given proposed meeting dates
    When LLM generates a meeting proposal email
    Then a professional meeting proposal should be generated
    And the email should include proposed dates
    And the email should suggest meeting format

  Scenario: Generate condition negotiation email
    Given negotiation points
    When LLM generates a negotiation email
    Then a professional negotiation email should be generated
    And the email should present negotiation points clearly
    And the email should maintain collaborative tone
