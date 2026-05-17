import { describe, it, expect } from 'vitest';
import { buildTrustSummary, trustVariantFromScore, normalizeExternalAccount } from '../auth/trust.js';
import type { ClerkUserInfo, Organization } from '../auth/types.js';

function makeUser(overrides: Partial<ClerkUserInfo> = {}): ClerkUserInfo {
	return {
		id: 'userTest',
		firstName: 'Test',
		lastName: 'User',
		fullName: 'Test User',
		username: null,
		emailAddress: 'test@example.com',
		phoneNumber: null,
		hasVerifiedEmail: false,
		hasVerifiedPhone: false,
		imageUrl: null,
		publicMetadata: {},
		...overrides,
	};
}

function makeOrg(overrides: Partial<Organization> = {}): Organization {
	return {
		id: 'orgTest',
		name: 'Test Org',
		slug: 'test',
		category: 'general',
		role: 'member',
		metadata: {},
		...overrides,
	};
}

describe('trustVariantFromScore', () => {
	it('returns success for score >= 75', () => {
		expect(trustVariantFromScore(75)).toBe('success');
		expect(trustVariantFromScore(100)).toBe('success');
	});

	it('returns accent for 50-74', () => {
		expect(trustVariantFromScore(50)).toBe('accent');
		expect(trustVariantFromScore(74)).toBe('accent');
	});

	it('returns warning for 25-49', () => {
		expect(trustVariantFromScore(25)).toBe('warning');
		expect(trustVariantFromScore(49)).toBe('warning');
	});

	it('returns default for < 25', () => {
		expect(trustVariantFromScore(0)).toBe('default');
		expect(trustVariantFromScore(24)).toBe('default');
	});
});

describe('buildTrustSummary — guest (null user)', () => {
	it('returns score 0 and label guest', () => {
		const summary = buildTrustSummary(null, null);
		expect(summary.score).toBe(0);
		expect(summary.label).toBe('guest');
		expect(summary.methods).toEqual([]);
		expect(summary.accessReady).toBe(true);
	});

	it('reports access reasons when org requires trust score', () => {
		const org = makeOrg({ requiredTrustScore: 50 });
		const summary = buildTrustSummary(null, org);
		expect(summary.accessReady).toBe(false);
		expect(summary.accessReasons).toContain('Trust score 50+ required');
	});

	it('reports access reasons when org requires minimum age', () => {
		const org = makeOrg({ minimumAge: 18 });
		const summary = buildTrustSummary(null, org);
		expect(summary.accessReady).toBe(false);
		expect(summary.accessReasons).toContain('Age 18+ required');
	});

	it('has 3 initial steps for guest', () => {
		const summary = buildTrustSummary(null, null);
		expect(summary.steps).toHaveLength(3);
		expect(summary.steps.every((s) => !s.completed)).toBe(true);
	});
});

describe('buildTrustSummary — authenticated user', () => {
	it('minimal user gets starter label (score ~5)', () => {
		const user = makeUser();
		const summary = buildTrustSummary(user, null);
		expect(summary.score).toBe(5);
		expect(summary.label).toBe('starter');
		expect(summary.methods).toContain('clerk');
	});

	it('user with username gets +15', () => {
		const user = makeUser({ username: 'alice' });
		const summary = buildTrustSummary(user, null);
		expect(summary.score).toBe(20);
		expect(summary.methods).toContain('username');
	});

	it('user with verified email gets +10', () => {
		const user = makeUser({ hasVerifiedEmail: true });
		const summary = buildTrustSummary(user, null);
		expect(summary.score).toBe(15);
		expect(summary.methods).toContain('email');
	});

	it('user with verified phone gets +20', () => {
		const user = makeUser({ hasVerifiedPhone: true });
		const summary = buildTrustSummary(user, null);
		expect(summary.score).toBe(25);
		expect(summary.label).toBe('verified');
		expect(summary.methods).toContain('phone');
	});

	it('user with web3 wallet gets +20', () => {
		const user = makeUser({ web3Wallets: [{ id: 'w1', web3Wallet: '0xabc' }] });
		const summary = buildTrustSummary(user, null);
		expect(summary.score).toBe(25);
		expect(summary.methods).toContain('metamask');
	});

	it('user with social account gets +10', () => {
		const user = makeUser({
			externalAccounts: [{ id: 'ea1', provider: 'google', label: 'Google', verified: true }],
		});
		const summary = buildTrustSummary(user, null);
		expect(summary.score).toBe(15);
		expect(summary.methods).toContain('social');
	});

	it('fully verified user reaches high-trust', () => {
		const user = makeUser({
			username: 'alice',
			hasVerifiedEmail: true,
			hasVerifiedPhone: true,
			web3Wallets: [{ id: 'w1', web3Wallet: '0xabc' }],
			externalAccounts: [{ id: 'ea1', provider: 'google', label: 'Google', verified: true }],
			publicMetadata: { 'ageVerified': true },
		});
		const summary = buildTrustSummary(user, null);
		expect(summary.score).toBe(100);
		expect(summary.label).toBe('high-trust');
	});

	it('explicit trustScore in metadata overrides calculation', () => {
		const user = makeUser({ publicMetadata: { 'trustScore': 42 } });
		const summary = buildTrustSummary(user, null);
		expect(summary.score).toBe(42);
	});

	it('score is clamped to 0-100', () => {
		const user = makeUser({ publicMetadata: { 'trustScore': 150 } });
		const summary = buildTrustSummary(user, null);
		expect(summary.score).toBe(100);
	});

	it('reports age access failure when under minimum', () => {
		const user = makeUser({ publicMetadata: { 'ageYears': 15 } });
		const org = makeOrg({ minimumAge: 18 });
		const summary = buildTrustSummary(user, org);
		expect(summary.accessReady).toBe(false);
		expect(summary.accessReasons.some((r) => r.includes('age 18'))).toBe(true);
	});

	it('org metadata minimumTrustScore works', () => {
		const user = makeUser();
		const org = makeOrg({ metadata: { 'minimumTrustScore': 50 } });
		const summary = buildTrustSummary(user, org);
		expect(summary.requiredTrustScore).toBe(50);
		expect(summary.accessReady).toBe(false);
	});

	it('steps track completion correctly', () => {
		const user = makeUser({ username: 'alice', hasVerifiedPhone: true });
		const summary = buildTrustSummary(user, null);
		const usernameStep = summary.steps.find((s) => s.id === 'username');
		const phoneStep = summary.steps.find((s) => s.id === 'phone');
		const metamaskStep = summary.steps.find((s) => s.id === 'metamask');
		expect(usernameStep!.completed).toBe(true);
		expect(phoneStep!.completed).toBe(true);
		expect(metamaskStep!.completed).toBe(false);
	});

	it('nextScoreTarget points to next threshold', () => {
		const user = makeUser(); // score = 5
		const summary = buildTrustSummary(user, null);
		expect(summary.nextScoreTarget).toBe(25);
	});
});

describe('normalizeExternalAccount', () => {
	it('normalizes a verified Google account', () => {
		const account = normalizeExternalAccount({
			id: 'ea1',
			provider: 'googleOauth',
			'verificationStatus': 'verified',
		});
		expect(account).not.toBeNull();
		expect(account!.provider).toBe('googleOauth');
		expect(account!.label).toBe('Google Oauth');
		expect(account!.verified).toBe(true);
	});

	it('returns null for account without id', () => {
		expect(normalizeExternalAccount({ provider: 'google' })).toBeNull();
	});

	it('detects verified from nested verification object', () => {
		const account = normalizeExternalAccount({
			id: 'ea2',
			verification: { status: 'verified' },
		});
		expect(account!.verified).toBe(true);
	});

	it('defaults provider to social', () => {
		const account = normalizeExternalAccount({ id: 'ea3' });
		expect(account!.provider).toBe('social');
	});
});
