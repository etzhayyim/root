# @etzhayyimcojp/cyber-freelance#MatchingNotificationCapability
# Capability: Matching Notification Capability
# Description: Sends email and in-app notifications when matching results are found
# Activity: SendMatchingNotificationActivity
# Implementation: performers/services/graphql/src/services/matching_notification.rs
# Generated from capabilities.jsonld

@e2e @matchingnotification
Feature: マッチング通知Capability
  マッチング結果が見つかった際にメールとアプリ内通知を送信する

  Background:
    Given ログイン済みのユーザーである

  @smoke
  Scenario: マッチング通知Capabilityが利用可能である
    When Matching Notification Capability機能にアクセスする
    Then 機能が正常に動作する

  @positive
  Scenario: マッチング通知Capabilityが正常に完了する
    Given システムが正常に稼働している
    When Matching Notification Capabilityを実行する
    Then 処理が成功する
    And 結果が正しく返される

  @negative
  Scenario: マッチング通知Capabilityがエラーを適切に処理する
    Given システムが正常に稼働している
    When Matching Notification Capabilityでエラーが発生する
    Then エラーが適切にハンドリングされる
    And エラーメッセージが表示される

  @validation
  Scenario: マッチング通知Capabilityが入力を検証する
    Given システムが正常に稼働している
    When 不正な入力でMatching Notification Capabilityを実行する
    Then バリデーションエラーが返される
    And 適切なエラーメッセージが表示される
