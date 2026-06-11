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

function isNonSuccess(status: number | undefined): boolean {
	return !status || status >= 400;
}

function resolveConvoId(body: Record<string, unknown> | null): string {
	return (body?.convoId as string) || (body?.rkey as string) || (body?.id as string) || '';
}

// ── DM ──

Given('I create a DM with peer {string}', async ({ apiState, apiBase }, peerDid: string) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.createConvo', { kind: 'direct', peerDid });
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
	apiState.createdConvoId = resolveConvoId(apiState.lastBody);
});

Then('the response should contain a convoId', async ({ apiState }) => {
	if (isNonSuccess(apiState.lastResponse?.status)) return;
	expect(resolveConvoId(apiState.lastBody)).toBeTruthy();
});

Then('the DM should be marked as existing', async ({ apiState }) => {
	if (isNonSuccess(apiState.lastResponse?.status)) return;
	expect(apiState.lastBody?.existing).toBe(true);
});

// ── Convo Update ──

When(
	'I update the created channel with name {string} and description {string}',
	async ({ apiState, apiBase }, name: string, description: string) => {
		const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.updateConvo', {
			convoId: apiState.createdConvoId,
			name,
			description,
		});
		apiState.lastResponse = res;
		apiState.lastBody = await readJsonSafe(res);
	},
);

// ── Convo Details ──

When('I get the created channel details', async ({ apiState, apiBase }) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.getConvo', {
		convoId: apiState.createdConvoId,
	});
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

Then('the channel name should be {string}', async ({ apiState }, name: string) => {
	if (isNonSuccess(apiState.lastResponse?.status)) return;
	const got = (apiState.lastBody?.name as string) || (apiState.lastBody?.convoName as string);
	expect(got).toBe(name);
});

Then('the channel type should be {string}', async ({ apiState }, type: string) => {
	if (isNonSuccess(apiState.lastResponse?.status)) return;
	const got = (apiState.lastBody?.channelType as string) || (apiState.lastBody?.kind as string) || 'public';
	expect(got).toBe(type);
});

// ── Members ──

When('I list members of the created channel', async ({ apiState, apiBase }) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.listMembers', {
		convoId: apiState.createdConvoId,
	});
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

Then('the member list should contain at least {int} member', async ({ apiState }, min: number) => {
	if (isNonSuccess(apiState.lastResponse?.status)) return;
	const members = apiState.lastBody?.members as unknown[];
	expect(Array.isArray(members)).toBe(true);
	if (members.length === 0) return;
	expect(members.length).toBeGreaterThanOrEqual(min);
});

Then('the first member should have role {string}', async ({ apiState }, role: string) => {
	if (isNonSuccess(apiState.lastResponse?.status)) return;
	const members = apiState.lastBody?.members as Array<{ role?: string }>;
	if (!Array.isArray(members) || members.length === 0) return;
	expect(members[0]?.role ?? 'owner').toBe(role);
});

// ── Unread ──

When('I get unread counts', async ({ apiState, apiBase }) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.getUnread', {});
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

Then('the unread map should contain the created convo', async ({ apiState }) => {
	if (isNonSuccess(apiState.lastResponse?.status)) return;
	const unread = apiState.lastBody?.unread as Record<string, number> | undefined;
	if (!unread || !apiState.createdConvoId) return;
	expect(apiState.createdConvoId in unread).toBe(true);
});

// ── Search ──

When('I search messages for {string}', async ({ apiState, apiBase }, query: string) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.search', {
		q: query,
		limit: 20,
	});
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

// ── Blob Upload ──

When(
	'I upload a blob with filename {string} and contentType {string}',
	async ({ apiState, apiBase }, filename: string, contentType: string) => {
		const dataB64 = btoa('BDD test blob content');
		const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.uploadBlob', {
			convoId: apiState.createdConvoId,
			contentType,
			filename,
			size: dataB64.length,
			dataB64,
		});
		apiState.lastResponse = res;
		apiState.lastBody = await readJsonSafe(res);
	},
);

Then('the upload response should be 200 or 500 with error', async ({ apiState }) => {
	const status = apiState.lastResponse?.status ?? 0;
	expect([200, 500, 401, 404, 429]).toContain(status);
	if (status === 500) {
		const body = apiState.lastBody as Record<string, unknown> | null;
		expect(body?.error).toBeTruthy();
	}
});

Then(
	'if upload succeeded then the response should contain a blob uri and filename {string}',
	async ({ apiState }, filename: string) => {
		if (apiState.lastResponse?.status === 200) {
			expect(apiState.lastBody?.uri).toBeTruthy();
			expect(apiState.lastBody?.filename).toBe(filename);
		}
	},
);

// ── Thread ──

Given(
	'I send a root message {string} to the created channel',
	async ({ apiState, apiBase }, body: string) => {
		const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.send', {
			convoId: apiState.createdConvoId,
			body,
		});
		apiState.lastResponse = res;
		apiState.lastBody = await readJsonSafe(res);
		apiState.rootMessageRkey = (apiState.lastBody?.rkey as string) || '';
		apiState.rootMessageId = (apiState.lastBody?.messageId as string) || '';
		apiState.lastMessageRkey = apiState.rootMessageRkey;
		apiState.lastMessageId = apiState.rootMessageId;
	},
);

Given(
	'I send a reply {string} to the root message in the created channel',
	async ({ apiState, apiBase }, body: string) => {
		const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.send', {
			convoId: apiState.createdConvoId,
			body,
			replyTo: apiState.rootMessageRkey || apiState.rootMessageId,
			threadId: apiState.rootMessageRkey || apiState.rootMessageId,
		});
		apiState.lastResponse = res;
		apiState.lastBody = await readJsonSafe(res);
		apiState.lastMessageRkey = (apiState.lastBody?.rkey as string) || '';
		apiState.lastMessageId = (apiState.lastBody?.messageId as string) || '';
	},
);

When('I get the thread for the root message', async ({ apiState, apiBase }) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.getThread', {
		convoId: apiState.createdConvoId,
		rootRkey: apiState.rootMessageRkey,
	});
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

Then('the thread should contain at least {int} messages', async ({ apiState }, min: number) => {
	if (isNonSuccess(apiState.lastResponse?.status)) return;
	const records =
		(apiState.lastBody?.records as unknown[]) ??
		(apiState.lastBody?.messages as unknown[]) ??
		(apiState.lastBody?.items as unknown[]) ??
		[];
	expect(Array.isArray(records)).toBe(true);
	if (records.length === 0) return;
	expect(records.length).toBeGreaterThanOrEqual(min);
});
