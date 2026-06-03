# @etzhayyimcojp/cyber-freelance#RecordRoutingCapability
# Capability: Record Routing Capability
# Description: Routes extracted information to appropriate database records, creating or updating JobSeeker, Job, or Agency records
# Activity: RouteRecordActivity
# Implementation: src/lib/services/record-router.ts
# Generated from capabilities.jsonld

@e2e @recordrouting
Feature: レコード振り分けCapability
  抽出された情報を適切なデータベースレコードに振り分け、JobSeeker、Job、またはAgencyレコードを作成または更新する

  Background:
    Given ログイン済みのユーザーである

  @smoke
  Scenario: レコード振り分けCapabilityが利用可能である
    When Record Routing Capability機能にアクセスする
    Then 機能が正常に動作する

  @positive
  Scenario: レコード振り分けCapabilityが正常に完了する
    Given システムが正常に稼働している
    When Record Routing Capabilityを実行する
    Then 処理が成功する
    And 結果が正しく返される

  @negative
  Scenario: レコード振り分けCapabilityがエラーを適切に処理する
    Given システムが正常に稼働している
    When Record Routing Capabilityでエラーが発生する
    Then エラーが適切にハンドリングされる
    And エラーメッセージが表示される

  @validation
  Scenario: レコード振り分けCapabilityが入力を検証する
    Given システムが正常に稼働している
    When 不正な入力でRecord Routing Capabilityを実行する
    Then バリデーションエラーが返される
    And 適切なエラーメッセージが表示される
