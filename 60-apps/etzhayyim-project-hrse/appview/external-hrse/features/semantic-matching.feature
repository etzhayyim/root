# @etzhayyimcojp/cyber-freelance#SemanticMatchingCapability
# Capability: Semantic Matching Capability
# Description: Uses LLM to evaluate semantic similarity of skills and experiences between job seekers and jobs
# Activity: EvaluateSemanticMatchingActivity
# Implementation: performers/services/graphql/src/services/semantic_matching.rs, performers/services/graphql/src/services/llm/mod.rs
# Generated from capabilities.jsonld

Feature: Semantic Matching Capability
  Uses LLM to evaluate semantic similarity of skills and experiences between job seekers and jobs

  Scenario: Semantic Matching Capability should be available
    Given the system is running
    When the "Semantic Matching Capability" capability is invoked
    Then it should perform the expected behavior
    And the result should be successful

  Scenario: Semantic Matching Capability should handle errors gracefully
    Given the system is running
    When an error occurs in "Semantic Matching Capability" capability
    Then it should handle the error appropriately
    And the error should be logged

  Scenario: Semantic Matching Capability should validate input
    Given the system is running
    When invalid input is provided to "Semantic Matching Capability" capability
    Then it should reject the input
    And an appropriate error message should be returned

  Scenario: Semantic matching should evaluate similarity
    Given job seeker and job data are available
    When semantic matching is performed for job matching
    Then similarity scores should be calculated
    And the scores should reflect semantic similarity
