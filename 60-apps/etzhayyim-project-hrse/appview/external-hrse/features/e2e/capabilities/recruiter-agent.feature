# @etzhayyimcojp/etzhayyim-hrse#RecruiterAgentCapability
# Capability: Recruiter AI Agent Capability
# Description: Hume AIを使用してリクルーターの業務を支援するAIエージェント機能。今日のタスク生成、推奨アクション提案、チャット形式での対話を提供
# Activity: GenerateDailyTasksActivity, ProvideSuggestionsActivity, ChatWithAgentActivity
# Implementation: pkg/service/recruiter_agent.go, pkg/hume/client.go, proto/hrse/v1/recruiter_agent.proto, src/app/agency/recruiter-supporter/page.tsx, src/components/recruiter-agent/ChatInterface.tsx, src/components/recruiter-agent/TaskDashboard.tsx, src/components/recruiter-agent/SuggestionPanel.tsx
# Generated from capabilities.jsonld

@e2e @recruiteragent
Feature: リクルーターAIエージェントCapability
  Hume AIを使用してリクルーターの業務を支援するAIエージェント機能。今日のタスク生成、推奨アクション提案、チャット形式での対話を提供

  Background:
    Given ログイン済みのリクルーターである

  @smoke
  Scenario: リクルーターAIエージェントCapabilityが利用可能である
    When Recruiter AI Agent Capability機能にアクセスする
    Then 機能が正常に動作する
    And 今日のタスクが表示される
    And 推奨アクションが表示される
    And チャットインターフェースが表示される

  @positive
  Scenario: 今日のタスクが正常に生成される
    Given システムが正常に稼働している
    When GetDailyTasksを実行する
    Then タスク一覧が返される
    And タスクには優先度が設定されている
    And タスクには説明が含まれている

  @positive
  Scenario: AIサジェストが正常に生成される
    Given システムが正常に稼働している
    When GetSuggestionsを実行する
    Then 推奨アクション一覧が返される
    And サジェストには理由が含まれている
    And サジェストには優先度が設定されている

  @positive
  Scenario: チャットメッセージが正常に送信される
    Given システムが正常に稼働している
    When SendChatMessageを実行する
    Then メッセージが送信される
    And AIエージェントからの応答が返される

  @positive
  Scenario: タスクが完了としてマークされる
    Given タスクが存在する
    When MarkTaskCompleteを実行する
    Then タスクが完了状態になる
    And タスクの完了日時が設定される

  @negative
  Scenario: リクルーターAIエージェントCapabilityがエラーを適切に処理する
    Given システムが正常に稼働している
    When Recruiter AI Agent Capabilityでエラーが発生する
    Then エラーが適切にハンドリングされる
    And エラーメッセージが表示される

  @validation
  Scenario: リクルーターAIエージェントCapabilityが入力を検証する
    Given システムが正常に稼働している
    When 不正な入力でRecruiter AI Agent Capabilityを実行する
    Then バリデーションエラーが返される
    And 適切なエラーメッセージが表示される

  @integration
  Scenario: チャット履歴が正常に取得される
    Given チャット履歴が存在する
    When GetChatHistoryを実行する
    Then チャット履歴が返される
    And メッセージが時系列順に並んでいる
