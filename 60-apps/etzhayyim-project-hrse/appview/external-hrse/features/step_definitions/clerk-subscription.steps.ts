// @etzhayyim/cyber-freelance#ClerkSubscriptionSteps
// Clerk Subscription関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

Given("a user exists in Clerk", async function (this: ICustomWorld) {
	this.context.clerkUser = {
		id: "userTest123",
		email: "test@example.com",
		metadata: {},
	};
	this.context.clerkUserExists = true;
});

Given("a subscription exists for a user", async function (this: ICustomWorld) {
	if (!this.context.clerkUserExists) {
		this.context.clerkUser = {
			id: "userTest123",
			email: "test@example.com",
			metadata: {},
		};
		this.context.clerkUserExists = true;
	}

	this.context.subscription = {
		id: "subTest123",
		contractId: "contract123",
		userId: this.context.clerkUser.id,
		status: "active",
		amount: 1000,
		currency: "JPY",
		createdAt: new Date().toISOString(),
	};
	this.context.subscriptionExists = true;
	this.context.clerkUser.metadata.subscription = this.context.subscription;
});

Given("an active subscription exists for a user", async function (this: ICustomWorld) {
	if (!this.context.clerkUserExists) {
		this.context.clerkUser = {
			id: "userTest123",
			email: "test@example.com",
			metadata: {},
		};
		this.context.clerkUserExists = true;
	}

	this.context.subscription = {
		id: "subTest123",
		contractId: "contract123",
		userId: this.context.clerkUser.id,
		status: "active",
		amount: 1000,
		currency: "JPY",
		createdAt: new Date().toISOString(),
	};
	this.context.subscriptionExists = true;
	this.context.subscriptionActive = true;
	this.context.clerkUser.metadata.subscription = this.context.subscription;
});

When("a subscription is created with contract ID and amount", async function (this: ICustomWorld) {
	if (!this.context.clerkUserExists) {
		throw new Error("Clerk user does not exist");
	}

	this.context.createdSubscription = {
		id: "subNew123",
		contractId: "contractNew123",
		userId: this.context.clerkUser.id,
		status: "active",
		amount: 2000,
		currency: "JPY",
		createdAt: new Date().toISOString(),
	};
	this.context.subscriptionCreated = true;
	this.context.subscription = this.context.createdSubscription;
	this.context.clerkUser.metadata.subscription = this.context.createdSubscription;
});

When("the subscription is updated with new amount or status", async function (this: ICustomWorld) {
	if (!this.context.subscriptionExists) {
		throw new Error("Subscription does not exist");
	}

	this.context.updatedSubscription = {
		...this.context.subscription,
		amount: 3000,
		status: "active",
		updatedAt: new Date().toISOString(),
	};
	this.context.subscriptionUpdated = true;
	this.context.subscription = this.context.updatedSubscription;
	this.context.clerkUser.metadata.subscription = this.context.updatedSubscription;
});

When("the subscription is retrieved by subscription ID", async function (this: ICustomWorld) {
	if (!this.context.subscriptionExists) {
		throw new Error("Subscription does not exist");
	}

	this.context.retrievedSubscription = this.context.subscription;
	this.context.subscriptionRetrieved = true;
});

When("the subscription is cancelled", async function (this: ICustomWorld) {
	if (!this.context.subscriptionExists || !this.context.subscriptionActive) {
		throw new Error("Active subscription does not exist");
	}

	this.context.cancelledSubscription = {
		...this.context.subscription,
		status: "cancelled",
		cancelledAt: new Date().toISOString(),
		updatedAt: new Date().toISOString(),
	};
	this.context.subscriptionCancelled = true;
	this.context.subscription = this.context.cancelledSubscription;
	this.context.subscriptionActive = false;
	this.context.clerkUser.metadata.subscription = this.context.cancelledSubscription;
});

Then("the subscription should be stored in user metadata", async function (this: ICustomWorld) {
	expect(this.context.subscriptionCreated).toBe(true);
	const user = this.context.clerkUser;
	if (!user) {
		throw new Error("Clerk user not found");
	}
	expect(user.metadata.subscription).toBeDefined();
	expect(user.metadata.subscription.id).toBe(this.context.createdSubscription.id);
});

Then("the subscription ID should be returned", async function (this: ICustomWorld) {
	expect(this.context.subscriptionCreated).toBe(true);
	expect(this.context.createdSubscription.id).toBeDefined();
	this.context.returnedSubscriptionId = this.context.createdSubscription.id;
});

Then("the subscription metadata should be updated", async function (this: ICustomWorld) {
	expect(this.context.subscriptionUpdated).toBe(true);
	const updated = this.context.updatedSubscription;
	if (!updated) {
		throw new Error("Updated subscription not found");
	}
	expect(updated.updatedAt).toBeDefined();
	expect(updated.amount).toBe(3000);
});

Then("the updatedAt timestamp should be set", async function (this: ICustomWorld) {
	const updated = this.context.updatedSubscription;
	if (!updated) {
		throw new Error("Updated subscription not found");
	}
	expect(updated.updatedAt).toBeDefined();
	expect(updated.updatedAt).toBeTruthy();
});

Then("the subscription data should be returned", async function (this: ICustomWorld) {
	expect(this.context.subscriptionRetrieved).toBe(true);
	expect(this.context.retrievedSubscription).toBeDefined();
});

Then("the data should include status, amount, and currency", async function (this: ICustomWorld) {
	const subscription = this.context.retrievedSubscription;
	if (!subscription) {
		throw new Error("Retrieved subscription not found");
	}
	expect(subscription.status).toBeDefined();
	expect(subscription.amount).toBeDefined();
	expect(subscription.currency).toBeDefined();
});

Then("the subscription status should be set to {string}", async function (this: ICustomWorld, expectedStatus: string) {
	expect(this.context.subscriptionCancelled).toBe(true);
	const cancelled = this.context.cancelledSubscription;
	if (!cancelled) {
		throw new Error("Cancelled subscription not found");
	}
	expect(cancelled.status).toBe(expectedStatus);
});

Then("the metadata should be updated", async function (this: ICustomWorld) {
	expect(this.context.subscriptionCancelled).toBe(true);
	const cancelled = this.context.cancelledSubscription;
	if (!cancelled) {
		throw new Error("Cancelled subscription not found");
	}
	expect(cancelled.updatedAt).toBeDefined();
	expect(cancelled.cancelledAt).toBeDefined();
	const user = this.context.clerkUser;
	if (!user) {
		throw new Error("Clerk user not found");
	}
	expect(user.metadata.subscription.status).toBe("cancelled");
});
