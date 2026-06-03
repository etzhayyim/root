import { describe, it, expect } from 'vitest';
import { parseZkV1Envelope } from '../auth/zk.js';

describe('parseZkV1Envelope', () => {
	it('parses valid zk-v1 envelope', () => {
		const input = {
			version: 'zk-v1',
			owner: { clerkUserId: 'user1', clerkOrgId: 'org1' },
			deviceId: 'dev1',
			alg: { kdf: 'pbkdf2-sha256', aead: 'aes-256-gcm', wrap: 'x25519-hkdf' },
			wrappedKeys: { akByMk: 'a', dkByAk: 'b', dekByAk: 'c' },
			aad: { objectId: 'obj1', createdAt: '2026-03-19T00:00:00Z' },
		};
		const result = parseZkV1Envelope(input);
		expect(result.version).toBe('zk-v1');
		expect(result.owner.clerkUserId).toBe('user1');
		expect(result.deviceId).toBe('dev1');
	});

	it('throws for null input', () => {
		expect(() => parseZkV1Envelope(null)).toThrow('invalid envelope: expected object');
	});

	it('throws for non-object input', () => {
		expect(() => parseZkV1Envelope('string')).toThrow('invalid envelope: expected object');
	});

	it('throws for wrong version', () => {
		expect(() => parseZkV1Envelope({ version: 'zk-v2' })).toThrow('unsupported version');
	});
});
