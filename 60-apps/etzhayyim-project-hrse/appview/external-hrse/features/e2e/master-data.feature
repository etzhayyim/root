# @etzhayyimcojp/cyber-freelance#MasterDataE2EBDD
# E2E BDD: マスターデータ管理機能

@e2e @admin @master-data
Feature: マスターデータ管理
  管理者として、マスターデータを管理できること
  
  Background:
    Given ログイン済みの管理者ユーザーである

  @list
  Scenario: マスターデータ一覧を表示できる
    When マスターデータ管理ページにアクセスする
    Then 資格タブが表示される
    And 専門分野タブが表示される
    And 言語タブが表示される

  @certifications @list
  Scenario: 資格一覧を表示できる
    When マスターデータ管理ページにアクセスする
    And 資格タブをクリックする
    Then 資格の一覧が表示される

  @certifications @create
  Scenario: 新しい資格を作成できる
    When マスターデータ管理ページにアクセスする
    And 資格タブをクリックする
    And 新規作成ボタンをクリックする
    And 資格名に "CISSP" を入力する
    And 説明に "情報セキュリティ専門家認定資格" を入力する
    And 作成ボタンをクリックする
    Then 作成成功メッセージが表示される
    And 資格 "CISSP" が一覧に表示される

  @certifications @edit
  Scenario: 資格を編集できる
    Given 資格 "TestCert" が存在する
    When マスターデータ管理ページにアクセスする
    And 資格タブをクリックする
    And 資格 "TestCert" の編集ボタンをクリックする
    And 資格名を "UpdatedCert" に変更する
    And 保存ボタンをクリックする
    Then 更新成功メッセージが表示される
    And 資格 "UpdatedCert" が一覧に表示される

  @certifications @delete
  Scenario: 資格を削除できる
    Given 資格 "ToDeleteCert" が存在する
    When マスターデータ管理ページにアクセスする
    And 資格タブをクリックする
    And 資格 "ToDeleteCert" の削除ボタンをクリックする
    And 削除を確認する
    Then 削除成功メッセージが表示される
    And 資格 "ToDeleteCert" が一覧に表示されない

  @specializations
  Scenario: 専門分野を管理できる
    When マスターデータ管理ページにアクセスする
    And 専門分野タブをクリックする
    Then 専門分野の一覧が表示される
    And 各専門分野に名前が表示される

  @languages
  Scenario: 言語を管理できる
    When マスターデータ管理ページにアクセスする
    And 言語タブをクリックする
    Then 言語の一覧が表示される
    And 各言語に名前が表示される



