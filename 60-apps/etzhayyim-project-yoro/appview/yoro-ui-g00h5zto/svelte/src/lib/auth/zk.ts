import {
	ARGON2ID_DEFAULT_PARAMS,
	deriveKeyArgon2id,
} from '@etzhayyim/sdk/kdf';

import type { KeyDerivationParams, ZkEnvelopeV1, ZkKdfInfo } from './types.js';

const DEFAULT_PBKDF2_ITERATIONS = 310_000;
const WRAPPING_KEY_BYTES = 32;

function toUint8(data: string): Uint8Array {
	return new TextEncoder().encode(data);
}

function toArrayBuffer(bytes: Uint8Array): ArrayBuffer {
	return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
}

function normalizeBase64Url(input: string): string {
	const trimmed = input.trim().replace(/-/g, '+').replace(/_/g, '/');
	const padLength = (4 - (trimmed.length % 4)) % 4;
	return trimmed + '='.repeat(padLength);
}

function toBase64Url(bytes: Uint8Array): string {
	let binary = '';
	for (const b of bytes) binary += String.fromCharCode(b);
	return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function normalizeSecretKey(secretKey: string): string {
	return secretKey.replace(/[\s-]/g, '').toUpperCase();
}

export function parseZkV1Envelope(payload: unknown): ZkEnvelopeV1 {
	if (!payload || typeof payload !== 'object') {
		throw new Error('invalid envelope: expected object');
	}
	const v = payload as Record<string, unknown>;
	if (v.version !== 'zk-v1') {
		throw new Error('invalid envelope: unsupported version');
	}
	return payload as ZkEnvelopeV1;
}

/**
 * Derive the zk wrapping key. New writes default to Argon2id (memory-hard,
 * RFC 9106 — via the @etzhayyim/sdk/kdf seam, per ADR-2606111300 residual
 * #2); `kdf: 'pbkdf2-sha256'` keeps existing envelopes unlockable
 * (crypto-agility read-compat — current + previous suite).
 */
export async function deriveWrappingKey(
	params: KeyDerivationParams
): Promise<{ key: Uint8Array; salt: string } & ZkKdfInfo> {
	const password = params.accountPassword.trim();
	const secret = normalizeSecretKey(params.secretKey);
	if (!password) throw new Error('accountPassword is required');
	if (!secret) throw new Error('secretKey is required');

	const salt =
		params.saltBase64Url ??
		toBase64Url(crypto.getRandomValues(new Uint8Array(16)));
	const saltBytes = Uint8Array.from(atob(normalizeBase64Url(salt)), (c) =>
		c.charCodeAt(0)
	);

	const kdf = params.kdf ?? 'argon2id';

	if (kdf === 'argon2id') {
		const derived = deriveKeyArgon2id({
			password: `${password}:${secret}`,
			salt: saltBytes,
			params: params.argon2 ?? ARGON2ID_DEFAULT_PARAMS,
			dkLen: WRAPPING_KEY_BYTES,
		});
		return {
			key: derived.key,
			kdf,
			salt,
			saltBase64Url: salt,
			argon2: derived.params,
		};
	}

	const iterations = params.iterations ?? DEFAULT_PBKDF2_ITERATIONS;
	if (iterations < 150_000) throw new Error('iterations must be >= 150000');

	const keyMaterial = await crypto.subtle.importKey(
		'raw',
		toArrayBuffer(toUint8(`${password}:${secret}`)),
		'PBKDF2',
		false,
		['deriveBits']
	);

	const bits = await crypto.subtle.deriveBits(
		{
			name: 'PBKDF2',
			hash: 'SHA-256',
			iterations,
			salt: toArrayBuffer(saltBytes),
		},
		keyMaterial,
		WRAPPING_KEY_BYTES * 8
	);

	return {
		key: new Uint8Array(bits),
		kdf,
		salt,
		saltBase64Url: salt,
		iterations,
	};
}
