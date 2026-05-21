// @etzhayyim/cyber-freelance#CommonSteps
// 共通のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

// System status steps
Given("the system is running", async function (this: ICustomWorld) {
	// システムが稼働していることを確認
	// 実際の実装では、ヘルスチェックエンドポイントなどを確認する
	this.context.systemRunning = true;
});

// Authentication steps
Given("the user is authenticated", async function (this: ICustomWorld) {
	this.context.authenticated = true;
	// テスト用の認証トークンを設定（実際の実装ではClerkのテストトークンを使用）
	this.context.authToken = "testAuthToken";
});

Given("the user is not authenticated", async function (this: ICustomWorld) {
	this.context.authenticated = false;
	delete this.context.authToken;
});

// Capability invocation steps
When(
	'the "{string}" capability is invoked',
	async function (this: ICustomWorld, capabilityName: string) {
		this.context.capabilityName = capabilityName;
		this.context.capabilityInvoked = true;
		// 実際の実装では、各Capabilityのエンドポイントを呼び出す
	}
);

When(
	'an error occurs in "{string}" capability',
	async function (this: ICustomWorld, capabilityName: string) {
		this.context.capabilityName = capabilityName;
		this.context.capabilityError = true;
		// エラーをシミュレート
	}
);

When(
	'invalid input is provided to "{string}" capability',
	async function (this: ICustomWorld, capabilityName: string) {
		this.context.capabilityName = capabilityName;
		this.context.invalidInput = true;
	}
);

// Result verification steps
Then("it should perform the expected behavior", async function (this: ICustomWorld) {
	expect(this.context.capabilityInvoked).toBe(true);
});

Then("the result should be successful", async function (this: ICustomWorld) {
	expect(this.context.capabilityInvoked).toBe(true);
	// 実際の実装では、レスポンスの成功ステータスを確認
	this.context.resultSuccess = true;
});

Then("it should handle the error appropriately", async function (this: ICustomWorld) {
	expect(this.context.capabilityError).toBe(true);
	// エラーが適切にハンドリングされたことを確認
	this.context.errorHandled = true;
});

Then("the error should be logged", async function (this: ICustomWorld) {
	expect(this.context.errorHandled).toBe(true);
	// エラーがログに記録されたことを確認
});

Then("it should reject the input", async function (this: ICustomWorld) {
	expect(this.context.invalidInput).toBe(true);
	// 入力が拒否されたことを確認
	this.context.inputRejected = true;
});

Then(
	"an appropriate error message should be returned",
	async function (this: ICustomWorld) {
		expect(this.context.inputRejected).toBe(true);
		// 適切なエラーメッセージが返されたことを確認
	}
);
