# @etzhayyimcojp/cyber-freelance#JobSeekerProfileE2EBDD
# E2E BDD: 求職者プロファイル管理機能

@e2e @job-seeker
Feature: 求職者プロファイル管理
  求職者として、自分のプロファイルを管理できること
  
  Background:
    Given ログイン済みの求職者ユーザーである

  @profile @view
  Scenario: プロファイルページを表示できる
    When 求職者プロファイルページにアクセスする
    Then プロファイルフォームが表示される
    And 基本情報入力欄が表示される
    And スキル選択欄が表示される

  @profile @edit
  Scenario: プロファイル情報を編集できる
    When 求職者プロファイルページにアクセスする
    And 希望単価に "5000" を入力する
    And 経験年数に "5" を入力する
    Then 入力した値が反映される

  @profile @save
  Scenario: プロファイル情報を保存できる
    When 求職者プロファイルページにアクセスする
    And 希望単価に "6000" を入力する
    And 保存ボタンをクリックする
    Then 保存成功メッセージが表示される

  @profile @save @persistence
  Scenario: 保存したプロファイルがリロード後も維持される
    Given 求職者プロファイルページにアクセスする
    And 希望単価に "7000" を入力する
    And 保存ボタンをクリックする
    And 保存成功メッセージが表示される
    When ページをリロードする
    Then 希望単価が "7000" である

  @profile @validation
  Scenario: 必須項目が未入力の場合エラーが表示される
    When 求職者プロファイルページにアクセスする
    And すべての必須項目をクリアする
    And 保存ボタンをクリックする
    Then バリデーションエラーが表示される

  @profile @skills
  Scenario: スキルを選択して保存できる
    When 求職者プロファイルページにアクセスする
    And スキル "Python" を選択する
    And スキル "Security" を選択する
    And 保存ボタンをクリックする
    Then 保存成功メッセージが表示される
    When ページをリロードする
    Then スキル "Python" が選択されている
    And スキル "Security" が選択されている
