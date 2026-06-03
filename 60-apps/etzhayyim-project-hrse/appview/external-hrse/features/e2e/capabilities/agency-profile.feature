# @etzhayyimcojp/cyber-freelance#AgencyProfileCapability
# Capability: Agency Profile Management Capability
# Description: Manages agency profile creation and updates, preventing duplicate key violations and integrating with Clerk organizations
# Activity: CreateAgencyProfileActivity, UpdateAgencyProfileActivity
# Implementation: performers/services/graphql/src/resolvers_async/mutation.rs, src/app/agency/profile/actions.ts, src/app/agency/profile/page.tsx, src/app/[orgId]/agency/profile/page.tsx, src/lib/hooks/use-agency-profile.ts
# Generated from capabilities.jsonld

@e2e @agencyprofile
Feature: エージェンシープロファイル管理Capability
  エージェンシープロファイルの作成と更新を管理し、重複キー違反を防止し、Clerk組織と統合する

  Background:
    Given ログイン済みのユーザーである

  @smoke
  Scenario: エージェンシープロファイル管理Capabilityが利用可能である
    When Agency Profile Management Capability機能にアクセスする
    Then 機能が正常に動作する

  @positive
  Scenario: エージェンシープロファイル管理Capabilityが正常に完了する
    Given システムが正常に稼働している
    When Agency Profile Management Capabilityを実行する
    Then 処理が成功する
    And 結果が正しく返される

  @negative
  Scenario: エージェンシープロファイル管理Capabilityがエラーを適切に処理する
    Given システムが正常に稼働している
    When Agency Profile Management Capabilityでエラーが発生する
    Then エラーが適切にハンドリングされる
    And エラーメッセージが表示される

  @validation
  Scenario: エージェンシープロファイル管理Capabilityが入力を検証する
    Given システムが正常に稼働している
    When 不正な入力でAgency Profile Management Capabilityを実行する
    Then バリデーションエラーが返される
    And 適切なエラーメッセージが表示される
