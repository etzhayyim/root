# @etzhayyimcojp/cyber-freelance#SemanticMatchingCapability
# Capability: Semantic Matching Capability
# Description: Uses LLM to evaluate semantic similarity of skills and experiences between job seekers and jobs
# Activity: EvaluateSemanticMatchingActivity
# Implementation: performers/services/graphql/src/services/semantic_matching.rs, performers/services/graphql/src/services/llm/mod.rs
# Generated from capabilities.jsonld

@e2e @semanticmatching
Feature: セマンティックマッチングCapability
  LLMを使用して求職者と案件のスキル・経験の意味的類似性を評価する

  Background:
    Given ログイン済みのユーザーである

  @smoke
  Scenario: セマンティックマッチングCapabilityが利用可能である
    When Semantic Matching Capability機能にアクセスする
    Then 機能が正常に動作する

  @positive
  Scenario: セマンティックマッチングCapabilityが正常に完了する
    Given システムが正常に稼働している
    When Semantic Matching Capabilityを実行する
    Then 処理が成功する
    And 結果が正しく返される

  @negative
  Scenario: セマンティックマッチングCapabilityがエラーを適切に処理する
    Given システムが正常に稼働している
    When Semantic Matching Capabilityでエラーが発生する
    Then エラーが適切にハンドリングされる
    And エラーメッセージが表示される

  @validation
  Scenario: セマンティックマッチングCapabilityが入力を検証する
    Given システムが正常に稼働している
    When 不正な入力でSemantic Matching Capabilityを実行する
    Then バリデーションエラーが返される
    And 適切なエラーメッセージが表示される
