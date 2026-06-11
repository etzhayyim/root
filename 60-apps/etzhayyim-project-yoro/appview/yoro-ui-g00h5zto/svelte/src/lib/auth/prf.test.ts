import { describe, it, expect } from 'vitest';
import {
	accountPrfSalt,
	prfRegistrationExtension,
	prfEvalExtension,
	prfRegistrationEvalExtension,
	extractPrfSecret,
	credentialSupportsPrf,
} from './prf.js';

describe('WebAuthn PRF ceremony helpers (ADR-2606014000 L0)', () => {
	it('accountPrfSalt is a stable 32-byte salt', () => {
		const a = accountPrfSalt('etzhayyim.com');
		const b = accountPrfSalt('etzhayyim.com');
		expect(a.length).toBe(32);
		expect(Array.from(a)).toEqual(Array.from(b));
		expect(Array.from(accountPrfSalt('other'))).not.toEqual(Array.from(a));
	});

	it('registration extension requests prf', () => {
		expect(prfRegistrationExtension()).toEqual({ prf: {} });
	});

	it('eval extension carries the salt under prf.eval.first', () => {
		const salt = accountPrfSalt('x');
		const ext = prfEvalExtension(salt) as any;
		expect(ext.prf.eval.first).toBe(salt);
	});

	it('registration-eval extension carries the salt (add-device, eval at create)', () => {
		const salt = accountPrfSalt('add-device');
		const ext = prfRegistrationEvalExtension(salt) as any;
		expect(ext.prf.eval.first).toBe(salt);
	});

	it('extractPrfSecret returns null when no prf result', () => {
		const fake = {
			getClientExtensionResults: () => ({}),
		} as unknown as PublicKeyCredential;
		expect(extractPrfSecret(fake)).toBeNull();
	});

	it('extractPrfSecret returns the 32-byte first result', () => {
		const secret = new Uint8Array(32).fill(7);
		const cred = {
			getClientExtensionResults: () => ({ prf: { results: { first: secret.buffer } } }),
		} as unknown as PublicKeyCredential;
		const got = extractPrfSecret(cred);
		expect(got).not.toBeNull();
		expect(got!.length).toBe(32);
	});

	it('extractPrfSecret accepts a typed-array (view) first result', () => {
		// The authenticator may return a Uint8Array view rather than a raw ArrayBuffer.
		const secret = new Uint8Array(32).fill(3);
		const cred = {
			getClientExtensionResults: () => ({ prf: { results: { first: secret } } }),
		} as unknown as PublicKeyCredential;
		const got = extractPrfSecret(cred);
		expect(got).not.toBeNull();
		expect(got!.length).toBe(32);
		expect(Array.from(got!)).toEqual(Array.from(secret));
	});

	it('extractPrfSecret rejects a wrong-length result', () => {
		const cred = {
			getClientExtensionResults: () => ({ prf: { results: { first: new Uint8Array(16).buffer } } }),
		} as unknown as PublicKeyCredential;
		expect(extractPrfSecret(cred)).toBeNull();
	});

	it('credentialSupportsPrf reflects the enabled flag', () => {
		const yes = { getClientExtensionResults: () => ({ prf: { enabled: true } }) } as unknown as PublicKeyCredential;
		const no = { getClientExtensionResults: () => ({ prf: { enabled: false } }) } as unknown as PublicKeyCredential;
		expect(credentialSupportsPrf(yes)).toBe(true);
		expect(credentialSupportsPrf(no)).toBe(false);
	});
});
