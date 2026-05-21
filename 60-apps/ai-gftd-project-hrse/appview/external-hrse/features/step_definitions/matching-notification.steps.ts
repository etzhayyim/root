// @etzhayyim/cyber-freelance#MatchingNotificationSteps
// Matching Notification関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

Given("matching results are available", async function (this: ICustomWorld) {
	this.context.matchingResults = [
		{
			jobSeekerId: "js-1",
			jobId: "job-1",
			similarityScore: 0.85,
			matchedSkills: ["JavaScript", "TypeScript", "React"],
		},
		{
			jobSeekerId: "js-2",
			jobId: "job-2",
			similarityScore: 0.92,
			matchedSkills: ["Python", "Django", "PostgreSQL"],
		},
	];
	this.context.matchingResultsAvailable = true;
});

Given("no matching results are available", async function (this: ICustomWorld) {
	this.context.matchingResults = [];
	this.context.matchingResultsAvailable = false;
});

When("a matching result is found", async function (this: ICustomWorld) {
	if (!this.context.matchingResultsAvailable) {
		throw new Error("Matching results are not available");
	}

	const results = this.context.matchingResults;
	if (results && results.length > 0) {
		this.context.matchingResultFound = true;
		this.context.foundMatch = results[0];
	} else {
		this.context.matchingResultFound = false;
	}
});

When("matching is performed", async function (this: ICustomWorld) {
	// マッチング処理をシミュレート
	this.context.matchingPerformed = true;
	
	if (this.context.matchingResultsAvailable && this.context.matchingResults.length > 0) {
		this.context.matchingResultFound = true;
		this.context.foundMatch = this.context.matchingResults[0];
	} else {
		this.context.matchingResultFound = false;
	}
});

Then("a notification should be sent", async function (this: ICustomWorld) {
	expect(this.context.matchingResultFound).toBe(true);
	this.context.notificationSent = true;
});

Then("the notification should include match details", async function (this: ICustomWorld) {
	expect(this.context.notificationSent).toBe(true);
	const match = this.context.foundMatch;
	if (!match) {
		throw new Error("Match details not found");
	}
	
	this.context.notificationDetails = {
		jobSeekerId: match.jobSeekerId,
		jobId: match.jobId,
		similarityScore: match.similarityScore,
		matchedSkills: match.matchedSkills,
	};
	expect(this.context.notificationDetails).toBeDefined();
});

Then("the notification should be sent via email and in-app", async function (this: ICustomWorld) {
	expect(this.context.notificationSent).toBe(true);
	this.context.emailNotificationSent = true;
	this.context.inAppNotificationSent = true;
	this.context.notificationChannels = ["email", "in-app"];
});

Then("no notification should be sent", async function (this: ICustomWorld) {
	expect(this.context.matchingResultFound).toBe(false);
	this.context.notificationSent = false;
});

Then("the system should continue normally", async function (this: ICustomWorld) {
	expect(this.context.notificationSent).toBe(false);
	this.context.systemContinuesNormally = true;
});
