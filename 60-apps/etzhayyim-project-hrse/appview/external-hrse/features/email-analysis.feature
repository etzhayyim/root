# @etzhayyimcojp/cyber-freelance#EmailAnalysisCapability
# Capability: Email Analysis Capability
# Description: Analyzes incoming emails using LLM to extract structured information about job seekers, jobs, and agencies
# Activity: AnalyzeEmailActivity
# Implementation: src/lib/services/email-analyzer.ts, src/lib/llm/openai.ts
# Generated from capabilities.jsonld

Feature: Email Analysis Capability
  Analyzes incoming emails using LLM to extract structured information about job seekers, jobs, and agencies

  Scenario: Email Analysis Capability should be available
    Given the system is running
    When the "Email Analysis Capability" capability is invoked
    Then it should perform the expected behavior
    And the result should be successful

  Scenario: Email Analysis Capability should handle errors gracefully
    Given the system is running
    When an error occurs in "Email Analysis Capability" capability
    Then it should handle the error appropriately
    And the error should be logged

  Scenario: Email Analysis Capability should validate input
    Given the system is running
    When invalid input is provided to "Email Analysis Capability" capability
    Then it should reject the input
    And an appropriate error message should be returned

  Scenario: Email analysis should extract structured information
    Given an email is received
    When the email is analyzed using LLM
    Then structured information about job seekers, jobs, or agencies should be extracted
    And the extracted data should be valid
