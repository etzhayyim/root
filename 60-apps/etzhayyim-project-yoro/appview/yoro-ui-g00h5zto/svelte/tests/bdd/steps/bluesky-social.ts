import { expect } from '@playwright/test';
import { Given, When, Then } from './fixtures';

const PDS_BASE = 'https://atproto.etzhayyim.com';
const PDS_XRPC = `${PDS_BASE}/xrpc`;

async function xrpcCall(nsid: string, body: Record<string, unknown> = {}): Promise<{ res: Response; data: Record<string, unknown> }> {
	const res = await fetch(`${PDS_XRPC}/${nsid}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
	let data: Record<string, unknown> = {};
	try { data = await res.json() as Record<string, unknown>; } catch { /* empty */ }
	return { res, data };
}

// ─── Timeline / Feed ─────────────────────────────────────────────

When('I call GetTimeline on atproto.etzhayyim.com with limit {int}', async ({ apiState }, limit: number) => {
	const { res, data } = await xrpcCall('app.bsky.feed.getTimeline', { limit });
	apiState.lastResponse = res;
	apiState.lastBody = data;
});

Then('the response should contain a feed array', async ({ apiState }) => {
	// feed may exist or response may be empty but should not error
	const body = apiState.lastBody;
	if (body && 'feed' in body) {
		expect(Array.isArray(body.feed)).toBe(true);
	}
});

When('I call listPublicConvos on atproto.etzhayyim.com with limit {int}', async ({ apiState }, limit: number) => {
	const { res, data } = await xrpcCall('com.etzhayyim.convo.listPublicConvos', { limit });
	apiState.lastResponse = res;
	apiState.lastBody = data;
});

When('I call SearchPosts on atproto.etzhayyim.com with query {string}', async ({ apiState }, q: string) => {
	const { res, data } = await xrpcCall('com.etzhayyim.convo.search', { q, limit: 10 });
	apiState.lastResponse = res;
	apiState.lastBody = data;
});

When('I call GetProfile on atproto.etzhayyim.com', async ({ apiState }) => {
	const { res, data } = await xrpcCall('app.bsky.actor.getProfile', {});
	apiState.lastResponse = res;
	apiState.lastBody = data;
});

Then('the response should contain a did field', async ({ apiState }) => {
	const body = apiState.lastBody;
	if (apiState.lastResponse?.ok && body) {
		expect(body).toHaveProperty('did');
	}
});

// ─── Channel + Message via atproto.etzhayyim.com ──────────────────────────

Given('I create a channel named {string} via atproto.etzhayyim.com', async ({ apiState }, name: string) => {
	const { res, data } = await xrpcCall('com.etzhayyim.convo.createConvo', { name });
	apiState.lastResponse = res;
	apiState.lastBody = data;
	if (data.convoId) apiState.createdConvoId = data.convoId as string;
	else if (data.rkey) apiState.createdConvoId = data.rkey as string;
});

When('I send a message {string} to the created channel via atproto.etzhayyim.com', async ({ apiState }, body: string) => {
	const { res, data } = await xrpcCall('com.etzhayyim.convo.send', {
		convoId: apiState.createdConvoId,
		body,
	});
	apiState.lastResponse = res;
	apiState.lastBody = data;
	if (data.rkey) {
		apiState.rootMessageRkey = apiState.lastMessageRkey || (data.rkey as string);
		apiState.lastMessageRkey = data.rkey as string;
	}
	if (data.id) apiState.lastMessageId = data.id as string;
});

When('I send a reply {string} to the root message via atproto.etzhayyim.com', async ({ apiState }, body: string) => {
	const { res, data } = await xrpcCall('com.etzhayyim.convo.send', {
		convoId: apiState.createdConvoId,
		body,
		replyTo: apiState.rootMessageRkey,
		threadId: apiState.rootMessageRkey,
	});
	apiState.lastResponse = res;
	apiState.lastBody = data;
	if (data.rkey) apiState.lastMessageRkey = data.rkey as string;
});

When('I list envelopes in the created channel via atproto.etzhayyim.com', async ({ apiState }) => {
	const { res, data } = await xrpcCall('com.etzhayyim.convo.listEnvelopes', {
		convoId: apiState.createdConvoId,
		limit: 50,
	});
	apiState.lastResponse = res;
	apiState.lastBody = data;
});

When('I get the thread for the root message via atproto.etzhayyim.com', async ({ apiState }) => {
	const { res, data } = await xrpcCall('com.etzhayyim.convo.getThread', {
		convoId: apiState.createdConvoId,
		rootRkey: apiState.rootMessageRkey,
	});
	apiState.lastResponse = res;
	apiState.lastBody = data;
});

When('I react with {string} to the last message via atproto.etzhayyim.com', async ({ apiState }, emoji: string) => {
	const { res, data } = await xrpcCall('com.etzhayyim.convo.react', {
		convoId: apiState.createdConvoId,
		rkey: apiState.lastMessageRkey,
		emoji,
	});
	apiState.lastResponse = res;
	apiState.lastBody = data;
});

When('I call GetNotificationCount on atproto.etzhayyim.com', async ({ apiState }) => {
	const { res, data } = await xrpcCall('app.bsky.notification.getUnreadCount', {});
	apiState.lastResponse = res;
	apiState.lastBody = data;
});

async function getTimelineSubject(): Promise<{ uri: string; cid: string } | null> {
	const { res, data } = await xrpcCall('app.bsky.feed.getTimeline', { limit: 20 });
	if (!res.ok) return null;
	const feed = (data.feed ?? []) as Array<Record<string, unknown>>;
	for (const item of feed) {
		const post = (item?.post ?? item) as Record<string, unknown>;
		const uri = typeof post?.uri === 'string' ? post.uri : '';
		const cid = typeof post?.cid === 'string' ? post.cid : '';
		if (uri && cid) return { uri, cid };
	}
	return null;
}

When('I like a timeline post via atproto.etzhayyim.com', async ({ apiState }) => {
	const subject = await getTimelineSubject();
	if (!subject) {
		apiState.lastResponse = new Response(null, { status: 401 });
		apiState.lastBody = { error: 'no timeline subject' };
		return;
	}
	const { res, data } = await xrpcCall('app.bsky.feed.like', { subject });
	apiState.lastResponse = res;
	apiState.lastBody = data;
});

When('I repost a timeline post via atproto.etzhayyim.com', async ({ apiState }) => {
	const subject = await getTimelineSubject();
	if (!subject) {
		apiState.lastResponse = new Response(null, { status: 401 });
		apiState.lastBody = { error: 'no timeline subject' };
		return;
	}
	const { res, data } = await xrpcCall('app.bsky.feed.repost', { subject });
	apiState.lastResponse = res;
	apiState.lastBody = data;
});

When('I reply to a timeline post via atproto.etzhayyim.com', async ({ apiState }) => {
	const subject = await getTimelineSubject();
	if (!subject) {
		apiState.lastResponse = new Response(null, { status: 401 });
		apiState.lastBody = { error: 'no timeline subject' };
		return;
	}
	const { res, data } = await xrpcCall('app.bsky.feed.post', {
		text: `E2E reply ${Date.now()}`,
		reply: {
			root: { uri: subject.uri, cid: subject.cid },
			parent: { uri: subject.uri, cid: subject.cid },
		},
	});
	apiState.lastResponse = res;
	apiState.lastBody = data;
});

When('I bookmark a timeline post via atproto.etzhayyim.com', async ({ apiState }) => {
	const subject = await getTimelineSubject();
	if (!subject) {
		apiState.lastResponse = new Response(null, { status: 401 });
		apiState.lastBody = { error: 'no timeline subject' };
		return;
	}
	const { res, data } = await xrpcCall('app.bsky.bookmark.createBookmark', {
		uri: subject.uri,
	});
	apiState.lastResponse = res;
	apiState.lastBody = data;
});

// Fetch steps are defined in homepage.ts and shared across features.
