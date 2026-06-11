import { describe, it, expect, beforeEach } from 'vitest';
import {
	getSession, setSession, clearSession,
	isDid, formatDID, memberLabel,
	type Session,
} from '$lib/atproto-agent';

describe('AT Protocol session management', () => {
	beforeEach(() => {
		clearSession();
	});

	it('getSession returns null by default', () => {
		expect(getSession()).toBeNull();
	});

	it('setSession stores session and getSession retrieves it', () => {
		const session: Session = {
			did: 'did:plc:alice123',
			handle: 'alice.etzhayyim.com',
			accessJwt: 'access-jwt-token',
			refreshJwt: 'refresh-jwt-token',
		};
		setSession(session);
		const got = getSession();
		expect(got).not.toBeNull();
		expect(got!.did).toBe('did:plc:alice123');
		expect(got!.handle).toBe('alice.etzhayyim.com');
		expect(got!.accessJwt).toBe('access-jwt-token');
	});

	it('clearSession removes session', () => {
		setSession({ did: 'did:plc:x', handle: 'x', accessJwt: 'a', refreshJwt: 'r' });
		expect(getSession()).not.toBeNull();
		clearSession();
		expect(getSession()).toBeNull();
	});

	it('setSession overwrites previous session', () => {
		setSession({ did: 'did:plc:first', handle: 'first', accessJwt: 'a1', refreshJwt: 'r1' });
		setSession({ did: 'did:plc:second', handle: 'second', accessJwt: 'a2', refreshJwt: 'r2' });
		expect(getSession()!.did).toBe('did:plc:second');
	});
});

describe('isDid', () => {
	it('returns true for did:plc', () => {
		expect(isDid('did:plc:abc123')).toBe(true);
	});

	it('returns true for did:web', () => {
		expect(isDid('did:web:etzhayyim.com')).toBe(true);
	});

	it('returns false for did:key', () => {
		expect(isDid('did:key:z6Mk...')).toBe(false);
	});

	it('returns false for empty string', () => {
		expect(isDid('')).toBe(false);
	});

	it('returns false for non-DID string', () => {
		expect(isDid('alice@example.com')).toBe(false);
	});
});

describe('formatDID', () => {
	it('truncates long did:plc', () => {
		const did = 'did:plc:abcdefghijklmnopqrstuvwxyz';
		const formatted = formatDID(did);
		expect(formatted).toBe('did:plc:abcdefgh...');
		expect(formatted.length).toBeLessThan(did.length);
	});

	it('returns short did:plc as-is', () => {
		expect(formatDID('did:plc:short')).toBe('did:plc:short');
	});

	it('returns did:web as-is', () => {
		expect(formatDID('did:web:etzhayyim.com')).toBe('did:web:etzhayyim.com');
	});

	it('compacts did:etzhayyim CIDv1 path-form', () => {
		const did = 'did:etzhayyim:bafkreidibmnd32gvhguhjqxtauz3cca3fzehf6sxhlkdobuacow5jdat4a:bafkreigdmlrvrq47toz3jkh4etig6em3zg2gemg7a42a5ervlq5y3o27cq';
		const formatted = formatDID(did);
		expect(formatted).toMatch(/^did:etzhayyim:.+\/…\/.+$/);
		expect(formatted.length).toBeLessThan(did.length);
	});

	it('compacts long did:etzhayyim root', () => {
		const did = 'did:etzhayyim:bafkreidibmnd32gvhguhjqxtauz3cca3fzehf6sxhlkdobuacow5jdat4a';
		const formatted = formatDID(did);
		expect(formatted).toMatch(/^did:etzhayyim:.+…$/);
		expect(formatted.length).toBeLessThan(did.length);
	});
});

describe('memberLabel', () => {
	it('returns empty string for empty input', () => {
		expect(memberLabel('')).toBe('');
	});

	it('strips did:web: prefix', () => {
		expect(memberLabel('did:web:etzhayyim.com')).toBe('etzhayyim.com');
	});

	it('truncates long did:plc', () => {
		const did = 'did:plc:abcdefghijklmnopqrstuvwxyz';
		expect(memberLabel(did)).toBe('did:plc:abcdefgh...');
	});

	it('returns other DID types as-is', () => {
		expect(memberLabel('did:key:z6Mk')).toBe('did:key:z6Mk');
	});
});
