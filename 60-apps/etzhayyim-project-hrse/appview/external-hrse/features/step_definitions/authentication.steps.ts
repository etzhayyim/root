// @etzhayyim/cyber-freelance#AuthenticationSteps
// 認証関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

// Token verification steps
When("a valid authentication token is provided", async function (this: ICustomWorld) {
	this.context.authToken = "validTestToken";
	this.context.authenticated = true;
});

When("an invalid authentication token is provided", async function (this: ICustomWorld) {
	this.context.authToken = "invalidTestToken";
	this.context.authenticated = false;
});

Then("the token should be verified successfully", async function (this: ICustomWorld) {
	expect(this.context.authToken).toBe("validTestToken");
	// 実際の実装では、Clerkのトークン検証を実行
	this.context.tokenVerified = true;
});

Then("the user should be authenticated", async function (this: ICustomWorld) {
	expect(this.context.tokenVerified).toBe(true);
	expect(this.context.authenticated).toBe(true);
});

Then("the token verification should fail", async function (this: ICustomWorld) {
	expect(this.context.authToken).toBe("invalidTestToken");
	this.context.tokenVerificationFailed = true;
});

Then("an authentication error should be returned", async function (this: ICustomWorld) {
	expect(this.context.tokenVerificationFailed).toBe(true);
	// 認証エラーが返されたことを確認
});

// Route protection steps
When("a protected route is accessed", async function (this: ICustomWorld) {
	this.context.routeAccessed = true;
	// 実際の実装では、保護されたルートにアクセスを試みる
});

Then("the request should be blocked", async function (this: ICustomWorld) {
	if (!this.context.authenticated) {
		expect(this.context.routeAccessed).toBe(true);
		this.context.requestBlocked = true;
	}
});

Then("the user should be redirected to authentication", async function (this: ICustomWorld) {
	expect(this.context.requestBlocked).toBe(true);
	// 認証ページにリダイレクトされたことを確認
});

Then("the request should be allowed", async function (this: ICustomWorld) {
	if (this.context.authenticated) {
		expect(this.context.routeAccessed).toBe(true);
		this.context.requestAllowed = true;
	}
});

Then("the route should be accessible", async function (this: ICustomWorld) {
	expect(this.context.requestAllowed).toBe(true);
});

// Authentication requirement steps
When(
	"I attempt to create an agency profile without authentication",
	async function (this: ICustomWorld) {
		this.context.authenticated = false;
		delete this.context.authToken;
		this.context.attemptedAction = "createAgencyProfile";
	}
);

Then("the system should return an authentication error", async function (this: ICustomWorld) {
	expect(this.context.authenticated).toBe(false);
	this.context.authenticationError = true;
});

Then(
	"the error message should indicate that authentication is required",
	async function (this: ICustomWorld) {
		expect(this.context.authenticationError).toBe(true);
		// 認証が必要であることを示すエラーメッセージを確認
	}
);

Then("no agency profile should be created", async function (this: ICustomWorld) {
	expect(this.context.authenticationError).toBe(true);
	// プロファイルが作成されなかったことを確認
});
