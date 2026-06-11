import { describe, it, expect } from 'vitest';
import { get } from 'svelte/store';
import {
	clerkLoaded, isSignedIn, clerkUser, sessionToken,
	onboardingCompleted, currentOrg, userOrganizations, orgLoading,
	displayName, userPlan, trustSummary,
} from '../auth/stores.js';
import type { ClerkUserInfo, Organization } from '../auth/types.js';

describe('auth stores — defaults', () => {
	it('clerkLoaded defaults to false', () => {
		expect(get(clerkLoaded)).toBe(false);
	});

	it('isSignedIn defaults to false', () => {
		expect(get(isSignedIn)).toBe(false);
	});

	it('clerkUser defaults to null', () => {
		expect(get(clerkUser)).toBeNull();
	});

	it('sessionToken defaults to null', () => {
		expect(get(sessionToken)).toBeNull();
	});

	it('onboardingCompleted defaults to false', () => {
		expect(get(onboardingCompleted)).toBe(false);
	});

	it('currentOrg defaults to null', () => {
		expect(get(currentOrg)).toBeNull();
	});

	it('userOrganizations defaults to empty array', () => {
		expect(get(userOrganizations)).toEqual([]);
	});

	it('orgLoading defaults to false', () => {
		expect(get(orgLoading)).toBe(false);
	});
});

describe('displayName — derived store', () => {
	it('returns Guest when user is null', () => {
		clerkUser.set(null);
		expect(get(displayName)).toBe('Guest');
	});

	it('returns fullName when available', () => {
		clerkUser.set({
			id: 'u1', firstName: 'Test', lastName: 'User', fullName: 'Test User',
			username: null, emailAddress: 'test@example.com', phoneNumber: null,
			hasVerifiedEmail: false, hasVerifiedPhone: false, imageUrl: null,
			publicMetadata: {},
		});
		expect(get(displayName)).toBe('Test User');
		clerkUser.set(null);
	});

	it('falls back to firstName', () => {
		clerkUser.set({
			id: 'u2', firstName: 'Alice', lastName: null, fullName: null,
			username: null, emailAddress: null, phoneNumber: null,
			hasVerifiedEmail: false, hasVerifiedPhone: false, imageUrl: null,
			publicMetadata: {},
		});
		expect(get(displayName)).toBe('Alice');
		clerkUser.set(null);
	});

	it('falls back to email local part', () => {
		clerkUser.set({
			id: 'u3', firstName: null, lastName: null, fullName: null,
			username: null, emailAddress: 'bob@etzhayyim.com', phoneNumber: null,
			hasVerifiedEmail: false, hasVerifiedPhone: false, imageUrl: null,
			publicMetadata: {},
		});
		expect(get(displayName)).toBe('bob');
		clerkUser.set(null);
	});

	it('falls back to User when nothing available', () => {
		clerkUser.set({
			id: 'u4', firstName: null, lastName: null, fullName: null,
			username: null, emailAddress: null, phoneNumber: null,
			hasVerifiedEmail: false, hasVerifiedPhone: false, imageUrl: null,
			publicMetadata: {},
		});
		expect(get(displayName)).toBe('User');
		clerkUser.set(null);
	});
});

describe('userPlan — derived store', () => {
	it('returns Free Plan by default', () => {
		clerkUser.set(null);
		expect(get(userPlan)).toBe('Free Plan');
	});

	it('returns plan from publicMetadata', () => {
		clerkUser.set({
			id: 'u5', firstName: null, lastName: null, fullName: null,
			username: null, emailAddress: null, phoneNumber: null,
			hasVerifiedEmail: false, hasVerifiedPhone: false, imageUrl: null,
			publicMetadata: { plan: 'Pro' },
		});
		expect(get(userPlan)).toBe('Pro');
		clerkUser.set(null);
	});
});

describe('trustSummary — derived store', () => {
	it('returns guest trust for null user', () => {
		clerkUser.set(null);
		currentOrg.set(null);
		const summary = get(trustSummary);
		expect(summary.score).toBe(0);
		expect(summary.label).toBe('guest');
	});

	it('updates when user changes', () => {
		clerkUser.set({
			id: 'u6', firstName: 'Alice', lastName: null, fullName: 'Alice',
			username: 'alice', emailAddress: 'a@etzhayyim.com', phoneNumber: null,
			hasVerifiedEmail: true, hasVerifiedPhone: false, imageUrl: null,
			publicMetadata: {},
		});
		currentOrg.set(null);
		const summary = get(trustSummary);
		expect(summary.score).toBeGreaterThan(0);
		expect(summary.methods).toContain('username');
		expect(summary.methods).toContain('email');
		clerkUser.set(null);
	});
});
