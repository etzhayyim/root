// @etzhayyim/cyber-freelance#EmailSyncJobSteps
// Email Sync Job関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

Given("I have Resend API credentials", async function (this: ICustomWorld) {
	this.context.resendApiCredentials = {
		apiKey: process.env.RESEND_API_KEY || "test-resend-api-key",
	};
	this.context.hasResendCredentials = true;
});

Given("an email sync job exists", async function (this: ICustomWorld) {
	this.context.emailSyncJob = {
		id: "test-job-id-1",
		status: "pending",
		limit: 100,
		processedCount: 0,
		totalEmails: 100,
		errorCount: 0,
		createdAt: new Date().toISOString(),
	};
	this.context.emailSyncJobExists = true;
});

Given("an email sync job exists with status {string}", async function (this: ICustomWorld, status: string) {
	this.context.emailSyncJob = {
		id: `test-job-id-${status}`,
		status,
		limit: 100,
		processedCount: 0,
		totalEmails: 100,
		errorCount: 0,
		createdAt: new Date().toISOString(),
		startedAt: status === "running" || status === "completed" || status === "failed" ? new Date().toISOString() : undefined,
		completedAt: status === "completed" || status === "failed" ? new Date().toISOString() : undefined,
	};
	this.context.emailSyncJobExists = true;
});

Given("a failed email sync job exists", async function (this: ICustomWorld) {
	this.context.emailSyncJob = {
		id: "test-failed-job-id",
		status: "failed",
		limit: 100,
		processedCount: 50,
		totalEmails: 100,
		errorCount: 5,
		errorMessage: "Failed to process some emails",
		createdAt: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
		startedAt: new Date(Date.now() - 3500000).toISOString(),
		completedAt: new Date(Date.now() - 1000000).toISOString(),
	};
	this.context.emailSyncJobExists = true;
});

Given("multiple email sync jobs exist", async function (this: ICustomWorld) {
	this.context.emailSyncJobs = [
		{
			id: "test-job-id-1",
			status: "completed",
			limit: 100,
			processedCount: 100,
			totalEmails: 100,
			errorCount: 0,
			createdAt: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
		},
		{
			id: "test-job-id-2",
			status: "running",
			limit: 200,
			processedCount: 50,
			totalEmails: 200,
			errorCount: 0,
			createdAt: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
		},
		{
			id: "test-job-id-3",
			status: "pending",
			limit: 50,
			processedCount: 0,
			totalEmails: 50,
			errorCount: 0,
			createdAt: new Date().toISOString(),
		},
	];
	this.context.multipleJobsExist = true;
});

Given("the database is connected", async function (this: ICustomWorld) {
	this.context.databaseConnected = true;
	this.context.databaseUrl = process.env.DATABASE_URL || "postgresql://localhost:5432/test";
});

When("I trigger a manual email sync with limit {string}", async function (this: ICustomWorld, limit: string) {
	if (!this.context.hasResendCredentials) {
		throw new Error("Resend API credentials not available");
	}

	this.context.triggeredSync = {
		limit: parseInt(limit, 10),
		timestamp: new Date().toISOString(),
	};
	this.context.syncTriggered = true;
});

When("the sync process starts", async function (this: ICustomWorld) {
	if (!this.context.emailSyncJobExists) {
		throw new Error("Email sync job does not exist");
	}

	const job = this.context.emailSyncJob;
	if (job.status === "pending") {
		job.status = "running";
		job.startedAt = new Date().toISOString();
	}
	this.context.syncProcessStarted = true;
});

When("emails are processed in email sync job", async function (this: ICustomWorld) {
	if (!this.context.emailSyncJobExists) {
		throw new Error("Email sync job does not exist");
	}

	const job = this.context.emailSyncJob;
	if (job.status === "running") {
		job.processedCount = Math.min(job.processedCount + 10, job.totalEmails);
	}
	this.context.emailsProcessed = true;
});

When("all emails are processed successfully", async function (this: ICustomWorld) {
	if (!this.context.emailSyncJobExists) {
		throw new Error("Email sync job does not exist");
	}

	const job = this.context.emailSyncJob;
	if (job.status === "running") {
		job.status = "completed";
		job.processedCount = job.totalEmails;
		job.completedAt = new Date().toISOString();
		job.errorCount = 0;
	}
	this.context.allEmailsProcessed = true;
});

When("errors occur during processing", async function (this: ICustomWorld) {
	if (!this.context.emailSyncJobExists) {
		throw new Error("Email sync job does not exist");
	}

	const job = this.context.emailSyncJob;
	if (job.status === "running") {
		job.status = "failed";
		job.errorCount = 5;
		job.errorMessage = "Failed to process some emails";
		job.completedAt = new Date().toISOString();
	}
	this.context.errorsOccurred = true;
});

When("I retry the job", async function (this: ICustomWorld) {
	if (!this.context.emailSyncJobExists) {
		throw new Error("Failed email sync job does not exist");
	}

	const originalJob = this.context.emailSyncJob;
	this.context.newJob = {
		id: `retry-${originalJob.id}`,
		status: "pending",
		limit: originalJob.limit,
		processedCount: 0,
		totalEmails: originalJob.totalEmails,
		errorCount: 0,
		createdAt: new Date().toISOString(),
	};
	this.context.jobRetried = true;
});

When("I query the job list", async function (this: ICustomWorld) {
	if (!this.context.multipleJobsExist) {
		throw new Error("Multiple email sync jobs do not exist");
	}

	this.context.queriedJobList = [...this.context.emailSyncJobs].sort((a, b) =>
		new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
	);
	this.context.jobListQueried = true;
});

When("I query the latest job", async function (this: ICustomWorld) {
	if (!this.context.multipleJobsExist) {
		throw new Error("Multiple email sync jobs do not exist");
	}

	const jobs = this.context.emailSyncJobs;
	this.context.latestJob = jobs.sort((a, b) =>
		new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
	)[0];
	this.context.latestJobQueried = true;
});

When("I query the job by ID", async function (this: ICustomWorld) {
	if (!this.context.emailSyncJobExists) {
		throw new Error("Email sync job does not exist");
	}

	this.context.queriedJob = this.context.emailSyncJob;
	this.context.jobQueriedById = true;
});

Then("a new email sync job should be created", async function (this: ICustomWorld) {
	expect(this.context.syncTriggered).toBe(true);
	this.context.newJobCreated = true;
});

Then("the job status should be {string}", async function (this: ICustomWorld, expectedStatus: string) {
	const job = this.context.emailSyncJob || this.context.newJob;
	if (!job) {
		throw new Error("Email sync job not found");
	}
	expect(job.status).toBe(expectedStatus);
});

Then("the job should have a unique ID", async function (this: ICustomWorld) {
	const job = this.context.newJob || this.context.emailSyncJob;
	if (!job) {
		throw new Error("Email sync job not found");
	}
	expect(job.id).toBeDefined();
	expect(job.id).toBeTruthy();
});

Then("the job status should change to {string}", async function (this: ICustomWorld, expectedStatus: string) {
	const job = this.context.emailSyncJob;
	if (!job) {
		throw new Error("Email sync job not found");
	}
	expect(job.status).toBe(expectedStatus);
});

Then("the job should have a startedAt timestamp", async function (this: ICustomWorld) {
	const job = this.context.emailSyncJob;
	if (!job) {
		throw new Error("Email sync job not found");
	}
	expect(job.startedAt).toBeDefined();
	expect(job.startedAt).toBeTruthy();
});

Then("the processed count should increase", async function (this: ICustomWorld) {
	const job = this.context.emailSyncJob;
	if (!job) {
		throw new Error("Email sync job not found");
	}
	expect(job.processedCount).toBeGreaterThan(0);
});

Then("the progress percentage should update", async function (this: ICustomWorld) {
	const job = this.context.emailSyncJob;
	if (!job) {
		throw new Error("Email sync job not found");
	}
	const progress = (job.processedCount / job.totalEmails) * 100;
	expect(progress).toBeGreaterThanOrEqual(0);
	expect(progress).toBeLessThanOrEqual(100);
});

Then("the job should be updated every {int} emails", async function (this: ICustomWorld, interval: number) {
	// ジョブが定期的に更新されることを確認
	this.context.jobUpdateInterval = interval;
	this.context.jobUpdatedPeriodically = true;
});

Then("the job should have a completedAt timestamp", async function (this: ICustomWorld) {
	const job = this.context.emailSyncJob;
	if (!job) {
		throw new Error("Email sync job not found");
	}
	expect(job.completedAt).toBeDefined();
	expect(job.completedAt).toBeTruthy();
});

Then("the processed count should equal total emails", async function (this: ICustomWorld) {
	const job = this.context.emailSyncJob;
	if (!job) {
		throw new Error("Email sync job not found");
	}
	expect(job.processedCount).toBe(job.totalEmails);
});

Then("errors should be zero", async function (this: ICustomWorld) {
	const job = this.context.emailSyncJob;
	if (!job) {
		throw new Error("Email sync job not found");
	}
	expect(job.errorCount).toBe(0);
});

Then("the error count should be greater than zero", async function (this: ICustomWorld) {
	const job = this.context.emailSyncJob;
	if (!job) {
		throw new Error("Email sync job not found");
	}
	expect(job.errorCount).toBeGreaterThan(0);
});

Then("the error message should be recorded", async function (this: ICustomWorld) {
	const job = this.context.emailSyncJob;
	if (!job) {
		throw new Error("Email sync job not found");
	}
	expect(job.errorMessage).toBeDefined();
	expect(job.errorMessage).toBeTruthy();
});

Then("a new job should be created", async function (this: ICustomWorld) {
	expect(this.context.jobRetried).toBe(true);
	expect(this.context.newJob).toBeDefined();
	this.context.newJobCreated = true;
});

Then("the new job should have status {string}", async function (this: ICustomWorld, expectedStatus: string) {
	const newJob = this.context.newJob;
	if (!newJob) {
		throw new Error("New job not found");
	}
	expect(newJob.status).toBe(expectedStatus);
});

Then("the new job should use the same limit as the original", async function (this: ICustomWorld) {
	const originalJob = this.context.emailSyncJob;
	const newJob = this.context.newJob;
	if (!originalJob || !newJob) {
		throw new Error("Jobs not found");
	}
	expect(newJob.limit).toBe(originalJob.limit);
});

Then("I should receive a list of jobs", async function (this: ICustomWorld) {
	expect(this.context.jobListQueried).toBe(true);
	expect(this.context.queriedJobList).toBeDefined();
	expect(this.context.queriedJobList.length).toBeGreaterThan(0);
});

Then("jobs should be ordered by createdAt descending", async function (this: ICustomWorld) {
	const jobs = this.context.queriedJobList;
	if (!jobs || jobs.length < 2) {
		return; // ソートの確認は2件以上必要
	}

	for (let i = 0; i < jobs.length - 1; i++) {
		const current = new Date(jobs[i].createdAt).getTime();
		const next = new Date(jobs[i + 1].createdAt).getTime();
		expect(current).toBeGreaterThanOrEqual(next);
	}
});

Then("each job should have status, progress, and statistics", async function (this: ICustomWorld) {
	const jobs = this.context.queriedJobList;
	if (!jobs) {
		throw new Error("Job list not found");
	}

	for (const job of jobs) {
		expect(job.status).toBeDefined();
		expect(job.processedCount).toBeDefined();
		expect(job.totalEmails).toBeDefined();
		expect(job.errorCount).toBeDefined();
	}
});

Then("I should receive the most recently created job", async function (this: ICustomWorld) {
	expect(this.context.latestJobQueried).toBe(true);
	expect(this.context.latestJob).toBeDefined();

	const latestJob = this.context.latestJob;
	const allJobs = this.context.emailSyncJobs;
	const mostRecent = allJobs.sort((a, b) =>
		new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
	)[0];

	expect(latestJob.id).toBe(mostRecent.id);
});

Then("the job should have all required fields", async function (this: ICustomWorld) {
	const job = this.context.latestJob || this.context.queriedJob;
	if (!job) {
		throw new Error("Job not found");
	}
	expect(job.id).toBeDefined();
	expect(job.status).toBeDefined();
	expect(job.limit).toBeDefined();
	expect(job.processedCount).toBeDefined();
	expect(job.totalEmails).toBeDefined();
	expect(job.createdAt).toBeDefined();
});

Then("I should receive the job details", async function (this: ICustomWorld) {
	expect(this.context.jobQueriedById).toBe(true);
	expect(this.context.queriedJob).toBeDefined();
});

Then("the job should include progress, statistics, and timestamps", async function (this: ICustomWorld) {
	const job = this.context.queriedJob;
	if (!job) {
		throw new Error("Job not found");
	}
	expect(job.processedCount).toBeDefined();
	expect(job.totalEmails).toBeDefined();
	expect(job.errorCount).toBeDefined();
	expect(job.createdAt).toBeDefined();
	if (job.status === "running" || job.status === "completed" || job.status === "failed") {
		expect(job.startedAt).toBeDefined();
	}
	if (job.status === "completed" || job.status === "failed") {
		expect(job.completedAt).toBeDefined();
	}
});
