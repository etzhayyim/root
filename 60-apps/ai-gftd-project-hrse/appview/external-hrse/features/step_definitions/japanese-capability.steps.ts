// @etzhayyim/cyber-freelance#JapaneseCapabilitySteps
// 日本語Capability関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import type { ICustomWorld } from "../support/world.js";

// Capability実行ステップ（日本語）
const capabilityNames: Record<string, string> = {
	"Agency Profile Management Capability": "Agency Profile Management Capability",
	"Authentication Capability": "Authentication Capability",
	"Clerk Subscription Management Capability": "Clerk Subscription Management Capability",
	"Email Analysis Capability": "Email Analysis Capability",
	"Event Trigger Capability": "Event Trigger Capability",
	"LLM Integration Capability": "LLM Integration Capability",
	"Master Data Management Capability": "Master Data Management Capability",
	"Matching Notification Capability": "Matching Notification Capability",
	"Record Routing Capability": "Record Routing Capability",
	"Resend Webhook Capability": "Resend Webhook Capability",
	"Semantic Matching Capability": "Semantic Matching Capability",
};

When("{string}を実行する", async function (this: ICustomWorld, capabilityName: string) {
	const englishName = capabilityNames[capabilityName] || capabilityName;
	this.context.capabilityName = englishName;
	this.context.capabilityInvoked = true;
});

When("{string}機能にアクセスする", async function (this: ICustomWorld, capabilityName: string) {
	const englishName = capabilityNames[capabilityName] || capabilityName;
	this.context.capabilityName = englishName;
	this.context.capabilityAccessed = true;
	this.context.capabilityInvoked = true;
});

When("{string}でエラーが発生する", async function (this: ICustomWorld, capabilityName: string) {
	const englishName = capabilityNames[capabilityName] || capabilityName;
	this.context.capabilityName = englishName;
	this.context.capabilityError = true;
});

When("不正な入力で{string}を実行する", async function (this: ICustomWorld, capabilityName: string) {
	const englishName = capabilityNames[capabilityName] || capabilityName;
	this.context.capabilityName = englishName;
	this.context.invalidInput = true;
});

// 英語のCapability名でもマッチするように追加
When("Agency Profile Management Capabilityを実行する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Agency Profile Management Capability";
	this.context.capabilityInvoked = true;
});

When("Agency Profile Management Capability機能にアクセスする", async function (this: ICustomWorld) {
	this.context.capabilityName = "Agency Profile Management Capability";
	this.context.capabilityAccessed = true;
	this.context.capabilityInvoked = true;
});

When("Agency Profile Management Capabilityでエラーが発生する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Agency Profile Management Capability";
	this.context.capabilityError = true;
});

When("Authentication Capabilityを実行する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Authentication Capability";
	this.context.capabilityInvoked = true;
});

When("Authentication Capability機能にアクセスする", async function (this: ICustomWorld) {
	this.context.capabilityName = "Authentication Capability";
	this.context.capabilityAccessed = true;
	this.context.capabilityInvoked = true;
});

When("Authentication Capabilityでエラーが発生する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Authentication Capability";
	this.context.capabilityError = true;
});

When("Clerk Subscription Management Capabilityを実行する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Clerk Subscription Management Capability";
	this.context.capabilityInvoked = true;
});

When("Clerk Subscription Management Capability機能にアクセスする", async function (this: ICustomWorld) {
	this.context.capabilityName = "Clerk Subscription Management Capability";
	this.context.capabilityAccessed = true;
	this.context.capabilityInvoked = true;
});

When("Clerk Subscription Management Capabilityでエラーが発生する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Clerk Subscription Management Capability";
	this.context.capabilityError = true;
});

When("Email Analysis Capabilityを実行する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Email Analysis Capability";
	this.context.capabilityInvoked = true;
});

When("Email Analysis Capability機能にアクセスする", async function (this: ICustomWorld) {
	this.context.capabilityName = "Email Analysis Capability";
	this.context.capabilityAccessed = true;
	this.context.capabilityInvoked = true;
});

When("Email Analysis Capabilityでエラーが発生する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Email Analysis Capability";
	this.context.capabilityError = true;
});

When("Event Trigger Capabilityを実行する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Event Trigger Capability";
	this.context.capabilityInvoked = true;
});

When("Event Trigger Capability機能にアクセスする", async function (this: ICustomWorld) {
	this.context.capabilityName = "Event Trigger Capability";
	this.context.capabilityAccessed = true;
	this.context.capabilityInvoked = true;
});

When("Event Trigger Capabilityでエラーが発生する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Event Trigger Capability";
	this.context.capabilityError = true;
});

When("LLM Integration Capabilityを実行する", async function (this: ICustomWorld) {
	this.context.capabilityName = "LLM Integration Capability";
	this.context.capabilityInvoked = true;
});

When("LLM Integration Capability機能にアクセスする", async function (this: ICustomWorld) {
	this.context.capabilityName = "LLM Integration Capability";
	this.context.capabilityAccessed = true;
	this.context.capabilityInvoked = true;
});

When("LLM Integration Capabilityでエラーが発生する", async function (this: ICustomWorld) {
	this.context.capabilityName = "LLM Integration Capability";
	this.context.capabilityError = true;
});

When("Master Data Management Capabilityを実行する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Master Data Management Capability";
	this.context.capabilityInvoked = true;
});

When("Master Data Management Capability機能にアクセスする", async function (this: ICustomWorld) {
	this.context.capabilityName = "Master Data Management Capability";
	this.context.capabilityAccessed = true;
	this.context.capabilityInvoked = true;
});

When("Master Data Management Capabilityでエラーが発生する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Master Data Management Capability";
	this.context.capabilityError = true;
});

When("Matching Notification Capabilityを実行する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Matching Notification Capability";
	this.context.capabilityInvoked = true;
});

When("Matching Notification Capability機能にアクセスする", async function (this: ICustomWorld) {
	this.context.capabilityName = "Matching Notification Capability";
	this.context.capabilityAccessed = true;
	this.context.capabilityInvoked = true;
});

When("Matching Notification Capabilityでエラーが発生する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Matching Notification Capability";
	this.context.capabilityError = true;
});

When("Record Routing Capabilityを実行する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Record Routing Capability";
	this.context.capabilityInvoked = true;
});

When("Record Routing Capability機能にアクセスする", async function (this: ICustomWorld) {
	this.context.capabilityName = "Record Routing Capability";
	this.context.capabilityAccessed = true;
	this.context.capabilityInvoked = true;
});

When("Record Routing Capabilityでエラーが発生する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Record Routing Capability";
	this.context.capabilityError = true;
});

When("Resend Webhook Capabilityを実行する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Resend Webhook Capability";
	this.context.capabilityInvoked = true;
});

When("Resend Webhook Capability機能にアクセスする", async function (this: ICustomWorld) {
	this.context.capabilityName = "Resend Webhook Capability";
	this.context.capabilityAccessed = true;
	this.context.capabilityInvoked = true;
});

When("Resend Webhook Capabilityでエラーが発生する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Resend Webhook Capability";
	this.context.capabilityError = true;
});

When("Semantic Matching Capabilityを実行する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Semantic Matching Capability";
	this.context.capabilityInvoked = true;
});

When("Semantic Matching Capability機能にアクセスする", async function (this: ICustomWorld) {
	this.context.capabilityName = "Semantic Matching Capability";
	this.context.capabilityAccessed = true;
	this.context.capabilityInvoked = true;
});

When("Semantic Matching Capabilityでエラーが発生する", async function (this: ICustomWorld) {
	this.context.capabilityName = "Semantic Matching Capability";
	this.context.capabilityError = true;
});


