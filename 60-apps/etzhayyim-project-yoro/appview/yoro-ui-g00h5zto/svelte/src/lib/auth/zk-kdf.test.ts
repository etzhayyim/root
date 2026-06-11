/**
 * zk KDF migration (ADR-2606111300 residual #2): new writes use Argon2id
 * via the @etzhayyim/sdk/kdf seam; pre-existing PBKDF2 envelopes stay
 * unlockable through the aad metadata dispatch (crypto-agility read-compat).
 */
import { describe, it, expect } from 'vitest';

import { deriveWrappingKey } from './zk.js';
import {
	attachKdfMetadata,
	getKdfMetadata,
	buildEmergencyKitText,
} from './key-bundle-flows.js';
import type { ZkEnvelopeV1 } from './types.js';

const hex = (b: Uint8Array) =>
	Array.from(b)
		.map((x) => x.toString(16).padStart(2, '0'))
		.join('');

const baseParams = {
	accountPassword: 'pw-123456',
	secretKey: 'ABCDE-FGHJK-LMNPQ-RSTUV-WXYZ2-34567',
	saltBase64Url: 'AAAAAAAAAAAAAAAAAAAAAA',
};

function makeEnvelope(): ZkEnvelopeV1 {
	return {
		version: 'zk-v1',
		owner: { clerkUserId: 'u1', clerkOrgId: 'o1' },
		deviceId: 'd1',
		alg: { kdf: 'argon2id', aead: 'xchacha20poly1305', wrap: 'x25519-hkdf' },
		wrappedKeys: { akByMk: 'a', dkByAk: 'b', dekByAk: 'c' },
		aad: { objectId: 'obj_1', createdAt: '2026-06-11T00:00:00.000Z' },
	};
}

describe('deriveWrappingKey — argon2id default', () => {
	it('defaults to argon2id and is deterministic for the same salt', async () => {
		const a = await deriveWrappingKey(baseParams);
		const b = await deriveWrappingKey(baseParams);
		expect(a.kdf).toBe('argon2id');
		expect(a.argon2?.mKiB).toBeGreaterThanOrEqual(19_456);
		expect(a.key.length).toBe(32);
		expect(hex(a.key)).toBe(hex(b.key));
	});

	it('explicit pbkdf2-sha256 keeps the legacy derivation (read-compat)', async () => {
		const r = await deriveWrappingKey({ ...baseParams, kdf: 'pbkdf2-sha256' });
		expect(r.kdf).toBe('pbkdf2-sha256');
		expect(r.iterations).toBe(310_000);
		expect(r.key.length).toBe(32);

		const argon = await deriveWrappingKey(baseParams);
		expect(hex(r.key)).not.toBe(hex(argon.key));
	});
});

describe('KDF envelope metadata roundtrip', () => {
	it('argon2id attach → get preserves cost parameters and sets alg.kdf', async () => {
		const derived = await deriveWrappingKey(baseParams);
		const env = attachKdfMetadata(makeEnvelope(), {
			kdf: derived.kdf,
			saltBase64Url: derived.saltBase64Url,
			argon2: derived.argon2,
		});
		expect(env.alg.kdf).toBe('argon2id');
		const meta = getKdfMetadata(env);
		expect(meta.kdf).toBe('argon2id');
		expect(meta.argon2).toEqual(derived.argon2);

		const rederived = await deriveWrappingKey({
			...baseParams,
			saltBase64Url: meta.saltBase64Url,
			kdf: meta.kdf,
			argon2: meta.argon2,
		});
		expect(hex(rederived.key)).toBe(hex(derived.key));
	});

	it('a legacy envelope without kdfName dispatches to PBKDF2', () => {
		const legacy = makeEnvelope();
		legacy.alg.kdf = 'pbkdf2-sha256';
		legacy.aad.kdfSaltB64url = baseParams.saltBase64Url;
		legacy.aad.kdfIterations = 310_000;
		const meta = getKdfMetadata(legacy);
		expect(meta.kdf).toBe('pbkdf2-sha256');
		expect(meta.iterations).toBe(310_000);
	});

	it('rejects an unknown kdfName instead of silently downgrading', () => {
		const env = makeEnvelope();
		env.aad.kdfSaltB64url = baseParams.saltBase64Url;
		env.aad.kdfName = 'md5-crypt';
		expect(() => getKdfMetadata(env)).toThrow(/unsupported kdfName/);
	});
});

describe('emergency kit text', () => {
	it('records Argon2id cost parameters', () => {
		const text = buildEmergencyKitText({
			userId: 'u1',
			orgId: 'o1',
			deviceId: 'd1',
			secretKey: 'S',
			kdf: {
				kdf: 'argon2id',
				saltBase64Url: 'salty',
				argon2: { mKiB: 19_456, t: 2, p: 1 },
			},
		});
		expect(text).toContain('Argon2id (RFC 9106)');
		expect(text).toContain('KDF Memory (KiB): 19456');
	});

	it('records PBKDF2 iterations for legacy bundles', () => {
		const text = buildEmergencyKitText({
			userId: 'u1',
			orgId: 'o1',
			deviceId: 'd1',
			secretKey: 'S',
			kdf: { kdf: 'pbkdf2-sha256', saltBase64Url: 'salty', iterations: 310_000 },
		});
		expect(text).toContain('PBKDF2-SHA256');
		expect(text).toContain('KDF Iterations: 310000');
	});
});
