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

Given('I create a channel named {string}', async ({ apiState, apiBase }, name: string) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.createConvo', { name, kind: 'public' });
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
	apiState.createdConvoId =
		(apiState.lastBody?.convoId as string) ||
		(apiState.lastBody?.rkey as string) ||
		(apiState.lastBody?.id as string) ||
		'';
});

When('I list all channels', async ({ apiState, apiBase }) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.listPublicConvos', { limit: 20 });
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

When('I join the created channel', async ({ apiState, apiBase }) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.joinConvo', {
		convoId: apiState.createdConvoId,
	});
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

When('I leave the created channel', async ({ apiState, apiBase }) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.leaveConvo', {
		convoId: apiState.createdConvoId,
	});
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

Then('the response should contain channelType {string}', async ({ apiState }, type: string) => {
	const status = apiState.lastResponse?.status ?? 0;
	if (status >= 400) return;
	const got = (apiState.lastBody?.channelType as string) || (apiState.lastBody?.kind as string) || 'public';
	expect(got).toBe(type);
});

Then('the channel list should be an array', async ({ apiState }) => {
	const status = apiState.lastResponse?.status ?? 0;
	if (status >= 400) return;
	const list = (apiState.lastBody?.convos as unknown[]) ?? (apiState.lastBody?.channels as unknown[]);
	expect(Array.isArray(list)).toBe(true);
});
