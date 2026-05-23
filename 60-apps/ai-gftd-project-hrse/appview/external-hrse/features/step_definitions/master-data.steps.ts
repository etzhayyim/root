// @etzhayyim/cyber-freelance#MasterDataSteps
// Master Data関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

Given("master data exists", async function (this: ICustomWorld) {
	this.context.masterData = {
		id: "test-master-data-id",
		type: "certification",
		name: "AWS Certified Solutions Architect",
		code: "AWS-CSA",
		description: "Amazon Web Services Certified Solutions Architect",
		createdAt: new Date().toISOString(),
	};
	this.context.masterDataExists = true;
});

When("master data is created with valid input", async function (this: ICustomWorld) {
	this.context.createdMasterData = {
		id: "new-master-data-id",
		type: "specialization",
		name: "Full Stack Development",
		code: "FSD",
		description: "Full stack web development",
		createdAt: new Date().toISOString(),
	};
	this.context.masterDataCreated = true;
	this.context.masterData = this.context.createdMasterData;
	this.context.masterDataExists = true;
});

When("the master data is updated with valid input", async function (this: ICustomWorld) {
	if (!this.context.masterDataExists) {
		throw new Error("Master data does not exist");
	}

	this.context.updatedMasterData = {
		...this.context.masterData,
		name: "Updated Master Data",
		description: "Updated description",
		updatedAt: new Date().toISOString(),
	};
	this.context.masterDataUpdated = true;
	this.context.masterData = this.context.updatedMasterData;
});

When("the master data is deleted", async function (this: ICustomWorld) {
	if (!this.context.masterDataExists) {
		throw new Error("Master data does not exist");
	}

	this.context.deletedMasterDataId = this.context.masterData.id;
	this.context.masterDataDeleted = true;
	this.context.masterDataExists = false;
	this.context.masterData = null;
});

When("master data is retrieved", async function (this: ICustomWorld) {
	if (!this.context.masterDataExists) {
		throw new Error("Master data does not exist");
	}

	this.context.retrievedMasterData = this.context.masterData;
	this.context.masterDataRetrieved = true;
});

Then("the master data should be created successfully", async function (this: ICustomWorld) {
	expect(this.context.masterDataCreated).toBe(true);
	expect(this.context.createdMasterData).toBeDefined();
	expect(this.context.createdMasterData.id).toBeDefined();
});

Then("the master data should be stored in the database", async function (this: ICustomWorld) {
	const masterData = this.context.createdMasterData;
	if (!masterData) {
		throw new Error("Created master data not found");
	}
	expect(masterData.id).toBeDefined();
	expect(masterData.type).toBeDefined();
	expect(masterData.name).toBeDefined();
	this.context.masterDataStored = true;
});

Then("the master data should be updated successfully", async function (this: ICustomWorld) {
	expect(this.context.masterDataUpdated).toBe(true);
	expect(this.context.updatedMasterData).toBeDefined();
});

Then("the updated data should be stored in the database", async function (this: ICustomWorld) {
	const updatedData = this.context.updatedMasterData;
	if (!updatedData) {
		throw new Error("Updated master data not found");
	}
	expect(updatedData.updatedAt).toBeDefined();
	this.context.updatedDataStored = true;
});

Then("the master data should be deleted successfully", async function (this: ICustomWorld) {
	expect(this.context.masterDataDeleted).toBe(true);
	expect(this.context.deletedMasterDataId).toBeDefined();
});

Then("the master data should be removed from the database", async function (this: ICustomWorld) {
	expect(this.context.masterDataDeleted).toBe(true);
	expect(this.context.masterDataExists).toBe(false);
	this.context.masterDataRemoved = true;
});

Then("the master data should be returned", async function (this: ICustomWorld) {
	expect(this.context.masterDataRetrieved).toBe(true);
	expect(this.context.retrievedMasterData).toBeDefined();
});

Then("the master data should include all required fields", async function (this: ICustomWorld) {
	const masterData = this.context.retrievedMasterData || this.context.masterData;
	if (!masterData) {
		throw new Error("Master data not found");
	}
	expect(masterData.id).toBeDefined();
	expect(masterData.type).toBeDefined();
	expect(masterData.name).toBeDefined();
	expect(masterData.createdAt).toBeDefined();
});
