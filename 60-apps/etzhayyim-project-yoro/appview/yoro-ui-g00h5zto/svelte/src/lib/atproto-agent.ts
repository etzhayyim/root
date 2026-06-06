import { AtpAgent } from '@etzhayyim/sdk/atproto';
import { setSignalTransport } from '@etzhayyim/signal';

export type Did = string;
export type ConvoId = string;
export type Convo = Record<string, unknown>;
export type ConvoEntry = Record<string, unknown>;
export type ConvoGroup = Record<string, unknown>;
export type ConvoMember = Record<string, unknown>;
export type ConvoSection = string;
export type ConvoSnapshot = Record<string, unknown>;
export type AuthorProfile = Record<string, unknown>;
export type PostView = Record<string, unknown>;
export type FeedItem = Record<string, unknown>;
export type FollowView = Record<string, unknown>;
export type FeedGeneratorView = Record<string, unknown>;
export type ListView = Record<string, unknown>;
export type StarterPackView = Record<string, unknown>;
export type MutedUser = Record<string, unknown>;
export type BlockedUser = Record<string, unknown>;
export type ThreadgateRule = Record<string, unknown>;
export type ThreadgateView = Record<string, unknown>;
export type RichTextFacet = Record<string, unknown>;
export type FacetFeature = Record<string, unknown>;
export type LabelView = Record<string, unknown>;
export type LabelValue = string;
export type SelfLabel = Record<string, unknown>;
export type NotificationReason = string;
export type NotificationView = Record<string, unknown>;
export type ConversationKind = string;
export type ConvoParticipantType = string;
export type ConvoEnvelope = Record<string, unknown>;
export type PresenceState = Record<string, unknown>;
export type UnreadCounts = Record<string, unknown>;
export type SyncSnapshot = Record<string, unknown>;
export type SyncState = string;
export type StreamEvent = Record<string, unknown>;
export type StreamState = string;
export type StreamConnection = { close?: () => void; unsubscribe?: () => void } & Record<string, unknown>;
export type CallSignal = Record<string, unknown>;
export type ConsentGrant = Record<string, unknown>;
export type PostAuthor = AuthorProfile;
export type PostEmbedView = Record<string, unknown>;
export type CardType = string;
export type CardPersonPayload = Record<string, unknown>;
export type CardOrganizationPayload = Record<string, unknown>;
export type CardServicePayload = Record<string, unknown>;
export type CardSystemPayload = Record<string, unknown>;
export type Session = {
	did: string;
	handle?: string;
	accessJwt: string;
	refreshJwt?: string;
};
export type Diff = Record<string, unknown>;

type XrpcOptions = {
	auth?: boolean;
	bearerToken?: string;
	timeout?: number;
};
type TokenProvider = () => string | Promise<string>;
type FeedOptions = {
	limit?: number;
	cursor?: string;
	light?: boolean;
};

const DEFAULT_SERVICE = 'https://atproto.etzhayyim.com';
const service = DEFAULT_SERVICE;

export const agent = new AtpAgent({ service });

// Feed/profile reads served browser-locally by the kotoba Service Worker
// (kotoba-sw.js) from the in-page kotoba Datom log. A Service Worker can only
// intercept SAME-ORIGIN requests, so these NSIDs must be sent to the apex
// origin (etzhayyim.com/xrpc/...) rather than the cross-origin PDS — otherwise
// the SW never sees them. Every other NSID keeps the direct PDS/AppView URL
// (Candidate C topology unchanged). When the SW is inactive these fall through
// to the apex Worker, identical to prior behaviour. (ADR-2605312345 /
// 2605215000 / 2606013800.)
const SW_LOCAL_NSIDS = new Set<string>([
	'app.bsky.feed.getTimeline',
	'app.bsky.feed.getDiscoverFeed',
	'app.bsky.feed.getAuthorFeed',
	'app.bsky.feed.getPostThread',
	'app.bsky.actor.getProfile',
	// writes (post / reply / comment / like / repost) — member-signed + stored
	// in the in-page kotoba node by kotoba-sw.js (Wikipedia-style local edits).
	'com.atproto.repo.createRecord',
]);

let tokenProvider: TokenProvider | null = null;
let inMemorySession: Session | null = null;
let lastSyncedJwt = '';

function readStoredSession(): Session | null {
	if (typeof localStorage === 'undefined') return inMemorySession;
	for (const key of ['atproto:session', 'etzhayyim:session']) {
		const raw = localStorage.getItem(key);
		if (!raw) continue;
		try {
			const parsed = JSON.parse(raw) as Partial<Session> & { accessToken?: string; jwt?: string };
			const accessJwt = parsed.accessJwt ?? parsed.accessToken ?? parsed.jwt;
			if (parsed.did && accessJwt) return { did: parsed.did, handle: parsed.handle, accessJwt, refreshJwt: parsed.refreshJwt };
		} catch {
			continue;
		}
	}
	return inMemorySession;
}

function storeSession(session: Session | null): void {
	inMemorySession = session;
	if (typeof localStorage === 'undefined') return;
	if (session) localStorage.setItem('atproto:session', JSON.stringify(session));
	else localStorage.removeItem('atproto:session');
}

async function getBearerToken(opts: XrpcOptions = {}): Promise<string> {
	if (opts.bearerToken) return opts.bearerToken;
	if (tokenProvider) return await tokenProvider();
	const session = readStoredSession();
	return session?.accessJwt ?? '';
}

export function getSession(): Session | null {
	return readStoredSession();
}

export function setSession(session: Session): void {
	storeSession(session);
	syncFromAtprotoSession();
}

export function clearSession(): void {
	storeSession(null);
	lastSyncedJwt = '';
	void agent.logout();
}

export function setTokenProvider(provider: TokenProvider | null): void {
	tokenProvider = provider;
}

export function syncFromAtprotoSession(): void {
	const session = readStoredSession();
	if (!session) {
		if (lastSyncedJwt) void agent.logout();
		lastSyncedJwt = '';
		return;
	}
	if (session.accessJwt === lastSyncedJwt) return;
	agent.sessionManager.session = {
		did: session.did,
		handle: session.handle ?? session.did,
		accessJwt: session.accessJwt,
		refreshJwt: session.refreshJwt ?? '',
		active: true,
	};
	lastSyncedJwt = session.accessJwt;
}

async function xrpc<T>(method: 'GET' | 'POST', nsid: string, data?: unknown, opts: XrpcOptions = {}): Promise<T> {
	const controller = new AbortController();
	const timeout = typeof window !== 'undefined' ? window.setTimeout(() => controller.abort(), opts.timeout ?? 30_000) : undefined;
	try {
		// SW-handled feed/profile reads go same-origin so kotoba-sw.js can
		// intercept them; all other NSIDs keep the direct PDS URL.
		const base =
			typeof window !== 'undefined' && SW_LOCAL_NSIDS.has(nsid)
				? window.location.origin
				: service;
		const url = new URL(`/xrpc/${nsid}`, base);
		const bearer = await getBearerToken(opts);
		const init: RequestInit = {
			method,
			headers: {
				...(method === 'POST' ? { 'content-type': 'application/json' } : {}),
				...(bearer ? { authorization: `Bearer ${bearer}` } : {}),
			},
			signal: controller.signal,
		};
		if (method === 'GET' && data && typeof data === 'object') {
			for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
				if (value === undefined || value === null) continue;
				url.searchParams.set(key, String(value));
			}
		} else if (method === 'POST') {
			init.body = JSON.stringify(data ?? {});
		}
		const res = await fetch(url, init);
		const body = await res.json().catch((_err) => ({}));
		if (!res.ok) throw new Error((body as { message?: string; error?: string }).message ?? (body as { error?: string }).error ?? `${nsid} failed (${res.status})`);
		return body as T;
	} finally {
		if (timeout !== undefined && typeof window !== 'undefined') window.clearTimeout(timeout);
	}
}

export function atProcedure<T = unknown>(nsid: string, body?: unknown, opts?: XrpcOptions): Promise<T> {
	return xrpc<T>('POST', nsid, body, opts);
}

export function atQuery<T = unknown>(nsid: string, params?: Record<string, unknown>, opts?: XrpcOptions): Promise<T> {
	return xrpc<T>('GET', nsid, params, opts);
}

setSignalTransport({
	procedure: <T>(nsid: string, body: unknown) => atProcedure<T>(nsid, body),
	query: <T>(nsid: string, params: Record<string, unknown>) => atQuery<T>(nsid, params),
});

export function getCurrentDID(): string {
	syncFromAtprotoSession();
	return agent.session?.did ?? readStoredSession()?.did ?? '';
}

export function isDid(value: string): boolean {
	return value.startsWith('did:');
}

export function formatDID(did: string): string {
	if (did.startsWith('did:web:')) return did.slice(8);
	if (did.length > 24) return `${did.slice(0, 18)}...`;
	return did;
}

export const memberLabel = formatDID;

export async function resolveHandle(handle: string): Promise<string> {
	syncFromAtprotoSession();
	const normalized = handle.replace(/^@/, '').trim().toLowerCase();
	const { data } = await agent.com.atproto.identity.resolveHandle({ handle: normalized });
	return data.did;
}

export async function getAuthorProfile(actor: string): Promise<AuthorProfile> {
	syncFromAtprotoSession();
	return atQuery<AuthorProfile>('app.bsky.actor.getProfile', { actor });
}

export const getProfile = getAuthorProfile;
export const yoroGetProfile = getAuthorProfile;

export async function searchActors(q: string, limit = 25): Promise<AuthorProfile[]> {
	syncFromAtprotoSession();
	const { data } = await agent.app.bsky.actor.searchActors({ q, limit });
	return data.actors as AuthorProfile[];
}

export const yoroSearchActors = searchActors;
export const searchActorsTypeahead = searchActors;

export async function searchPosts(q: string, limit = 25): Promise<PostView[]> {
	syncFromAtprotoSession();
	const data = await atQuery<{ posts?: PostView[] }>('app.bsky.feed.searchPosts', { q, limit });
	return (data.posts ?? []) as PostView[];
}

function normalizeFeedOptions(limitOrOpts: number | FeedOptions | undefined, cursor?: string): FeedOptions {
	if (limitOrOpts && typeof limitOrOpts === 'object') {
		return {
			limit: limitOrOpts.limit ?? 50,
			cursor: limitOrOpts.cursor,
			light: limitOrOpts.light,
		};
	}
	return { limit: limitOrOpts ?? 50, cursor };
}

export async function getAuthorFeed(actor: string, limitOrOpts: number | FeedOptions = 30, cursor?: string): Promise<{ feed: FeedItem[]; cursor?: string }> {
	syncFromAtprotoSession();
	const { limit, cursor: normalizedCursor } = normalizeFeedOptions(limitOrOpts, cursor);

	if (actor.includes('malak.etzhayyim.com')) {
		try {
			const res = await fetch('http://localhost:8099/feed');
			if (res.ok) {
				const data = await res.json();
				return { feed: data };
			}
		} catch (e) {
			console.error("Local malak feed fetch failed", e);
		}
	}

	return atQuery<{ feed: FeedItem[]; cursor?: string }>('app.bsky.feed.getAuthorFeed', { actor, limit, cursor: normalizedCursor });
}

export const yoroGetAuthorFeed = getAuthorFeed;

export async function getTimeline(limitOrOpts: number | FeedOptions = 50, cursor?: string): Promise<{ feed: FeedItem[]; cursor?: string }> {
	syncFromAtprotoSession();
	const { limit, cursor: normalizedCursor } = normalizeFeedOptions(limitOrOpts, cursor);
	return atQuery<{ feed: FeedItem[]; cursor?: string }>('app.bsky.feed.getTimeline', { limit, cursor: normalizedCursor });
}

export const yoroGetTimeline = getTimeline;

export async function getDiscoverFeed(limitOrOpts: number | FeedOptions = 50, cursor?: string): Promise<{ feed: FeedItem[]; cursor?: string }> {
	syncFromAtprotoSession();
	const { limit, cursor: normalizedCursor } = normalizeFeedOptions(limitOrOpts, cursor);
	return atQuery<{ feed: FeedItem[]; cursor?: string }>('app.bsky.feed.getDiscoverFeed', { limit, cursor: normalizedCursor });
}

export const yoroGetDiscoverFeed = getDiscoverFeed;

export async function getFeed(feed: string, limitOrOpts: number | FeedOptions = 50, cursor?: string): Promise<{ feed: FeedItem[]; cursor?: string }> {
	syncFromAtprotoSession();
	const { limit, cursor: normalizedCursor } = normalizeFeedOptions(limitOrOpts, cursor);
	return atQuery<{ feed: FeedItem[]; cursor?: string }>('app.bsky.feed.getFeed', { feed, limit, cursor: normalizedCursor });
}

export async function getFeedGenerator(feed: string): Promise<FeedGeneratorView> {
	syncFromAtprotoSession();
	const data = await atQuery<{ view: FeedGeneratorView }>('app.bsky.feed.getFeedGenerator', { feed });
	return data.view as FeedGeneratorView;
}

export async function getSuggestedFeeds(limitOrOpts: number | FeedOptions = 20, cursor?: string) {
	syncFromAtprotoSession();
	const { limit, cursor: normalizedCursor } = normalizeFeedOptions(limitOrOpts, cursor);
	return atQuery('app.bsky.feed.getSuggestedFeeds', { limit, cursor: normalizedCursor });
}

export async function getPostThread(uri: string, depth = 6, parentHeight = 80) {
	syncFromAtprotoSession();
	return atQuery('app.bsky.feed.getPostThread', { uri, depth, parentHeight });
}

export const getThread = getPostThread;

function rkeyFromAtUri(uri: string): string {
	const rkey = uri.split('/').pop();
	if (!rkey) throw new Error(`Invalid AT URI: ${uri}`);
	return rkey;
}

export async function followUser(did: string): Promise<{ uri: string; cid: string }> {
	syncFromAtprotoSession();
	const repo = getCurrentDID();
	if (!repo) throw new Error('followUser: no session');
	return agent.app.bsky.graph.follow.create({ repo }, { subject: did, createdAt: new Date().toISOString() });
}

export async function unfollowUser(followUri: string): Promise<void> {
	syncFromAtprotoSession();
	const repo = getCurrentDID();
	if (!repo) throw new Error('unfollowUser: no session');
	await agent.app.bsky.graph.follow.delete({ repo, rkey: rkeyFromAtUri(followUri) });
}

export async function getFollows(actor: string, limitOrOpts: number | FeedOptions = 50, cursor?: string) {
	syncFromAtprotoSession();
	const { limit, cursor: normalizedCursor } = normalizeFeedOptions(limitOrOpts, cursor);
	return atQuery('app.bsky.graph.getFollows', { actor, limit, cursor: normalizedCursor });
}

export async function getFollowers(actor: string, limitOrOpts: number | FeedOptions = 50, cursor?: string) {
	syncFromAtprotoSession();
	const { limit, cursor: normalizedCursor } = normalizeFeedOptions(limitOrOpts, cursor);
	return atQuery('app.bsky.graph.getFollowers', { actor, limit, cursor: normalizedCursor });
}

export function likePost(uri: string, cid: string) {
	// Route through createRecord so it goes same-origin → kotoba-sw.js applies the
	// like as a member-signed local write (no atproto session required; the SW
	// holds the member identity). Falls through to the apex/AppView otherwise.
	return createRecord('app.bsky.feed.like', { subject: { uri, cid }, createdAt: new Date().toISOString() });
}

export async function unlikePost(likeUri: string): Promise<void> {
	const repo = getCurrentDID();
	if (!repo) throw new Error('unlikePost: no session');
	await agent.app.bsky.feed.like.delete({ repo, rkey: rkeyFromAtUri(likeUri) });
}

export function repost(uri: string, cid: string) {
	return createRecord('app.bsky.feed.repost', { subject: { uri, cid }, createdAt: new Date().toISOString() });
}

export async function unrepost(repostUri: string): Promise<void> {
	const repo = getCurrentDID();
	if (!repo) throw new Error('unrepost: no session');
	await agent.app.bsky.feed.repost.delete({ repo, rkey: rkeyFromAtUri(repostUri) });
}

export async function uploadBlob(data: Uint8Array | Blob, encoding?: string) {
	syncFromAtprotoSession();
	const res = await agent.com.atproto.repo.uploadBlob(data, { encoding });
	return res.data.blob;
}

export function uploadVideo(file: Blob, opts?: Record<string, unknown>) {
	return atProcedure('app.bsky.video.uploadVideo', { file, ...opts });
}

export function getVideoJobStatus(jobId: string) {
	return atQuery('app.bsky.video.getJobStatus', { jobId });
}

export async function setProfile(profile: Record<string, unknown>): Promise<void> {
	const repo = getCurrentDID();
	if (!repo) throw new Error('setProfile: no session');
	await agent.com.atproto.repo.putRecord({
		repo,
		collection: 'app.bsky.actor.profile',
		rkey: 'self',
		record: { $type: 'app.bsky.actor.profile', ...profile },
	});
}

export function createRecord(collection: string, record: Record<string, unknown>, repo = getCurrentDID()) {
	return atProcedure('com.atproto.repo.createRecord', { repo, collection, record });
}

export function listRecords(
	collectionOrRepo: string,
	repoOrCollection = getCurrentDID(),
	limitOrOptions: number | { limit?: number; cursor?: string } = 50,
	cursor?: string,
) {
	const oldOrder = repoOrCollection.includes('.');
	const collection = oldOrder ? repoOrCollection : collectionOrRepo;
	const repo = oldOrder ? collectionOrRepo : repoOrCollection;
	const limit = typeof limitOrOptions === 'number' ? limitOrOptions : (limitOrOptions.limit ?? 50);
	const nextCursor = typeof limitOrOptions === 'number' ? cursor : limitOrOptions.cursor;
	return atQuery('com.atproto.repo.listRecords', { repo, collection, limit, cursor: nextCursor });
}

export function deleteRecord(collection: string, rkey: string, repo = getCurrentDID()) {
	return atProcedure('com.atproto.repo.deleteRecord', { repo, collection, rkey });
}

const query = <T = unknown>(nsid: string, params?: Record<string, unknown>) => atQuery<T>(nsid, params);
const proc = <T = unknown>(nsid: string, body?: unknown, opts?: XrpcOptions) => atProcedure<T>(nsid, body, opts);

export const describeServer = () => query('com.atproto.server.describeServer');
export const getPreferences = () => query('app.bsky.actor.getPreferences');
export const getActorLikes = (actor: string, limit?: number, cursor?: string) => query('app.bsky.feed.getActorLikes', { actor, limit, cursor });
export const getLikes = (uri: string, cid?: string, limit?: number, cursor?: string) => query('app.bsky.feed.getLikes', { uri, cid, limit, cursor });
export const getQuotes = (uri: string, cid?: string, limit?: number, cursor?: string) => query('app.bsky.feed.getQuotes', { uri, cid, limit, cursor });
export const getRepostedBy = (uri: string, cid?: string, limit?: number, cursor?: string) => query('app.bsky.feed.getRepostedBy', { uri, cid, limit, cursor });
export const getKnownFollowers = (actor: string, limit?: number, cursor?: string) => query('app.bsky.graph.getKnownFollowers', { actor, limit, cursor });
export const getList = (list: string, limit?: number, cursor?: string) => query('app.bsky.graph.getList', { list, limit, cursor });
export const getLists = (actor: string, limit?: number, cursor?: string) => query('app.bsky.graph.getLists', { actor, limit, cursor });
export const getMutes = (limit?: number, cursor?: string) => query('app.bsky.graph.getMutes', { limit, cursor });
export const getStarterPack = (starterPack: string) => query('app.bsky.graph.getStarterPack', { starterPack });
export const muteActor = (actor: string) => proc('app.bsky.graph.muteActor', { actor });
export const unmuteActor = (actor: string) => proc('app.bsky.graph.unmuteActor', { actor });
export const blockActor = (actor: string) => proc('app.bsky.graph.blockActor', { actor });
export const unblockActor = (actor: string) => proc('app.bsky.graph.unblockActor', { actor });
export const reportContent = (body: Record<string, unknown>) => proc('com.atproto.moderation.createReport', body);
export const createBookmark = (uri: string, cid?: string) => proc('app.bsky.bookmark.createBookmark', { uri, cid });
export const deleteBookmark = (uri: string) => proc('app.bsky.bookmark.deleteBookmark', { uri });
export const createPost = (record: Record<string, unknown>) => createRecord('app.bsky.feed.post', { createdAt: new Date().toISOString(), ...record });
export const sendInteractions = (interactions: unknown[]) => proc('app.bsky.feed.sendInteractions', { interactions });
export const muteThread = (root: string) => proc('app.bsky.graph.muteThread', { root });
export const unmuteThread = (root: string) => proc('app.bsky.graph.unmuteThread', { root });
export const setThreadgate = (post: string, rules: unknown[]) => proc('app.bsky.feed.postgate', { post, rules });
export const removeThreadgate = (post: string) => proc('app.bsky.feed.removeThreadgate', { post });

export const listAppPasswords = () => query('com.atproto.server.listAppPasswords');
export const createAppPassword = (name: string) => proc('com.atproto.server.createAppPassword', { name });
export const revokeAppPassword = (name: string) => proc('com.atproto.server.revokeAppPassword', { name });

export const createConvo = (body: Record<string, unknown>) => proc('chat.bsky.convo.createConvo', body);
export async function createProjectConvo(body: Record<string, unknown> | string): Promise<Record<string, any>> {
	const payload = typeof body === 'string'
		? {
			name: `Chat with ${formatDID(body)}`,
			kind: 'dm',
			members: [body],
		}
		: body;
	const res = await proc<Record<string, any>>('com.etzhayyim.projector.newProjectConvo', payload);
	if (res?.convoId && !res.convo) {
		return { ...res, convo: { convoId: res.convoId } };
	}
	return res;
}
export const sendProjectMessage = (convoId: string, text: string, extra?: Record<string, unknown>) => proc('com.etzhayyim.projector.sendProjectMessage', { convoId, text, ...extra });
export const listConvos = (params?: Record<string, unknown>) => query('chat.bsky.convo.listConvos', params);
export const getConvo = (convoId: string) => query('chat.bsky.convo.getConvo', { convoId });
export const updateConvo = (body: Record<string, unknown>) => proc('chat.bsky.convo.updateConvo', body);
export const archiveConvo = (convoId: string) => proc('chat.bsky.convo.leaveConvo', { convoId });
export const getConvoMessages = (convoId: string, limit?: number, cursor?: string) => query('chat.bsky.convo.getMessages', { convoId, limit, cursor });
export const listConvoMembers = (convoId: string) => query('chat.bsky.convo.getConvo', { convoId });
export const inviteConvoMember = (convoId: string, did: string) => proc('chat.bsky.convo.addMember', { convoId, did });
export const updateConvoMemberRole = (convoId: string, did: string, role: string) => proc('com.etzhayyim.convo.updateMemberRole', { convoId, did, role });
export const setConvoEncryption = (convoId: string, enabled: boolean) => proc('com.etzhayyim.convo.setEncryption', { convoId, enabled });
export const rotateGroupKey = (convoId: string) => proc('com.etzhayyim.convo.rotateGroupKey', { convoId });
export const getUnread = () => query('chat.bsky.convo.getUnreadCount');
export const listPresence = (dids?: string[]) => query('com.etzhayyim.presence.listPresence', { dids });
export const setupConvoPush = (body: Record<string, unknown>) => proc('com.etzhayyim.convo.setupPush', body);
export const unsubscribePush = (body: Record<string, unknown>) => proc('com.etzhayyim.convo.unsubscribePush', body);

export const listDevices = () => query('com.etzhayyim.signal.listDevices');
export const ensureDevice = (body?: Record<string, unknown>) => proc('com.etzhayyim.signal.ensureDevice', body);
export const revokeDevice = (deviceId: string) => proc('com.etzhayyim.signal.revokeDevice', { deviceId });
export const renameDevice = (deviceId: string, name: string) => proc('com.etzhayyim.signal.renameDevice', { deviceId, name });
export const replenishOtpks = (
	deviceIdOrBody?: string | Record<string, unknown>,
	keys?: number[][],
	keyIds?: number[],
) => proc('com.etzhayyim.signal.replenishOtpks',
	typeof deviceIdOrBody === 'string' ? { deviceId: deviceIdOrBody, keys, keyIds } : deviceIdOrBody,
);
export const ensureSignalIdentity = (did?: string, deviceId?: string) => proc('com.etzhayyim.signal.ensureIdentity', { did, deviceId });
export const hasIdentity = () => query('com.etzhayyim.signal.hasIdentity');
export const getIdentityFingerprint = (did: string) => query('com.etzhayyim.signal.getIdentityFingerprint', { did });
export const verifyIdentityKey = (did: string, fingerprint: string) => proc('com.etzhayyim.signal.verifyIdentityKey', { did, fingerprint });
export const resolveConsent = (body: Record<string, unknown>) => proc('com.etzhayyim.consent.resolveConsent', body);

export const sendCallOffer = (body: Record<string, unknown>) => proc('com.etzhayyim.call.sendOffer', body);
export const sendCallAnswer = (body: Record<string, unknown>) => proc('com.etzhayyim.call.sendAnswer', body);
export const sendCallICE = (body: Record<string, unknown>) => proc('com.etzhayyim.call.sendIce', body);
export const hangupCall = (body: Record<string, unknown>) => proc('com.etzhayyim.call.hangup', body);
export const getICEServers = () => query('com.etzhayyim.call.getIceServers');

export const blobUrl = (blob: { ref?: { $link?: string }; cid?: string } | string): string => {
	const cid = typeof blob === 'string' ? blob : (blob.ref?.$link ?? blob.cid ?? '');
	return cid ? `${service}/xrpc/com.atproto.sync.getBlob?did=${encodeURIComponent(getCurrentDID())}&cid=${encodeURIComponent(cid)}` : '';
};

export const decodePayload = (value: unknown) => value;
export const decodeAndDecryptPayload = async (value: unknown) => value;
export const decodeMessageBody = (envelope: Record<string, unknown>) => String(envelope.text ?? envelope.body ?? envelope.message ?? '');
export const isEncryptedVal = (value: unknown) => Boolean(value && typeof value === 'object' && 'encrypted' in value);
export const parseCardType = (value: unknown): CardType => String(value ?? '');
export const detectFacets = async () => [];
export const resolveFacetMentions = async () => [];

export function subscribeAtprotoStream(_handler?: (event: StreamEvent) => void): StreamConnection {
	return { close() {}, unsubscribe() {} };
}

export const fn = { atQuery, atProcedure };
