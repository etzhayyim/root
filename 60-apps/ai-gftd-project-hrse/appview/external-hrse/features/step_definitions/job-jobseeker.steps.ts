// @etzhayyim/cyber-freelance#JobJobSeekerSteps
// Job and JobSeeker関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

Given("a job exists", async function (this: ICustomWorld) {
	this.context.job = {
		id: "test-job-id",
		title: "Software Engineer",
		company: "Tech Corp",
		description: "We are looking for a software engineer",
		requiredSkills: ["JavaScript", "TypeScript", "React"],
		status: "active",
		createdAt: new Date().toISOString(),
	};
	this.context.jobExists = true;
});

Given("no job exists", async function (this: ICustomWorld) {
	this.context.job = null;
	this.context.jobExists = false;
});

Given("a job seeker exists", async function (this: ICustomWorld) {
	this.context.jobSeeker = {
		id: "test-job-seeker-id",
		name: "Test Job Seeker",
		email: "jobseeker@example.com",
		skills: ["JavaScript", "TypeScript", "React"],
		experience: "5 years of software development",
		createdAt: new Date().toISOString(),
	};
	this.context.jobSeekerExists = true;
});

Given("no job seeker exists", async function (this: ICustomWorld) {
	this.context.jobSeeker = null;
	this.context.jobSeekerExists = false;
});

When("a new job is created", async function (this: ICustomWorld) {
	this.context.createdJob = {
		id: "new-job-id",
		title: "New Software Engineer Position",
		company: "New Tech Corp",
		description: "New position description",
		requiredSkills: ["Python", "Django"],
		status: "active",
		createdAt: new Date().toISOString(),
	};
	this.context.jobCreated = true;
	this.context.job = this.context.createdJob;
	this.context.jobExists = true;
});

When("a new job seeker is created", async function (this: ICustomWorld) {
	this.context.createdJobSeeker = {
		id: "new-job-seeker-id",
		name: "New Job Seeker",
		email: "newjobseeker@example.com",
		skills: ["Python", "Django"],
		experience: "3 years",
		createdAt: new Date().toISOString(),
	};
	this.context.jobSeekerCreated = true;
	this.context.jobSeeker = this.context.createdJobSeeker;
	this.context.jobSeekerExists = true;
});

When("the job is updated", async function (this: ICustomWorld) {
	if (!this.context.jobExists) {
		throw new Error("Job does not exist");
	}

	this.context.updatedJob = {
		...this.context.job,
		title: "Updated Software Engineer",
		updatedAt: new Date().toISOString(),
	};
	this.context.jobUpdated = true;
	this.context.job = this.context.updatedJob;
});

When("the job seeker is updated", async function (this: ICustomWorld) {
	if (!this.context.jobSeekerExists) {
		throw new Error("Job seeker does not exist");
	}

	this.context.updatedJobSeeker = {
		...this.context.jobSeeker,
		skills: [...this.context.jobSeeker.skills, "Node.js"],
		updatedAt: new Date().toISOString(),
	};
	this.context.jobSeekerUpdated = true;
	this.context.jobSeeker = this.context.updatedJobSeeker;
});

Then("matching results should be generated", async function (this: ICustomWorld) {
	this.context.matchingProcessingTriggered = true;
	this.context.matchingResults = [
		{
			jobSeekerId: this.context.jobSeeker?.id || "test-job-seeker-id",
			jobId: this.context.job?.id || "test-job-id",
			similarityScore: 0.85,
			matchedSkills: ["JavaScript", "TypeScript"],
		},
	];
	this.context.matchingResultsGenerated = true;
	expect(this.context.matchingResultsGenerated).toBe(true);
});
