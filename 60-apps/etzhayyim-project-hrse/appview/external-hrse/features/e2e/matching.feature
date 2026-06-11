# @etzhayyimcojp/cyber-freelance#MatchingE2EBDD
# E2E BDD: マッチング機能

@e2e @matching
Feature: マッチング機能
  求職者と案件のマッチングを確認できること
  
  Background:
    Given ログイン済みのユーザーである

  @semantic
  Scenario: セマンティックマッチング結果を表示できる
    Given 求職者プロファイルが存在する
    And 案件が存在する
    When マッチング結果ページにアクセスする
    Then マッチング結果一覧が表示される
    And 各マッチング結果にスコアが表示される

  @semantic @detail
  Scenario: マッチング結果の詳細を確認できる
    Given 求職者プロファイルが存在する
    And 案件が存在する
    When マッチング結果ページにアクセスする
    And 最初のマッチング結果をクリックする
    Then マッチング詳細が表示される
    And スキルマッチ率が表示される
    And セマンティック類似度が表示される

  @filter
  Scenario: マッチング結果をフィルタできる
    Given 複数のマッチング結果が存在する
    When マッチング結果ページにアクセスする
    And スコアフィルタを "80" 以上に設定する
    Then 80%以上のマッチング結果のみ表示される

  @notification
  Scenario: 新しいマッチングの通知を受け取れる
    Given 求職者プロファイルが存在する
    When 新しい案件が作成される
    And マッチングが実行される
    Then 通知アイコンに新しい通知が表示される
    And 通知をクリックするとマッチング詳細が表示される



