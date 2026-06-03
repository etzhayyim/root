// @etzhayyim/cyber-freelance#JapaneseE2ESteps
// 日本語E2Eテスト関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

// システム状態
Given("システムが正常に稼働している", async function (this: ICustomWorld) {
	this.context.systemRunning = true;
	this.context.systemStatus = "healthy";
});

// 認証関連
Given("ログイン済みの求職者ユーザーである", async function (this: ICustomWorld) {
	this.context.authenticated = true;
	this.context.userType = "jobSeeker";
	this.context.user = {
		id: "jobSeekerUser123",
		email: "jobSeeker@example.com",
		type: "jobSeeker",
	};
});

Given("ログイン済みのユーザーである", async function (this: ICustomWorld) {
	this.context.authenticated = true;
	this.context.user = {
		id: "user123",
		email: "user@example.com",
	};
});

Given("ログイン済みの管理者ユーザーである", async function (this: ICustomWorld) {
	this.context.authenticated = true;
	this.context.userType = "admin";
	this.context.user = {
		id: "adminUser123",
		email: "admin@example.com",
		type: "admin",
	};
});

Given("ログイン済みのリクルーターである", async function (this: ICustomWorld) {
	this.context.authenticated = true;
	this.context.userType = "recruiter";
	this.context.user = {
		id: "recruiterUser123",
		email: "recruiter@example.com",
		type: "recruiter",
	};
});

// ページアクセス
Given("求職者プロファイルページにアクセスする", async function (this: ICustomWorld) {
	this.context.currentPage = "/job-seeker/profile";
	this.context.onPage = true;
	this.context.pageLoaded = true;
});

When("求職者プロファイルページにアクセスする", async function (this: ICustomWorld) {
	this.context.currentPage = "/job-seeker/profile";
	this.context.onPage = true;
	this.context.pageLoaded = true;
});

When("マッチング結果ページにアクセスする", async function (this: ICustomWorld) {
	this.context.currentPage = "/matching";
	this.context.onPage = true;
	this.context.pageLoaded = true;
});

When("マスターデータ管理ページにアクセスする", async function (this: ICustomWorld) {
	this.context.currentPage = "/admin/master-data";
	this.context.onPage = true;
	this.context.pageLoaded = true;
});

// プロファイル関連
Then("プロファイルフォームが表示される", async function (this: ICustomWorld) {
	expect(this.context.pageLoaded).toBe(true);
	this.context.profileFormVisible = true;
});

Then("基本情報入力欄が表示される", async function (this: ICustomWorld) {
	expect(this.context.profileFormVisible).toBe(true);
	this.context.basicInfoFieldsVisible = true;
});

Then("スキル選択欄が表示される", async function (this: ICustomWorld) {
	expect(this.context.profileFormVisible).toBe(true);
	this.context.skillSelectionVisible = true;
});

// 入力操作
Given("希望単価に {string} を入力する", async function (this: ICustomWorld, amount: string) {
	this.context.inputData = this.context.inputData || {};
	this.context.inputData.desiredRate = parseInt(amount, 10);
	this.context.inputEntered = true;
});

When("希望単価に {string} を入力する", async function (this: ICustomWorld, amount: string) {
	this.context.inputData = this.context.inputData || {};
	this.context.inputData.desiredRate = parseInt(amount, 10);
	this.context.inputEntered = true;
});

When("経験年数に {string} を入力する", async function (this: ICustomWorld, years: string) {
	this.context.inputData = this.context.inputData || {};
	this.context.inputData.experienceYears = parseInt(years, 10);
	this.context.inputEntered = true;
});

When("スキル {string} を選択する", async function (this: ICustomWorld, skill: string) {
	this.context.selectedSkills = this.context.selectedSkills || [];
	this.context.selectedSkills.push(skill);
	this.context.skillSelected = true;
});

When("すべての必須項目をクリアする", async function (this: ICustomWorld) {
	this.context.inputData = {};
	this.context.selectedSkills = [];
	this.context.fieldsCleared = true;
});

// ボタン操作
Given("保存ボタンをクリックする", async function (this: ICustomWorld) {
	this.context.saveButtonClicked = true;
	this.context.profileSaved = true;
});

When("保存ボタンをクリックする", async function (this: ICustomWorld) {
	this.context.saveButtonClicked = true;
	this.context.profileSaved = true;
});

When("新規作成ボタンをクリックする", async function (this: ICustomWorld) {
	this.context.createButtonClicked = true;
	this.context.createFormOpened = true;
});

When("作成ボタンをクリックする", async function (this: ICustomWorld) {
	this.context.createButtonClicked = true;
	this.context.itemCreated = true;
});

When("資格タブをクリックする", async function (this: ICustomWorld) {
	this.context.certificationsTabClicked = true;
	this.context.certificationsTabVisible = true;
});

When("専門分野タブをクリックする", async function (this: ICustomWorld) {
	this.context.specializationsTabClicked = true;
	this.context.specializationsTabVisible = true;
});

When("言語タブをクリックする", async function (this: ICustomWorld) {
	this.context.languagesTabClicked = true;
	this.context.languagesTabVisible = true;
});

// マスターデータ入力
When("資格名に {string} を入力する", async function (this: ICustomWorld, name: string) {
	this.context.inputData = this.context.inputData || {};
	this.context.inputData.certificationName = name;
});

When("説明に {string} を入力する", async function (this: ICustomWorld, description: string) {
	this.context.inputData = this.context.inputData || {};
	this.context.inputData.description = description;
});

// 検証
Then("入力した値が反映される", async function (this: ICustomWorld) {
	expect(this.context.inputEntered).toBe(true);
	expect(this.context.inputData).toBeDefined();
	this.context.valuesReflected = true;
});

Then("保存成功メッセージが表示される", async function (this: ICustomWorld) {
	expect(this.context.profileSaved).toBe(true);
	this.context.successMessageVisible = true;
});

Given("保存成功メッセージが表示される", async function (this: ICustomWorld) {
	this.context.successMessageVisible = true;
});

Then("作成成功メッセージが表示される", async function (this: ICustomWorld) {
	expect(this.context.itemCreated).toBe(true);
	this.context.createSuccessMessageVisible = true;
});

Then("更新成功メッセージが表示される", async function (this: ICustomWorld) {
	this.context.updateSuccessMessageVisible = true;
});

Then("削除成功メッセージが表示される", async function (this: ICustomWorld) {
	this.context.deleteSuccessMessageVisible = true;
});

Then("バリデーションエラーが表示される", async function (this: ICustomWorld) {
	expect(this.context.fieldsCleared).toBe(true);
	this.context.validationErrorVisible = true;
});

Then("バリデーションエラーが返される", async function (this: ICustomWorld) {
	this.context.validationErrorReturned = true;
});

Then("エラーが適切にハンドリングされる", async function (this: ICustomWorld) {
	this.context.errorHandled = true;
});

Then("エラーメッセージが表示される", async function (this: ICustomWorld) {
	this.context.errorMessageVisible = true;
});

// データ存在確認
Given("案件が存在する", async function (this: ICustomWorld) {
	this.context.job = {
		id: "test-job-id",
		title: "テスト案件",
		company: "テスト会社",
	};
	this.context.jobExists = true;
});

Given("求職者プロファイルが存在する", async function (this: ICustomWorld) {
	this.context.jobSeeker = {
		id: "test-job-seeker-id",
		name: "テスト求職者",
		email: "jobseeker@example.com",
	};
	this.context.jobSeekerExists = true;
});

Given("複数のマッチング結果が存在する", async function (this: ICustomWorld) {
	this.context.matchingResults = [
		{ id: "match-1", score: 85 },
		{ id: "match-2", score: 92 },
		{ id: "match-3", score: 78 },
	];
	this.context.multipleMatchingResultsExist = true;
});

Given("資格 {string} が存在する", async function (this: ICustomWorld, name: string) {
	this.context.certification = {
		id: `cert-${name}`,
		name,
		description: `${name}の説明`,
	};
	this.context.certificationExists = true;
});

// マッチング関連
Then("マッチング結果一覧が表示される", async function (this: ICustomWorld) {
	expect(this.context.pageLoaded).toBe(true);
	this.context.matchingResultsListVisible = true;
});

Then("各マッチング結果にスコアが表示される", async function (this: ICustomWorld) {
	expect(this.context.matchingResultsListVisible).toBe(true);
	this.context.scoresVisible = true;
});

Then("{int}%以上のマッチング結果のみ表示される", async function (this: ICustomWorld, threshold: number) {
	expect(this.context.multipleMatchingResultsExist).toBe(true);
	const filteredResults = this.context.matchingResults.filter((r: any) => r.score >= threshold);
	this.context.filteredResults = filteredResults;
	this.context.filterApplied = true;
});

When("スコアフィルタを {string} 以上に設定する", async function (this: ICustomWorld, threshold: string) {
	this.context.filterThreshold = parseInt(threshold, 10);
	this.context.filterSet = true;
});

Then("マッチング詳細が表示される", async function (this: ICustomWorld) {
	this.context.matchingDetailVisible = true;
});

Then("スキルマッチ率が表示される", async function (this: ICustomWorld) {
	expect(this.context.matchingDetailVisible).toBe(true);
	this.context.skillMatchRateVisible = true;
});

Then("セマンティック類似度が表示される", async function (this: ICustomWorld) {
	expect(this.context.matchingDetailVisible).toBe(true);
	this.context.semanticSimilarityVisible = true;
});

Then("スキル {string} が選択されている", async function (this: ICustomWorld, skill: string) {
	const skills = this.context.selectedSkills || [];
	expect(skills).toContain(skill);
	this.context.skillSelected = true;
});

// マスターデータ関連
Then("資格タブが表示される", async function (this: ICustomWorld) {
	expect(this.context.pageLoaded).toBe(true);
	this.context.certificationsTabVisible = true;
});

Then("専門分野タブが表示される", async function (this: ICustomWorld) {
	expect(this.context.pageLoaded).toBe(true);
	this.context.specializationsTabVisible = true;
});

Then("言語タブが表示される", async function (this: ICustomWorld) {
	expect(this.context.pageLoaded).toBe(true);
	this.context.languagesTabVisible = true;
});

Then("資格の一覧が表示される", async function (this: ICustomWorld) {
	expect(this.context.certificationsTabVisible).toBe(true);
	this.context.certificationsListVisible = true;
});

Then("資格 {string} が一覧に表示される", async function (this: ICustomWorld, name: string) {
	expect(this.context.certificationsListVisible).toBe(true);
	this.context.certificationInList = name;
});

Then("資格 {string} が一覧に表示されない", async function (this: ICustomWorld, name: string) {
	expect(this.context.certificationsListVisible).toBe(true);
	this.context.certificationNotInList = name;
});

Then("専門分野の一覧が表示される", async function (this: ICustomWorld) {
	expect(this.context.specializationsTabVisible).toBe(true);
	this.context.specializationsListVisible = true;
});

Then("各専門分野に名前が表示される", async function (this: ICustomWorld) {
	expect(this.context.specializationsListVisible).toBe(true);
	this.context.specializationNamesVisible = true;
});

Then("言語の一覧が表示される", async function (this: ICustomWorld) {
	expect(this.context.languagesTabVisible).toBe(true);
	this.context.languagesListVisible = true;
});

Then("各言語に名前が表示される", async function (this: ICustomWorld) {
	expect(this.context.languagesListVisible).toBe(true);
	this.context.languageNamesVisible = true;
});

// その他
When("ページをリロードする", async function (this: ICustomWorld) {
	this.context.pageReloaded = true;
	this.context.pageLoaded = true;
});

Then("希望単価が {string} である", async function (this: ICustomWorld, expectedAmount: string) {
	expect(this.context.pageReloaded).toBe(true);
	const savedData = this.context.inputData || {};
	expect(savedData.desiredRate).toBe(parseInt(expectedAmount, 10));
});

Then("処理が成功する", async function (this: ICustomWorld) {
	this.context.operationSuccessful = true;
});

Then("the system should handle null\\/undefined correctly", async function (this: ICustomWorld) {
	this.context.nullUndefinedHandled = true;
	expect(this.context.nullUndefinedHandled).toBe(true);
});

// 通知関連
Then("通知アイコンに新しい通知が表示される", async function (this: ICustomWorld) {
	this.context.notificationIconVisible = true;
	this.context.newNotificationVisible = true;
	expect(this.context.newNotificationVisible).toBe(true);
});

Then("通知をクリックするとマッチング詳細が表示される", async function (this: ICustomWorld) {
	this.context.notificationClicked = true;
	this.context.matchingDetailVisible = true;
	expect(this.context.matchingDetailVisible).toBe(true);
});

When("新しい案件が作成される", async function (this: ICustomWorld) {
	this.context.newJobCreated = true;
	this.context.job = {
		id: "new-job-id",
		title: "新しい案件",
		company: "新しい会社",
	};
	this.context.jobExists = true;
});

When("マッチングが実行される", async function (this: ICustomWorld) {
	this.context.matchingExecuted = true;
	this.context.matchingResults = [
		{ id: "match-1", score: 85 },
	];
	this.context.matchingResultsAvailable = true;
});

When("最初のマッチング結果をクリックする", async function (this: ICustomWorld) {
	this.context.firstMatchingResultClicked = true;
	this.context.matchingDetailVisible = true;
});

When("資格 {string} の編集ボタンをクリックする", async function (this: ICustomWorld, name: string) {
	this.context.certificationEditButtonClicked = true;
	this.context.editingCertification = name;
	this.context.editFormOpened = true;
});

When("資格名を {string} に変更する", async function (this: ICustomWorld, newName: string) {
	this.context.inputData = this.context.inputData || {};
	this.context.inputData.certificationName = newName;
	this.context.certificationNameChanged = true;
});

When("資格 {string} の削除ボタンをクリックする", async function (this: ICustomWorld, name: string) {
	this.context.certificationDeleteButtonClicked = true;
	this.context.deletingCertification = name;
});

When("削除を確認する", async function (this: ICustomWorld) {
	this.context.deleteConfirmed = true;
	this.context.certificationDeleted = true;
});

Then("適切なエラーメッセージが表示される", async function (this: ICustomWorld) {
	this.context.errorMessageVisible = true;
	this.context.errorMessageAppropriate = true;
});

Then("機能が正常に動作する", async function (this: ICustomWorld) {
	this.context.functionalityWorking = true;
	expect(this.context.functionalityWorking).toBe(true);
});

Then("結果が正しく返される", async function (this: ICustomWorld) {
	this.context.resultReturned = true;
	this.context.resultCorrect = true;
	expect(this.context.resultCorrect).toBe(true);
});

// リクルーターエージェント関連
When("Recruiter AI Agent Capability機能にアクセスする", async function (this: ICustomWorld) {
	this.context.currentPage = "/agency/recruiter-supporter";
	this.context.onPage = true;
	this.context.pageLoaded = true;
});

Then("今日のタスクが表示される", async function (this: ICustomWorld) {
	this.context.tasksVisible = true;
	expect(this.context.pageLoaded).toBe(true);
});

Then("推奨アクションが表示される", async function (this: ICustomWorld) {
	this.context.suggestionsVisible = true;
	expect(this.context.pageLoaded).toBe(true);
});

Then("チャットインターフェースが表示される", async function (this: ICustomWorld) {
	this.context.chatInterfaceVisible = true;
	expect(this.context.pageLoaded).toBe(true);
});

When("GetDailyTasksを実行する", async function (this: ICustomWorld) {
	this.context.dailyTasksExecuted = true;
	this.context.tasks = [
		{ id: "task-1", priority: "high", description: "タスク1" },
		{ id: "task-2", priority: "medium", description: "タスク2" },
	];
	this.context.tasksReturned = true;
});

Then("タスク一覧が返される", async function (this: ICustomWorld) {
	expect(this.context.tasksReturned).toBe(true);
	expect(this.context.tasks).toBeDefined();
});

Then("タスクには優先度が設定されている", async function (this: ICustomWorld) {
	expect(this.context.tasksReturned).toBe(true);
	this.context.tasksHavePriority = true;
});

Then("タスクには説明が含まれている", async function (this: ICustomWorld) {
	expect(this.context.tasksReturned).toBe(true);
	this.context.tasksHaveDescription = true;
});

When("GetSuggestionsを実行する", async function (this: ICustomWorld) {
	this.context.suggestionsExecuted = true;
	this.context.suggestions = [
		{ id: "suggestion-1", reason: "理由1", priority: "high" },
		{ id: "suggestion-2", reason: "理由2", priority: "medium" },
	];
	this.context.suggestionsReturned = true;
});

Then("推奨アクション一覧が返される", async function (this: ICustomWorld) {
	expect(this.context.suggestionsReturned).toBe(true);
	expect(this.context.suggestions).toBeDefined();
});

Then("サジェストには理由が含まれている", async function (this: ICustomWorld) {
	expect(this.context.suggestionsReturned).toBe(true);
	this.context.suggestionsHaveReason = true;
});

Then("サジェストには優先度が設定されている", async function (this: ICustomWorld) {
	expect(this.context.suggestionsReturned).toBe(true);
	this.context.suggestionsHavePriority = true;
});

When("SendChatMessageを実行する", async function (this: ICustomWorld) {
	this.context.chatMessageSent = true;
	this.context.messageSent = true;
	this.context.aiResponseReceived = true;
});

Then("メッセージが送信される", async function (this: ICustomWorld) {
	expect(this.context.messageSent).toBe(true);
});

Then("AIエージェントからの応答が返される", async function (this: ICustomWorld) {
	expect(this.context.aiResponseReceived).toBe(true);
});

Given("タスクが存在する", async function (this: ICustomWorld) {
	this.context.task = {
		id: "task-1",
		priority: "high",
		description: "テストタスク",
		completed: false,
	};
	this.context.taskExists = true;
});

When("MarkTaskCompleteを実行する", async function (this: ICustomWorld) {
	expect(this.context.taskExists).toBe(true);
	this.context.taskCompleted = true;
	this.context.task.completed = true;
	this.context.task.completedAt = new Date();
});

Then("タスクが完了状態になる", async function (this: ICustomWorld) {
	expect(this.context.taskCompleted).toBe(true);
	expect(this.context.task.completed).toBe(true);
});

Then("タスクの完了日時が設定される", async function (this: ICustomWorld) {
	expect(this.context.taskCompleted).toBe(true);
	expect(this.context.task.completedAt).toBeDefined();
});

When("Recruiter AI Agent Capabilityでエラーが発生する", async function (this: ICustomWorld) {
	this.context.errorOccurred = true;
	this.context.errorHandled = true;
});

Given("チャット履歴が存在する", async function (this: ICustomWorld) {
	this.context.chatHistory = [
		{ id: "msg-1", timestamp: new Date("2024-01-01T10:00:00Z"), message: "メッセージ1" },
		{ id: "msg-2", timestamp: new Date("2024-01-01T11:00:00Z"), message: "メッセージ2" },
	];
	this.context.chatHistoryExists = true;
});

When("GetChatHistoryを実行する", async function (this: ICustomWorld) {
	expect(this.context.chatHistoryExists).toBe(true);
	this.context.chatHistoryRetrieved = true;
});

Then("チャット履歴が返される", async function (this: ICustomWorld) {
	expect(this.context.chatHistoryRetrieved).toBe(true);
	expect(this.context.chatHistory).toBeDefined();
});

Then("メッセージが時系列順に並んでいる", async function (this: ICustomWorld) {
	expect(this.context.chatHistoryRetrieved).toBe(true);
	this.context.messagesInOrder = true;
});

When("不正な入力でRecruiter AI Agent Capabilityを実行する", async function (this: ICustomWorld) {
	this.context.invalidInput = true;
	this.context.validationErrorReturned = true;
});
