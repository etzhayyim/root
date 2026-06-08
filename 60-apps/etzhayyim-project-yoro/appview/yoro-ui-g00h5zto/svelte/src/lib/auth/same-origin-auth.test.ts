import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { signInSameOrigin } from './same-origin-auth.js';

const originalNavigator = globalThis.navigator;
const originalLocalStorage = globalThis.localStorage;
const originalWindow = (globalThis as any).window;

function installLocalStorage() {
	const store: Record<string, string> = {};
	const storage = {
		getItem: vi.fn((key: string) => store[key] ?? null),
		setItem: vi.fn((key: string, value: string) => {
			store[key] = value;
		}),
		removeItem: vi.fn((key: string) => {
			delete store[key];
		}),
		clear: vi.fn(() => {
			for (const key of Object.keys(store)) delete store[key];
		}),
		key: vi.fn((index: number) => Object.keys(store)[index] ?? null),
		get length() {
			return Object.keys(store).length;
		},
	} as unknown as Storage;
	Object.defineProperty(globalThis, 'localStorage', { value: storage, configurable: true });
	return storage;
}

function installWebAuthn(assertion: PublicKeyCredential) {
	Object.defineProperty(globalThis, 'navigator', {
		value: {
			credentials: {
				get: vi.fn().mockResolvedValue(assertion),
			},
		},
		configurable: true,
	});
	(globalThis as any).window = {};
}

function fakeAssertion(rawId: Uint8Array, extensionResults: Record<string, unknown> = {}): PublicKeyCredential {
	return {
		rawId: rawId.buffer.slice(rawId.byteOffset, rawId.byteOffset + rawId.byteLength),
		getClientExtensionResults: () => extensionResults,
	} as unknown as PublicKeyCredential;
}

describe('same-origin passkey sign-in', () => {
	beforeEach(() => {
		installLocalStorage();
	});

	afterEach(() => {
		vi.restoreAllMocks();
		Object.defineProperty(globalThis, 'navigator', { value: originalNavigator, configurable: true });
		Object.defineProperty(globalThis, 'localStorage', { value: originalLocalStorage, configurable: true });
		(globalThis as any).window = originalWindow;
	});

	it('falls back to the stored DID when the selected provider returns no PRF and has no credential map', async () => {
		const storedDid = 'did:key:z6MkiExistingAccount';
		localStorage.setItem('etzhayyim-auth-did', storedDid);
		installWebAuthn(fakeAssertion(new Uint8Array([1, 2, 3, 4])));

		const result = await signInSameOrigin(() => Date.parse('2026-06-08T00:00:00.000Z'));

		expect(result).toMatchObject({
			did: storedDid,
			handle: 'member-6mkiexis',
			method: 'p256-passkey',
			serverConfirmed: false,
		});
		expect(localStorage.getItem('etzhayyim-auth-cred-did')).toContain(storedDid);
	});
});
