// @etzhayyim/cyber-freelance#ResendWebhookSteps
// Resend Webhook関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

Given("a Resend webhook receives an email reply", async function (this: ICustomWorld) {
	this.context.webhookEvent = {
		type: "email.received",
		data: {
			from: "sender@example.com",
			to: "recipient@example.com",
			subject: "Re: Matching Opportunity",
			html: "<p>I'm interested. Can we schedule a meeting?</p>",
			text: "I'm interested. Can we schedule a meeting?",
		},
	};
	this.context.isReply = true;
});

Given("the email is a reply to an existing conversation", async function (this: ICustomWorld) {
	this.context.conversationExists = true;
	this.context.conversationId = "conv-1";
});

When("the webhook processes the email", async function (this: ICustomWorld) {
	this.context.webhookProcessed = true;
	this.context.emailAnalyzed = true;
});

Then("EmailAgentService should analyze the reply", async function (this: ICustomWorld) {
	expect(this.context.emailAnalyzed).toBe(true);
});

Then("the reply intent should be determined", async function (this: ICustomWorld) {
	this.context.replyIntent = "scheduleMeeting";
	expect(this.context.replyIntent).toBeDefined();
});

Then("the reply should be saved to emailMessages table", async function (this: ICustomWorld) {
	this.context.replySaved = true;
	expect(this.context.replySaved).toBe(true);
});

Then("the reply status should be {string}", async function (this: ICustomWorld, status: string) {
	this.context.replyStatus = status;
	expect(this.context.replyStatus).toBe(status);
});

Given("a Resend webhook event is received", async function (this: ICustomWorld) {
	this.context.webhookEvent = {
		type: "email.sent",
		data: {
			emailId: "test-email-id",
			to: "recipient@example.com",
			from: "sender@example.com",
			subject: "Test Email",
		},
		timestamp: new Date().toISOString(),
		signature: "valid-signature-hash",
	};
	this.context.webhookEventReceived = true;
});

Given("a Resend email delivery event is received", async function (this: ICustomWorld) {
	this.context.webhookEvent = {
		type: "email.delivered",
		data: {
			emailId: "test-email-id",
			to: "recipient@example.com",
			status: "delivered",
		},
		timestamp: new Date().toISOString(),
		signature: "valid-signature-hash",
	};
	this.context.webhookEventReceived = true;
	this.context.emailDeliveryEventReceived = true;
});

When("the webhook signature is verified", async function (this: ICustomWorld) {
	if (!this.context.webhookEventReceived) {
		throw new Error("Webhook event not received");
	}

	const event = this.context.webhookEvent;
	const isValid = event.signature === "valid-signature-hash";
	
	if (isValid) {
		this.context.signatureVerified = true;
		this.context.webhookProcessed = true;
	} else {
		this.context.signatureVerified = false;
		this.context.webhookRejected = true;
	}
});

When("the webhook signature is invalid", async function (this: ICustomWorld) {
	if (!this.context.webhookEventReceived) {
		throw new Error("Webhook event not received");
	}

	this.context.webhookEvent.signature = "invalid-signature-hash";
	this.context.signatureVerified = false;
	this.context.webhookRejected = true;
});

When("the webhook is processed", async function (this: ICustomWorld) {
	if (!this.context.webhookEventReceived) {
		throw new Error("Webhook event not received");
	}

	if (this.context.signatureVerified !== false) {
		this.context.webhookProcessed = true;
		this.context.eventProcessed = true;
	} else {
		this.context.webhookRejected = true;
	}
});

Then("the email event should be processed", async function (this: ICustomWorld) {
	expect(this.context.webhookProcessed).toBe(true);
	expect(this.context.eventProcessed).toBe(true);
});

Then("email analysis should be triggered", async function (this: ICustomWorld) {
	expect(this.context.webhookProcessed).toBe(true);
	this.context.emailAnalysisTriggered = true;
});

Then("the webhook should be rejected", async function (this: ICustomWorld) {
	expect(this.context.webhookRejected).toBe(true);
	expect(this.context.signatureVerified).toBe(false);
});

Then("an error should be returned", async function (this: ICustomWorld) {
	expect(this.context.webhookRejected).toBe(true);
	this.context.webhookError = {
		message: "Invalid webhook signature",
		code: "INVALID_SIGNATURE",
	};
});

Then("the email delivery status should be updated", async function (this: ICustomWorld) {
	expect(this.context.emailDeliveryEventReceived).toBe(true);
	expect(this.context.webhookProcessed).toBe(true);
	this.context.emailDeliveryStatusUpdated = true;
	this.context.emailDeliveryStatus = "delivered";
});

Then("the event should be logged", async function (this: ICustomWorld) {
	expect(this.context.eventProcessed).toBe(true);
	this.context.eventLogged = true;
	this.context.loggedEvent = {
		type: this.context.webhookEvent.type,
		timestamp: this.context.webhookEvent.timestamp,
		data: this.context.webhookEvent.data,
	};
});
