# @etzhayyimcojp/cyber-freelance#EmailAnalysisCapability
# Capability: Email Analysis Capability
# Description: Analyzes incoming emails using LLM to extract structured information about job seekers, jobs, and agencies
# Activity: AnalyzeEmailActivity
# Implementation: src/lib/services/email-analyzer.ts, src/lib/llm/openai.ts
# Generated from capabilities.jsonld

@e2e @emailanalysis
Feature: メール分析Capability
  LLMを使用して受信メールを分析し、人材、案件、エージェントに関する構造化情報を抽出する

  Background:
    Given ログイン済みのユーザーである

  @smoke
  Scenario: メール分析Capabilityが利用可能である
    When Email Analysis Capability機能にアクセスする
    Then 機能が正常に動作する

  @positive
  Scenario: メール分析Capabilityが正常に完了する
    Given システムが正常に稼働している
    When Email Analysis Capabilityを実行する
    Then 処理が成功する
    And 結果が正しく返される

  @negative
  Scenario: メール分析Capabilityがエラーを適切に処理する
    Given システムが正常に稼働している
    When Email Analysis Capabilityでエラーが発生する
    Then エラーが適切にハンドリングされる
    And エラーメッセージが表示される

  @validation
  Scenario: メール分析Capabilityが入力を検証する
    Given システムが正常に稼働している
    When 不正な入力でEmail Analysis Capabilityを実行する
    Then バリデーションエラーが返される
    And 適切なエラーメッセージが表示される
