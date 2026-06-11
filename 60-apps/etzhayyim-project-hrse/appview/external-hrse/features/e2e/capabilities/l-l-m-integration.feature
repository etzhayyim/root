# @etzhayyimcojp/cyber-freelance#LLMIntegrationCapability
# Capability: LLM Integration Capability
# Description: Integrates with OpenAI GPT-4 to analyze email content and extract structured data
# Activity: ExtractEntityInfoActivity
# Implementation: src/lib/llm/openai.ts, src/lib/llm/prompts.ts
# Generated from capabilities.jsonld

@e2e @llmintegration
Feature: LLM統合Capability
  OpenAI GPT-4と統合してメール内容を分析し、構造化データを抽出する

  Background:
    Given ログイン済みのユーザーである

  @smoke
  Scenario: LLM統合Capabilityが利用可能である
    When LLM Integration Capability機能にアクセスする
    Then 機能が正常に動作する

  @positive
  Scenario: LLM統合Capabilityが正常に完了する
    Given システムが正常に稼働している
    When LLM Integration Capabilityを実行する
    Then 処理が成功する
    And 結果が正しく返される

  @negative
  Scenario: LLM統合Capabilityがエラーを適切に処理する
    Given システムが正常に稼働している
    When LLM Integration Capabilityでエラーが発生する
    Then エラーが適切にハンドリングされる
    And エラーメッセージが表示される

  @validation
  Scenario: LLM統合Capabilityが入力を検証する
    Given システムが正常に稼働している
    When 不正な入力でLLM Integration Capabilityを実行する
    Then バリデーションエラーが返される
    And 適切なエラーメッセージが表示される
