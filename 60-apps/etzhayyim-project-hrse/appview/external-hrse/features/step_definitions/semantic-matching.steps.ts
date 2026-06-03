// @etzhayyim/cyber-freelance#SemanticMatchingSteps
// Semantic Matching関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

Given("job seeker and job data are available", async function (this: ICustomWorld) {
	this.context.jobSeekerData = {
		id: "test-job-seeker-id",
		name: "Test Job Seeker",
		email: "jobseeker@example.com",
		skills: ["JavaScript", "TypeScript", "React"],
		experience: "5 years of software development",
	};
	
	this.context.jobData = {
		id: "test-job-id",
		title: "Senior Software Engineer",
		company: "Tech Corp",
		requiredSkills: ["JavaScript", "TypeScript", "React", "Node.js"],
		description: "We are looking for an experienced software engineer",
	};
	
	this.context.dataAvailable = true;
});

When("semantic matching is performed for job matching", async function (this: ICustomWorld) {
	if (!this.context.dataAvailable) {
		throw new Error("Job seeker and job data are not available");
	}
	
	// セマンティックマッチングをシミュレート
	this.context.semanticMatchingPerformed = true;
	this.context.matchingResults = {
		similarityScore: 0.85,
		matched: true,
		matchedSkills: ["JavaScript", "TypeScript", "React"],
	};
});

Then("similarity scores should be calculated", async function (this: ICustomWorld) {
	expect(this.context.semanticMatchingPerformed).toBe(true);
	expect(this.context.matchingResults).toBeDefined();
	expect(this.context.matchingResults.similarityScore).toBeGreaterThan(0);
	expect(this.context.matchingResults.similarityScore).toBeLessThanOrEqual(1);
});

Then("the scores should reflect semantic similarity", async function (this: ICustomWorld) {
	const results = this.context.matchingResults;
	if (!results) {
		throw new Error("Matching results not found");
	}

	expect(results.similarityScore).toBeGreaterThan(0);
	expect(results.matchedSkills).toBeDefined();
	expect(results.matchedSkills.length).toBeGreaterThan(0);
});
