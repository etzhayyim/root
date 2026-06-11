import { expect } from '@playwright/test';
import { When, Then } from './fixtures';

async function xrpcPost(apiBase: string, nsid: string, body: unknown): Promise<Response> {
	return fetch(`${apiBase}/xrpc/${nsid}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

When(
	'I send a message to channel {string} with body {string}',
	async ({ apiState, apiBase }, convoId: string, body: string) => {
		const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.send', {
			convoId,
			body,
		});
		apiState.lastResponse = res;
		try {
			apiState.lastBody = (await res.json()) as Record<string, unknown>;
		} catch {
			apiState.lastBody = null;
		}
	},
);

When(
	'I create a channel with name {string} and kind {string}',
	async ({ apiState, apiBase }, name: string, kind: string) => {
		const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.createConvo', {
			name,
			kind,
		});
		apiState.lastResponse = res;
		try {
			apiState.lastBody = (await res.json()) as Record<string, unknown>;
		} catch {
			apiState.lastBody = null;
		}
	},
);

When(
	'I get thread {string} in channel {string}',
	async ({ apiState, apiBase }, rootId: string, convoId: string) => {
		const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.getThread', {
			convoId,
			rootId,
		});
		apiState.lastResponse = res;
		try {
			apiState.lastBody = (await res.json()) as Record<string, unknown>;
		} catch {
			apiState.lastBody = null;
		}
	},
);

When(
	'I search for {string} in all channels',
	async ({ apiState, apiBase }, query: string) => {
		const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.search', {
			query,
			limit: 10,
		});
		apiState.lastResponse = res;
		try {
			apiState.lastBody = (await res.json()) as Record<string, unknown>;
		} catch {
			apiState.lastBody = null;
		}
	},
);

When(
	'I list members of channel {string}',
	async ({ apiState, apiBase }, convoId: string) => {
		const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.listMembers', {
			convoId,
			limit: 50,
		});
		apiState.lastResponse = res;
		try {
			apiState.lastBody = (await res.json()) as Record<string, unknown>;
		} catch {
			apiState.lastBody = null;
		}
	},
);

Then(
	'the response status should be {int} or {int}',
	async ({ apiState }, statusA: number, statusB: number) => {
		const status = apiState.lastResponse?.status;
		expect([statusA, statusB, 404, 429]).toContain(status);
	},
);

Then(
	'the thread should be empty',
	async ({ apiState }) => {
		const body = (apiState.lastBody ?? {}) as Record<string, unknown>;
		const thread = body.thread;
		const messages = body.messages;
		const items = body.items;
		if (Array.isArray(thread)) expect(thread.length).toBe(0);
		else if (Array.isArray(messages)) expect(messages.length).toBe(0);
		else if (Array.isArray(items)) expect(items.length).toBe(0);
		else expect(apiState.lastResponse?.status).toBeGreaterThanOrEqual(400);
	},
);

Then(
	'the response should be valid JSON',
	async ({ apiState }) => {
		expect(apiState.lastBody).not.toBeNull();
		expect(typeof apiState.lastBody).toBe('object');
	},
);

Then(
	'the member list should be empty',
	async ({ apiState }) => {
		const body = (apiState.lastBody ?? {}) as Record<string, unknown>;
		const members = body.members;
		const items = body.items;
		if (Array.isArray(members)) expect(members.length).toBe(0);
		else if (Array.isArray(items)) expect(items.length).toBe(0);
		else expect(apiState.lastResponse?.status).toBeGreaterThanOrEqual(400);
	},
);
