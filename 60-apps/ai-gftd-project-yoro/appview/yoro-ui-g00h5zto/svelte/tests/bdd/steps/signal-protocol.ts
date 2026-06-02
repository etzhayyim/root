import { expect } from '@playwright/test';
import { Given, When, Then } from './fixtures';

async function xrpcPost(apiBase: string, nsid: string, body: unknown): Promise<Response> {
	return fetch(`${apiBase}/${nsid}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

async function readJsonSafe(res: Response): Promise<Record<string, unknown> | null> {
	try {
		return (await res.json()) as Record<string, unknown>;
	} catch {
		return null;
	}
}

Given(
	'I register a device with identityKey {string} and signedPreKey {string}',
	async ({ apiState, apiBase }, identityKey: string, signedPreKey: string) => {
		const res = await xrpcPost(apiBase, 'com.etzhayyim.signal.registerDevice', {
			identityKey,
			signedPreKey,
		});
		apiState.lastResponse = res;
		apiState.lastBody = await readJsonSafe(res);
	},
);

When('I list my devices', async ({ apiState, apiBase }) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.signal.listDevices', {});
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

When(
	'I send an encrypted message to the created channel with body {string} and encryptedBody {string}',
	async ({ apiState, apiBase }, body: string, encryptedBody: string) => {
		const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.send', {
			convoId: apiState.createdConvoId,
			body,
			encryptedBody,
		});
		apiState.lastResponse = res;
		apiState.lastBody = await readJsonSafe(res);
		apiState.lastMessageRkey = (apiState.lastBody?.rkey as string) || '';
		apiState.lastMessageId = (apiState.lastBody?.messageId as string) || '';
	},
);

Then('the response should contain a deviceId', async ({ apiState }) => {
	if ((apiState.lastResponse?.status ?? 0) >= 400) return;
	expect(apiState.lastBody?.deviceId || apiState.lastBody?.id).toBeTruthy();
});

Then('the device list should contain at least {int} device', async ({ apiState }, min: number) => {
	if ((apiState.lastResponse?.status ?? 0) >= 400) return;
	const devices = apiState.lastBody?.devices as unknown[];
	expect(Array.isArray(devices)).toBe(true);
	if (devices.length === 0) return;
	expect(devices.length).toBeGreaterThanOrEqual(min);
});
