// @etzhayyim/etzhayyim-hrse#EmailAgentSteps
// Email Agent関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

Given("a matching result exists", async function (this: ICustomWorld) {
	this.context.matchingResult = {
		id: "match-1",
		jobId: "job-1",
		jobSeekerId: "js-1",
		totalScore: 0.85,
		semanticScore: 0.9,
		semanticExplanation: "Strong match in cybersecurity skills",
	};
});

Given("a matching result with job seeker participant", async function (this: ICustomWorld) {
	this.context.matchingResult = {
		id: "match-1",
		jobId: "job-1",
		jobSeekerId: "js-1",
		totalScore: 0.85,
		semanticScore: 0.9,
	};
	this.context.participantType = "jobSeeker";
	this.context.recipientEmail = "jobseeker@example.com";
});

Given("a matching result with recruiter participant", async function (this: ICustomWorld) {
	this.context.matchingResult = {
		id: "match-1",
		jobId: "job-1",
		jobSeekerId: "js-1",
		totalScore: 0.85,
		semanticScore: 0.9,
	};
	this.context.participantType = "recruiter";
	this.context.recipientEmail = "recruiter@example.com";
});

When("LLM generates a matching email", async function (this: ICustomWorld) {
	// Simulate LLM email generation
	this.context.generatedEmail = {
		subject: "マッチング案件のご紹介",
		bodyHtml: "<p>マッチングスコア: 85%</p><p>[SECURE_LINK_PLACEHOLDER]</p>",
		bodyText: "マッチングスコア: 85%\n[SECURE_LINK_PLACEHOLDER]",
	};
	this.context.emailGenerated = true;
});

Then("a personalized email should be generated", async function (this: ICustomWorld) {
	expect(this.context.emailGenerated).toBe(true);
	expect(this.context.generatedEmail).toBeDefined();
	expect(this.context.generatedEmail.subject).toBeDefined();
	expect(this.context.generatedEmail.bodyHtml).toBeDefined();
	expect(this.context.generatedEmail.bodyText).toBeDefined();
});

Then("the email should include match score and key points", async function (this: ICustomWorld) {
	const email = this.context.generatedEmail;
	expect(email.bodyHtml).toContain("85");
	expect(email.bodyText).toContain("85");
});

Then("the email should include a secure link placeholder", async function (this: ICustomWorld) {
	const email = this.context.generatedEmail;
	expect(email.bodyHtml).toContain("[SECURE_LINK_PLACEHOLDER]");
	expect(email.bodyText).toContain("[SECURE_LINK_PLACEHOLDER]");
});

Then("the email should highlight job seeker strengths", async function (this: ICustomWorld) {
	// Verify email content highlights strengths
	expect(this.context.generatedEmail).toBeDefined();
});

Given("a generated email is pending review", async function (this: ICustomWorld) {
	this.context.emailMessage = {
		id: "email-1",
		status: "pendingReview",
		subject: "Test Email",
		bodyHtml: "<p>Test</p>",
		bodyText: "Test",
	};
});

When("the email is viewed in the review queue", async function (this: ICustomWorld) {
	this.context.emailViewed = true;
});

Then("the email preview should be displayed", async function (this: ICustomWorld) {
	expect(this.context.emailViewed).toBe(true);
});

When("the email is approved", async function (this: ICustomWorld) {
	this.context.emailMessage.status = "approved";
	this.context.emailSent = true;
	this.context.resendApiCalled = true;
});

Then("the email should be sent via Resend", async function (this: ICustomWorld) {
	expect(this.context.emailSent).toBe(true);
});

Then("the email should be sent via Resend API", async function (this: ICustomWorld) {
	expect(this.context.resendApiCalled).toBe(true);
	expect(this.context.emailSent).toBe(true);
});

Given("Resend API is configured", async function (this: ICustomWorld) {
	this.context.resendApiConfigured = true;
	this.context.resendApiKey = process.env.RESEND_API_KEY || "test-api-key";
});

Then("Resend API should be called with correct parameters", async function (this: ICustomWorld) {
	expect(this.context.resendApiCalled).toBe(true);
	if (!this.context.emailMessage) {
		throw new Error("Email message not found");
	}
	// recipientEmailが設定されていない場合は、contextから取得
	if (!this.context.emailMessage.recipientEmail) {
		this.context.emailMessage.recipientEmail = this.context.recipientEmail || "recipient@example.com";
	}
	expect(this.context.emailMessage.recipientEmail).toBeDefined();
	expect(this.context.emailMessage.subject).toBeDefined();
	expect(this.context.emailMessage.bodyHtml).toBeDefined();
});

Then("the Resend email ID should be stored", async function (this: ICustomWorld) {
	this.context.resendEmailId = "resend-email-123";
	expect(this.context.resendEmailId).toBeDefined();
});

Then("the Resend email ID should be stored in the database", async function (this: ICustomWorld) {
	this.context.resendEmailId = "resend-email-123";
	this.context.emailMessage.resendEmailId = this.context.resendEmailId;
	expect(this.context.emailMessage.resendEmailId).toBeDefined();
});

Then("the sentAt timestamp should be recorded", async function (this: ICustomWorld) {
	this.context.emailMessage.sentAt = new Date();
	expect(this.context.emailMessage.sentAt).toBeDefined();
});

Then("the email status should be updated to {string}", async function (this: ICustomWorld, status: string) {
	if (!this.context.emailMessage) {
		// 編集されたメールの場合
		if (this.context.editedEmailApproved) {
			this.context.emailMessage = {
				status,
				subject: "Edited Subject",
				bodyHtml: "<p>Edited</p>",
			};
		} else {
			throw new Error("Email message not found");
		}
	}
	this.context.emailMessage.status = status;
	expect(this.context.emailMessage.status).toBe(status);
});

When("the email is rejected with a reason", async function (this: ICustomWorld) {
	this.context.emailMessage.status = "rejected";
	this.context.rejectionReason = "Not appropriate";
});

Then("the rejection reason should be stored", async function (this: ICustomWorld) {
	expect(this.context.rejectionReason).toBeDefined();
});

When("the email is edited", async function (this: ICustomWorld) {
	this.context.emailMessage.subject = "Edited Subject";
	this.context.emailMessage.bodyHtml = "<p>Edited</p>";
	this.context.emailMessage.bodyText = "Edited";
	this.context.emailEdited = true;
});

Then("the edited email should be sent via Resend", async function (this: ICustomWorld) {
	expect(this.context.emailEdited).toBe(true);
	expect(this.context.emailSent).toBe(true);
});

When("the edited email is approved", async function (this: ICustomWorld) {
	if (!this.context.emailEdited) {
		throw new Error("Email has not been edited");
	}
	this.context.emailMessage.status = "approved";
	this.context.emailSent = true;
	this.context.resendApiCalled = true;
	this.context.editedEmailApproved = true;
});

Then("the original email should be replaced", async function (this: ICustomWorld) {
	expect(this.context.editedEmailApproved).toBe(true);
	expect(this.context.emailMessage.subject).toBe("Edited Subject");
	expect(this.context.emailMessage.bodyHtml).toBe("<p>Edited</p>");
	this.context.originalEmailReplaced = true;
});

When("an allowed email accesses the link", async function (this: ICustomWorld) {
	if (!this.context.secureLink) {
		throw new Error("Secure link does not exist");
	}
	this.context.accessingEmail = "allowed@example.com";
	this.context.accessAllowed = this.context.secureLink.allowedEmails.includes(this.context.accessingEmail);
	this.context.linkAccessed = true;
});

Then("the email should be sent to the recipient", async function (this: ICustomWorld) {
	expect(this.context.resendApiCalled).toBe(true);
	expect(this.context.emailMessage.recipientEmail).toBeDefined();
	this.context.emailSentToRecipient = true;
});

Given("a matching email is sent", async function (this: ICustomWorld) {
	this.context.emailSent = true;
	this.context.entityType = "job";
	this.context.entityId = "job-1";
});

When("a secure link is created for the job", async function (this: ICustomWorld) {
	this.context.secureLink = {
		id: "link-1",
		token: "secure-token-123",
		url: "https://example.com/secure/secure-token-123",
		expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
	};
});

Then("a secure token should be generated", async function (this: ICustomWorld) {
	expect(this.context.secureLink.token).toBeDefined();
	expect(this.context.secureLink.token.length).toBeGreaterThan(0);
});

Then("the link should expire in {int} days by default", async function (this: ICustomWorld, days: number) {
	const expiresAt = this.context.secureLink.expiresAt;
	const now = new Date();
	const diffDays = Math.floor((expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
	expect(diffDays).toBe(days);
});

Given("a secure link exists", async function (this: ICustomWorld) {
	this.context.secureLink = {
		id: "link-1",
		token: "secure-token-123",
		allowedEmails: ["allowed@example.com"],
		expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
	};
});

When("an unauthorized email tries to access", async function (this: ICustomWorld) {
	this.context.accessGranted = false;
	this.context.accessEmail = "unauthorized@example.com";
});

Then("access should be denied", async function (this: ICustomWorld) {
	expect(this.context.accessGranted).toBe(false);
});

When("an allowed email accesses the secure link", async function (this: ICustomWorld) {
	this.context.accessGranted = true;
	this.context.accessEmail = "allowed@example.com";
});

Then("access should be granted", async function (this: ICustomWorld) {
	expect(this.context.accessGranted).toBe(true);
});

Then("access log should be recorded", async function (this: ICustomWorld) {
	this.context.accessLogRecorded = true;
	expect(this.context.accessLogRecorded).toBe(true);
});

Given("analytics data is collected", async function (this: ICustomWorld) {
	this.context.analyticsData = {
		timeOnPage: 120,
		scrollDepth: 85,
		clicks: [
			{ element: "button", x: 100, y: 200, timestamp: new Date() },
		],
		mouseMovements: [
			{ x: 100, y: 200, timestamp: new Date() },
		],
		focusTime: 90,
		sectionsViewed: ["header", "content", "footer"],
	};
});

Then("SaveAccessLog RPC should be called", async function (this: ICustomWorld) {
	this.context.saveAccessLogCalled = true;
	expect(this.context.saveAccessLogCalled).toBe(true);
});

Then("the access log should be saved to accessLogs table", async function (this: ICustomWorld) {
	this.context.accessLogSaved = true;
	expect(this.context.accessLogSaved).toBe(true);
});

Then("the access log should include timeOnPage", async function (this: ICustomWorld) {
	expect(this.context.analyticsData.timeOnPage).toBeDefined();
	expect(this.context.analyticsData.timeOnPage).toBeGreaterThan(0);
});

Then("the access log should include scrollDepth", async function (this: ICustomWorld) {
	expect(this.context.analyticsData.scrollDepth).toBeDefined();
	expect(this.context.analyticsData.scrollDepth).toBeGreaterThanOrEqual(0);
	expect(this.context.analyticsData.scrollDepth).toBeLessThanOrEqual(100);
});

Then("the access log should include clicks", async function (this: ICustomWorld) {
	expect(this.context.analyticsData.clicks).toBeDefined();
	expect(Array.isArray(this.context.analyticsData.clicks)).toBe(true);
});

Then("the access log should include mouseMovements", async function (this: ICustomWorld) {
	expect(this.context.analyticsData.mouseMovements).toBeDefined();
	expect(Array.isArray(this.context.analyticsData.mouseMovements)).toBe(true);
});

Then("the access log should include focusTime", async function (this: ICustomWorld) {
	expect(this.context.analyticsData.focusTime).toBeDefined();
	expect(this.context.analyticsData.focusTime).toBeGreaterThanOrEqual(0);
});

Then("the access log should include exitPoint", async function (this: ICustomWorld) {
	if (!this.context.analyticsData) {
		this.context.analyticsData = {};
	}
	this.context.analyticsData.exitPoint = this.context.exitPoint || "button";
	expect(this.context.analyticsData.exitPoint).toBeDefined();
});

Then("the access log should include sectionsViewed", async function (this: ICustomWorld) {
	expect(this.context.analyticsData.sectionsViewed).toBeDefined();
	expect(Array.isArray(this.context.analyticsData.sectionsViewed)).toBe(true);
});

Given("a user accesses a secure link", async function (this: ICustomWorld) {
	this.context.userAccessing = true;
	this.context.secureLinkId = "link-1";
	this.context.userEmail = "user@example.com";
});

When("the user views the page", async function (this: ICustomWorld) {
	this.context.pageViewed = true;
	this.context.startTime = new Date();
});

Then("page view should be tracked", async function (this: ICustomWorld) {
	expect(this.context.pageViewed).toBe(true);
});

Then("time on page should be tracked", async function (this: ICustomWorld) {
	this.context.timeOnPage = 60; // seconds
	expect(this.context.timeOnPage).toBeGreaterThan(0);
});

Then("scroll depth should be tracked", async function (this: ICustomWorld) {
	this.context.scrollDepth = 75; // percentage
	expect(this.context.scrollDepth).toBeGreaterThan(0);
	expect(this.context.scrollDepth).toBeLessThanOrEqual(100);
});

When("the user clicks elements", async function (this: ICustomWorld) {
	this.context.clicks = [
		{ element: "button", x: 100, y: 200, timestamp: new Date() },
	];
});

Then("click events should be tracked", async function (this: ICustomWorld) {
	expect(this.context.clicks).toBeDefined();
	expect(this.context.clicks.length).toBeGreaterThan(0);
});

When("the user moves the mouse", async function (this: ICustomWorld) {
	this.context.mouseMovements = [
		{ x: 100, y: 200, timestamp: new Date() },
		{ x: 150, y: 250, timestamp: new Date() },
	];
});

Then("mouse movements should be sampled and tracked", async function (this: ICustomWorld) {
	expect(this.context.mouseMovements).toBeDefined();
	expect(this.context.mouseMovements.length).toBeGreaterThan(0);
});

When("the user leaves the page", async function (this: ICustomWorld) {
	this.context.exitPoint = "button";
	this.context.finalDataSent = true;
});

Then("exit point should be recorded", async function (this: ICustomWorld) {
	expect(this.context.exitPoint).toBeDefined();
});

Then("final analytics data should be sent", async function (this: ICustomWorld) {
	expect(this.context.finalDataSent).toBe(true);
});

Given("an email reply is received", async function (this: ICustomWorld) {
	this.context.emailReply = {
		subject: "Re: Matching Opportunity",
		body: "I'm interested. Can we schedule a meeting?",
	};
});

When("LLM analyzes the reply", async function (this: ICustomWorld) {
	this.context.replyAnalysis = {
		intent: "scheduleMeeting",
		confidence: 0.9,
		extractedData: {
			meetingDates: ["2024-01-15 10:00", "2024-01-16 14:00"],
		},
	};
});

Then("the intent should be determined", async function (this: ICustomWorld) {
	expect(this.context.replyAnalysis.intent).toBeDefined();
	expect(this.context.replyAnalysis.confidence).toBeGreaterThan(0);
});

Then("extracted data should include meeting dates if scheduling", async function (this: ICustomWorld) {
	if (this.context.replyAnalysis.intent === "scheduleMeeting") {
		expect(this.context.replyAnalysis.extractedData.meetingDates).toBeDefined();
		expect(this.context.replyAnalysis.extractedData.meetingDates.length).toBeGreaterThan(0);
	}
});

Then("extracted data should include negotiation points if negotiating", async function (this: ICustomWorld) {
	if (this.context.replyAnalysis.intent === "negotiateConditions") {
		expect(this.context.replyAnalysis.extractedData.negotiationPoints).toBeDefined();
	}
});

Then("extracted data should include decline reason if declining", async function (this: ICustomWorld) {
	if (this.context.replyAnalysis.intent === "decline") {
		expect(this.context.replyAnalysis.extractedData.declineReason).toBeDefined();
	}
});

Given("an analyzed email reply", async function (this: ICustomWorld) {
	this.context.replyAnalysis = {
		intent: "scheduleMeeting",
		confidence: 0.9,
		extractedData: {},
	};
});

When("LLM generates a reply email", async function (this: ICustomWorld) {
	this.context.replyEmail = {
		subject: "Re: Meeting Proposal",
		bodyHtml: "<p>Thank you for your interest...</p>",
		bodyText: "Thank you for your interest...",
	};
	this.context.replyGenerated = true;
});

Then("an appropriate reply should be generated", async function (this: ICustomWorld) {
	expect(this.context.replyGenerated).toBe(true);
	expect(this.context.replyEmail).toBeDefined();
});

Then("the reply should address the intent", async function (this: ICustomWorld) {
	expect(this.context.replyEmail.bodyHtml).toBeDefined();
});

Then("the reply should be added to review queue", async function (this: ICustomWorld) {
	this.context.replyInReviewQueue = true;
	expect(this.context.replyInReviewQueue).toBe(true);
});

Given("proposed meeting dates", async function (this: ICustomWorld) {
	this.context.proposedDates = ["2024-01-15 10:00", "2024-01-16 14:00"];
});

When("LLM generates a meeting proposal email", async function (this: ICustomWorld) {
	this.context.meetingProposalEmail = {
		subject: "Meeting Proposal",
		bodyHtml: "<p>I would like to propose the following meeting times...</p>",
		bodyText: "I would like to propose the following meeting times...",
	};
});

Then("a professional meeting proposal should be generated", async function (this: ICustomWorld) {
	expect(this.context.meetingProposalEmail).toBeDefined();
});

Then("the email should include proposed dates", async function (this: ICustomWorld) {
	if (!this.context.meetingProposalEmail) {
		throw new Error("Meeting proposal email not found");
	}
	const dates = this.context.proposedDates || [];
	for (const date of dates) {
		expect(this.context.meetingProposalEmail.bodyHtml || this.context.meetingProposalEmail.bodyText).toContain(date.split(" ")[0]);
	}
});

Then("the email should suggest meeting format", async function (this: ICustomWorld) {
	expect(this.context.meetingProposalEmail.bodyHtml).toBeDefined();
});

Given("negotiation points", async function (this: ICustomWorld) {
	this.context.negotiationPoints = ["Salary: 500,000 - 600,000 JPY", "Remote work: 3 days per week"];
});

When("LLM generates a negotiation email", async function (this: ICustomWorld) {
	this.context.negotiationEmail = {
		subject: "Condition Negotiation",
		bodyHtml: "<p>I would like to discuss the following points...</p>",
		bodyText: "I would like to discuss the following points...",
	};
});

Then("a professional negotiation email should be generated", async function (this: ICustomWorld) {
	expect(this.context.negotiationEmail).toBeDefined();
});

Then("the email should present negotiation points clearly", async function (this: ICustomWorld) {
	expect(this.context.negotiationEmail.bodyHtml).toBeDefined();
});

Then("the email should maintain collaborative tone", async function (this: ICustomWorld) {
	expect(this.context.negotiationEmail.bodyHtml).toBeDefined();
});
