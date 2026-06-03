# @etzhayyimcojp/cyber-freelance#EventTriggerCapability
# Capability: Event Trigger Capability
# Description: Detects job and job seeker registration/update events and triggers matching processing
# Activity: TriggerMatchingOnJobUpdateActivity, TriggerMatchingOnJobSeekerUpdateActivity
# Implementation: performers/services/graphql/src/resolvers/mutation/mod.rs
# Generated from capabilities.jsonld

@e2e @eventtrigger
Feature: イベントトリガーCapability
  案件・人材の登録・更新イベントを検知し、マッチング処理をトリガーする

  Background:
    Given ログイン済みのユーザーである

  @smoke
  Scenario: イベントトリガーCapabilityが利用可能である
    When Event Trigger Capability機能にアクセスする
    Then 機能が正常に動作する

  @positive
  Scenario: イベントトリガーCapabilityが正常に完了する
    Given システムが正常に稼働している
    When Event Trigger Capabilityを実行する
    Then 処理が成功する
    And 結果が正しく返される

  @negative
  Scenario: イベントトリガーCapabilityがエラーを適切に処理する
    Given システムが正常に稼働している
    When Event Trigger Capabilityでエラーが発生する
    Then エラーが適切にハンドリングされる
    And エラーメッセージが表示される

  @validation
  Scenario: イベントトリガーCapabilityが入力を検証する
    Given システムが正常に稼働している
    When 不正な入力でEvent Trigger Capabilityを実行する
    Then バリデーションエラーが返される
    And 適切なエラーメッセージが表示される
