import { KeyBundleClient } from './key-bundles.js';
import type {
	EnrollKeyBundleInput,
	EnrollKeyBundleResult,
	FetchAndUnlockKeyBundleInput,
	FetchAndUnlockKeyBundleResult,
	KeyBundleClientConfig,
	ZkEnvelopeV1,
} from './types.js';
import { deriveWrappingKey, parseZkV1Envelope } from './zk.js';

const SECRET_KEY_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

function randomInt(max: number): number {
	const arr = crypto.getRandomValues(new Uint32Array(1));
	return arr[0] % max;
}

export function generateSecretKey(segments = 6, charsPerSegment = 5): string {
	if (segments <= 0 || charsPerSegment <= 0) {
		throw new Error('segments and charsPerSegment must be > 0');
	}
	const out: string[] = [];
	for (let s = 0; s < segments; s++) {
		let part = '';
		for (let i = 0; i < charsPerSegment; i++) {
			part += SECRET_KEY_ALPHABET[randomInt(SECRET_KEY_ALPHABET.length)];
		}
		out.push(part);
	}
	return out.join('-');
}

function parseEnvelopeJson(envelopeJson: string): ZkEnvelopeV1 {
	let parsed: unknown;
	try {
		parsed = JSON.parse(envelopeJson);
	} catch {
		throw new Error('invalid envelopeJson: expected valid JSON');
	}
	return parseZkV1Envelope(parsed);
}

function requireBinding(
	envelope: ZkEnvelopeV1,
	orgId: string,
	userId: string,
	deviceId: string,
): void {
	if (envelope.owner.clerkOrgId !== orgId) {
		throw new Error('envelope org binding mismatch');
	}
	if (envelope.owner.clerkUserId !== userId) {
		throw new Error('envelope user binding mismatch');
	}
	if (envelope.deviceId !== deviceId) {
		throw new Error('envelope device binding mismatch');
	}
}

function attachKdfMetadata(
	envelope: ZkEnvelopeV1,
	saltBase64Url: string,
	iterations: number,
): ZkEnvelopeV1 {
	return {
		...envelope,
		aad: {
			...envelope.aad,
			kdfSaltB64url: saltBase64Url,
			kdfIterations: iterations,
		},
	};
}

function getKdfMetadata(envelope: ZkEnvelopeV1): { saltBase64Url: string; iterations: number } {
	const salt = String(envelope.aad.kdfSaltB64url ?? '').trim();
	const iterationsRaw = envelope.aad.kdfIterations;
	const iterations =
		typeof iterationsRaw === 'number'
			? iterationsRaw
			: Number.parseInt(String(iterationsRaw ?? ''), 10);
	if (!salt) {
		throw new Error('missing kdfSaltB64url in envelope.aad');
	}
	if (!Number.isFinite(iterations) || iterations < 150_000) {
		throw new Error('invalid kdfIterations in envelope.aad');
	}
	return { saltBase64Url: salt, iterations };
}

function encodeEnvelope(envelope: ZkEnvelopeV1): string {
	return JSON.stringify(envelope);
}

function makeClient(config?: KeyBundleClientConfig): KeyBundleClient {
	return new KeyBundleClient(config);
}

export async function enrollKeyBundle(
	input: EnrollKeyBundleInput,
): Promise<EnrollKeyBundleResult> {
	const orgId = input.orgId.trim();
	const userId = input.userId.trim();
	const deviceId = input.deviceId.trim();
	const envelope = parseEnvelopeJson(input.envelopeJson);
	requireBinding(envelope, orgId, userId, deviceId);

	const kdf = await deriveWrappingKey({
		accountPassword: input.accountPassword,
		secretKey: input.secretKey,
		saltBase64Url: input.saltBase64Url,
		iterations: input.iterations,
	});
	const envelopeWithKdf = attachKdfMetadata(envelope, kdf.salt, kdf.iterations);
	const client = makeClient(input.clientConfig);
	const bundle = await client.upsertBundle({
		orgId,
		userId,
		deviceId,
		version: envelope.version,
		envelopeJson: encodeEnvelope(envelopeWithKdf),
	});

	return {
		bundle,
		kdf: {
			saltBase64Url: kdf.salt,
			iterations: kdf.iterations,
		},
	};
}

export async function fetchAndUnlockKeyBundle(
	input: FetchAndUnlockKeyBundleInput,
): Promise<FetchAndUnlockKeyBundleResult> {
	const orgId = input.orgId.trim();
	const userId = input.userId.trim();
	const deviceId = input.deviceId.trim();
	const client = makeClient(input.clientConfig);
	const bundle = await client.fetchBundle({ orgId, userId, deviceId });
	const envelope = parseEnvelopeJson(bundle.envelopeJson);
	requireBinding(envelope, orgId, userId, deviceId);

	const meta = getKdfMetadata(envelope);
	const derived = await deriveWrappingKey({
		accountPassword: input.accountPassword,
		secretKey: input.secretKey,
		saltBase64Url: meta.saltBase64Url,
		iterations: meta.iterations,
	});

	return {
		bundle,
		envelope,
		kdf: {
			saltBase64Url: derived.salt,
			iterations: derived.iterations,
		},
		wrappingKey: derived.key,
	};
}

export function buildEmergencyKitText(input: {
	userId: string;
	orgId: string;
	deviceId: string;
	secretKey: string;
	saltBase64Url: string;
	iterations: number;
	issuedAt?: Date;
}): string {
	const issuedAt = (input.issuedAt ?? new Date()).toISOString();
	return [
		'# etzhayyim Emergency Kit',
		'',
		'Keep this file offline in a secure location.',
		`Issued At: ${issuedAt}`,
		`User ID: ${input.userId}`,
		`Org ID: ${input.orgId}`,
		`Device ID: ${input.deviceId}`,
		`Secret Key: ${input.secretKey}`,
		`KDF Salt (base64url): ${input.saltBase64Url}`,
		`KDF Iterations: ${input.iterations}`,
		'',
		'Without Account Password + Secret Key, encrypted data cannot be decrypted.',
	].join('\n');
}

export function downloadEmergencyKit(filename: string, content: string): void {
	const safeName = filename.trim() || 'etzhayyim-emergency-kit.txt';
	const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
	const url = URL.createObjectURL(blob);
	try {
		const a = document.createElement('a');
		a.href = url;
		a.download = safeName;
		a.rel = 'noopener';
		a.click();
	} finally {
		URL.revokeObjectURL(url);
	}
}
