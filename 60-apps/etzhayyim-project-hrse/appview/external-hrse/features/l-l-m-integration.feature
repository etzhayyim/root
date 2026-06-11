# @etzhayyimcojp/cyber-freelance#LLMIntegrationCapability
# Capability: LLM Integration Capability
# Description: Integrates with OpenAI GPT-4 to analyze email content and extract structured data
# Activity: ExtractEntityInfoActivity
# Implementation: src/lib/llm/openai.ts, src/lib/llm/prompts.ts
# Generated from capabilities.jsonld

Feature: LLM Integration Capability
  Integrates with OpenAI GPT-4 to analyze email content and extract structured data

  Scenario: LLM Integration Capability should be available
    Given the system is running
    When the "LLM Integration Capability" capability is invoked
    Then it should perform the expected behavior
    And the result should be successful

  Scenario: LLM Integration Capability should handle errors gracefully
    Given the system is running
    When an error occurs in "LLM Integration Capability" capability
    Then it should handle the error appropriately
    And the error should be logged

  Scenario: LLM Integration Capability should validate input
    Given the system is running
    When invalid input is provided to "LLM Integration Capability" capability
    Then it should reject the input
    And an appropriate error message should be returned

  Scenario: LLM should extract structured data from email content
    Given an email is received
    When the email content is analyzed using LLM
    Then structured data should be extracted
    And the extracted data should include job seeker, job, or agency information

  Scenario: LLM should handle API errors gracefully
    Given the LLM API is unavailable
    When email content is analyzed using LLM
    Then the error should be handled gracefully
    And an appropriate error message should be returned

  Scenario: LLM should handle rate limiting
    Given LLM API rate limit is reached
    When email content is analyzed using LLM
    Then the rate limit error should be handled
    And retry logic should be applied
