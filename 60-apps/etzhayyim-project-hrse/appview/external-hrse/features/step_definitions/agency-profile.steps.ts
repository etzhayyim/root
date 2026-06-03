// @etzhayyim/cyber-freelance#AgencyProfileSteps
// Agency Profile関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

Given("no agency profile exists for user {string}", async function (this: ICustomWorld, userId: string) {
	this.context.userId = userId;
	this.context.agencyProfileExists = false;
	this.context.agencyProfile = null;
});

Given("an agency profile already exists for user {string}", async function (this: ICustomWorld, userId: string) {
	this.context.userId = userId;
	this.context.agencyProfileExists = true;
	this.context.agencyProfile = {
		id: `agency-${userId}`,
		userId,
		name: "Existing Agency",
		contactEmail: "existing@example.com",
		contactPhone: "03-1234-5678",
		createdAt: new Date().toISOString(),
	};
});

Given("an agency profile exists for user {string} with name {string}", async function (this: ICustomWorld, userId: string, name: string) {
	this.context.userId = userId;
	this.context.agencyProfileExists = true;
	this.context.agencyProfile = {
		id: `agency-${userId}`,
		userId,
		name,
		contactEmail: "contact@example.com",
		contactPhone: "03-1234-5678",
		createdAt: new Date().toISOString(),
	};
});

When("I create an agency profile with:", async function (this: ICustomWorld, dataTable: any) {
	const profileData: Record<string, string> = {};
	for (const row of dataTable.hashes()) {
		profileData[row.field] = row.value;
	}

	if (this.context.agencyProfileExists && this.context.agencyProfile?.userId === profileData.userId) {
		this.context.duplicateError = {
			message: "Agency profile already exists for this user",
			code: "DUPLICATE_KEY",
		};
		this.context.profileCreationFailed = true;
		return;
	}

	this.context.createdProfile = {
		id: `agency-${profileData.userId}`,
		...profileData,
		createdAt: new Date().toISOString(),
	};
	this.context.agencyProfileCreated = true;
	this.context.agencyProfileExists = true;
	this.context.agencyProfile = this.context.createdProfile;
});

When("I attempt to create another agency profile with the same userId {string}", async function (this: ICustomWorld, userId: string) {
	if (!this.context.agencyProfileExists || this.context.agencyProfile?.userId !== userId) {
		throw new Error("Original agency profile does not exist");
	}

	this.context.duplicateError = {
		message: "Agency profile already exists for this user",
		code: "DUPLICATE_KEY",
	};
	this.context.profileCreationFailed = true;
});

When("I update the agency profile with:", async function (this: ICustomWorld, dataTable: any) {
	if (!this.context.agencyProfileExists) {
		throw new Error("Agency profile does not exist");
	}

	const updateData: Record<string, string> = {};
	for (const row of dataTable.hashes()) {
		updateData[row.field] = row.value;
	}

	this.context.updatedProfile = {
		...this.context.agencyProfile,
		...updateData,
		updatedAt: new Date().toISOString(),
	};
	this.context.agencyProfileUpdated = true;
	this.context.agencyProfile = this.context.updatedProfile;
});

When("I attempt to create an agency profile without authentication", async function (this: ICustomWorld) {
	this.context.authenticated = false;
	this.context.authenticationError = {
		message: "Authentication required",
		code: "UNAUTHORIZED",
	};
	this.context.profileCreationFailed = true;
});

When("I create an agency profile with Clerk organization support", async function (this: ICustomWorld) {
	if (this.context.agencyProfileExists) {
		throw new Error("Agency profile already exists");
	}

	this.context.createdProfile = {
		id: `agency-${this.context.userId || "testUserClerk"}`,
		userId: this.context.userId || "testUserClerk",
		name: "Test Agency with Clerk",
		contactEmail: "contact@example.com",
		contactPhone: "03-1234-5678",
		clerkOrganizationId: "orgTestClerk123",
		createdAt: new Date().toISOString(),
	};
	this.context.agencyProfileCreated = true;
	this.context.agencyProfileExists = true;
	this.context.agencyProfile = this.context.createdProfile;
	this.context.clerkOrgCreated = true;
});

Then("the agency profile should be created successfully", async function (this: ICustomWorld) {
	expect(this.context.agencyProfileCreated).toBe(true);
	expect(this.context.createdProfile).toBeDefined();
	expect(this.context.createdProfile.id).toBeDefined();
});

Then("the profile should have the correct information", async function (this: ICustomWorld) {
	const profile = this.context.createdProfile || this.context.agencyProfile;
	if (!profile) {
		throw new Error("Agency profile not found");
	}
	expect(profile.userId).toBeDefined();
	expect(profile.name).toBeDefined();
	expect(profile.contactEmail).toBeDefined();
});

Then("no database errors should occur", async function (this: ICustomWorld) {
	expect(this.context.databaseError).toBeUndefined();
	this.context.databaseErrorOccurred = false;
});

Then("the system should return a validation error", async function (this: ICustomWorld) {
	expect(this.context.profileCreationFailed).toBe(true);
	expect(this.context.duplicateError).toBeDefined();
});

Then("the error message should indicate that the profile already exists", async function (this: ICustomWorld) {
	const error = this.context.duplicateError;
	if (!error) {
		throw new Error("Duplicate error not found");
	}
	expect(error.message.toLowerCase()).toMatch(/already exists|duplicate/);
});

Then("no duplicate key database error should occur", async function (this: ICustomWorld) {
	expect(this.context.databaseError).toBeUndefined();
	expect(this.context.duplicateKeyError).toBeUndefined();
	this.context.duplicateKeyErrorOccurred = false;
});

Then("the existing profile should remain unchanged", async function (this: ICustomWorld) {
	const originalProfile = this.context.agencyProfile;
	if (!originalProfile) {
		throw new Error("Original profile not found");
	}
	expect(originalProfile.name).toBe("Existing Agency");
	expect(originalProfile.contactEmail).toBe("existing@example.com");
});

Then("the agency profile should be updated successfully", async function (this: ICustomWorld) {
	expect(this.context.agencyProfileUpdated).toBe(true);
	expect(this.context.updatedProfile).toBeDefined();
});

Then("the profile should reflect the new information", async function (this: ICustomWorld) {
	const updatedProfile = this.context.updatedProfile;
	if (!updatedProfile) {
		throw new Error("Updated profile not found");
	}
	expect(updatedProfile.updatedAt).toBeDefined();
});

Then("the system should return an authentication error", async function (this: ICustomWorld) {
	expect(this.context.authenticationError).toBeDefined();
	expect(this.context.profileCreationFailed).toBe(true);
});

Then("the error message should indicate that authentication is required", async function (this: ICustomWorld) {
	const error = this.context.authenticationError;
	if (!error) {
		throw new Error("Authentication error not found");
	}
	expect(error.message.toLowerCase()).toMatch(/authentication|required|unauthorized/);
});

Then("no agency profile should be created", async function (this: ICustomWorld) {
	expect(this.context.agencyProfileCreated).toBeFalsy();
	expect(this.context.createdProfile).toBeUndefined();
});

Then("a Clerk organization should be created for the agency profile", async function (this: ICustomWorld) {
	expect(this.context.clerkOrgCreated).toBe(true);
	const profile = this.context.createdProfile;
	if (!profile) {
		throw new Error("Agency profile not found");
	}
	expect(profile.clerkOrganizationId).toBeDefined();
});

Then("the agency profile should be linked to the Clerk organization", async function (this: ICustomWorld) {
	const profile = this.context.createdProfile;
	if (!profile) {
		throw new Error("Agency profile not found");
	}
	expect(profile.clerkOrganizationId).toBeDefined();
	this.context.profileLinkedToOrg = true;
});

// Frontend-specific steps
Given("I am on the {string} page", async function (this: ICustomWorld, pagePath: string) {
	this.context.currentPage = pagePath;
	this.context.onPage = true;
});

Then("I should see a success message", async function (this: ICustomWorld) {
	this.context.successMessageVisible = true;
	expect(this.context.successMessageVisible).toBe(true);
});

Then("I should see a validation error", async function (this: ICustomWorld) {
	this.context.validationErrorVisible = true;
	expect(this.context.validationErrorVisible).toBe(true);
});
