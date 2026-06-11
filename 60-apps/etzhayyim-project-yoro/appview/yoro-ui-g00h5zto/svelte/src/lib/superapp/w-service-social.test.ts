import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('$lib/atproto-agent', () => ({
	getSession: vi.fn().mockReturnValue(null),
	memberLabel: vi.fn((d: string) => d.slice(0, 12)),
	isDid: vi.fn((s: string) => s.startsWith('did:plc:') || s.startsWith('did:web:')),
	resolveHandle: vi.fn().mockResolvedValue('did:plc:resolved'),
	getCurrentDID: vi.fn().mockResolvedValue('did:plc:self'),
	formatDID: vi.fn((d: string) => d),
	atQuery: vi.fn().mockResolvedValue({}),
	atProcedure: vi.fn().mockResolvedValue({}),
}));

import { atProcedure, atQuery } from '$lib/atproto-agent';
import {
	// Social Graph
	getTimeline, getAuthorFeed, getPostThread, createPost,
	likePost, unlikePost, repost, unrepost,
	followUser, unfollowUser, getFollowers, getFollows,
	getAuthorProfile,
	// Feed detail
	getPosts, getLikes, getRepostedBy, getQuotes, getActorLikes,
	getListFeed, getFeed, getFeedGenerator, getFeedGenerators,
	getSuggestedFeeds, getActorFeeds, sendInteractions,
	// Actor
	getProfiles, getSuggestions, searchActors, searchActorsTypeahead,
	getPreferences, putPreferences,
	// Graph
	getRelationships, getKnownFollowers, getSuggestedFollowsByActor,
	getList, getLists, muteActorList, unmuteActorList,
	// Moderation
	muteActor, unmuteActor, blockActor, unblockActor,
	getMutes, getBlocks,
	muteThread, unmuteThread,
	setThreadgate, removeThreadgate, reportContent,
	// Bookmark / Draft / Video
	createBookmark, deleteBookmark, getBookmarks,
	createDraft, updateDraft, deleteDraft, getDrafts,
	getVideoUploadLimits, getVideoJobStatus,
	getRecord, listRecords, queryLabels,
	// Notifications
	listNotifications, getNotificationCount, updateNotificationSeen,
	// Sync
	syncGetLatestCommit, syncGetRepoStatus, syncListRepos,
	// Ozone
	ozoneListTemplates, ozoneQueryStatuses, ozoneTeamListMembers,
	// Helpers
	decodeMessageBody, isEncrypted, blobUrl,
} from '$lib/atproto-agent';

const mockAtProcedure = atProcedure as ReturnType<typeof vi.fn>;
const mockAtQuery = atQuery as ReturnType<typeof vi.fn>;

beforeEach(() => {
	vi.clearAllMocks();
});

// ─── 1. Social Graph (13 tests) ──────────────────────────────────────────────

describe('Social Graph', () => {
	it('getTimeline calls atProcedure with app.bsky.feed.getTimeline', async () => {
		mockAtProcedure.mockResolvedValueOnce({ feed: [{ post: { uri: 'at://x' } }], cursor: 'c1' });
		const res = await getTimeline({ limit: 10, cursor: 'abc' });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getTimeline', { limit: 10, cursor: 'abc' });
		expect(res.feed).toHaveLength(1);
	});

	it('getTimeline uses default limit of 50', async () => {
		mockAtProcedure.mockResolvedValueOnce({ feed: [{ post: { uri: 'at://x' } }] });
		await getTimeline();
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getTimeline', { limit: 50, cursor: undefined });
	});

	it('getAuthorFeed calls atProcedure with app.bsky.feed.getAuthorFeed', async () => {
		mockAtProcedure.mockResolvedValueOnce({ feed: [{ post: { uri: 'at://x' } }] });
		const res = await getAuthorFeed('did:plc:alice', { limit: 20 });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getAuthorFeed', { actor: 'did:plc:alice', limit: 20, cursor: undefined });
		expect(res.feed).toHaveLength(1);
	});

	it('getPostThread calls atProcedure with app.bsky.feed.getPostThread', async () => {
		mockAtProcedure.mockResolvedValueOnce({ thread: { post: { uri: 'at://x/post/rk1' }, replies: [] } });
		const res = await getPostThread('at://x/post/rk1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getPostThread', { uri: 'at://x/post/rk1', depth: 6, parentHeight: 80 });
		expect(res.thread.post.uri).toBe('at://x/post/rk1');
	});

	it('createPost calls atProcedure with com.atproto.repo.createRecord', async () => {
		mockAtProcedure.mockResolvedValueOnce({ uri: 'at://did:plc:self/app.bsky.feed.post/rk1', cid: 'cid1' });
		await createPost('Hello world');
		expect(mockAtProcedure).toHaveBeenCalledWith('com.atproto.repo.createRecord', expect.objectContaining({
			collection: 'app.bsky.feed.post',
			record: expect.objectContaining({
				$type: 'app.bsky.feed.post',
				text: 'Hello world',
			}),
		}));
	});

	it('likePost calls atProcedure with app.bsky.feed.like', async () => {
		await likePost('at://did:plc:x/post/rk1', 'cid123');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.like', { subject: { uri: 'at://did:plc:x/post/rk1', cid: 'cid123' } });
	});

	it('unlikePost calls atProcedure with app.bsky.feed.unlike', async () => {
		await unlikePost('at://did:plc:x/post/rk1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.unlike', { uri: 'at://did:plc:x/post/rk1' });
	});

	it('repost calls atProcedure with app.bsky.feed.repost', async () => {
		await repost('at://did:plc:x/post/rk1', 'cid456');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.repost', { subject: { uri: 'at://did:plc:x/post/rk1', cid: 'cid456' } });
	});

	it('unrepost calls atProcedure with app.bsky.feed.unrepost', async () => {
		await unrepost('at://did:plc:x/post/rk1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.unrepost', { uri: 'at://did:plc:x/post/rk1' });
	});

	it('followUser calls atProcedure with app.bsky.graph.follow', async () => {
		await followUser('did:plc:alice');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.follow', { subject: 'did:plc:alice' });
	});

	it('unfollowUser calls atProcedure with app.bsky.graph.unfollow', async () => {
		await unfollowUser('did:plc:alice');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.unfollow', { did: 'did:plc:alice' });
	});

	it('getFollowers calls atProcedure with app.bsky.graph.getFollowers', async () => {
		mockAtProcedure.mockResolvedValueOnce({ followers: [], cursor: 'next' });
		await getFollowers('did:plc:alice', { limit: 25, cursor: 'c1' });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.getFollowers', { actor: 'did:plc:alice', limit: 25, cursor: 'c1' });
	});

	it('getFollows calls atProcedure with app.bsky.graph.getFollows', async () => {
		mockAtProcedure.mockResolvedValueOnce({ follows: [], cursor: 'next' });
		await getFollows('did:plc:bob', { limit: 30 });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.getFollows', { actor: 'did:plc:bob', limit: 30, cursor: undefined });
	});

	it('getAuthorProfile calls atQuery with app.bsky.actor.getProfile', async () => {
		mockAtQuery.mockResolvedValueOnce({
			did: 'did:plc:alice', handle: 'alice.bsky.social', displayName: 'Alice',
			followersCount: 100, followsCount: 50, postsCount: 200,
		});
		const res = await getAuthorProfile('did:plc:alice');
		expect(mockAtQuery).toHaveBeenCalledWith('app.bsky.actor.getProfile', { actor: 'did:plc:alice' });
		expect(res.displayName).toBe('Alice');
	});
});

// ─── 2. Feed detail APIs (12 tests) ──────────────────────────────────────────

describe('Feed detail APIs', () => {
	it('getPosts calls atProcedure with app.bsky.feed.getPosts', async () => {
		mockAtProcedure.mockResolvedValueOnce({ posts: [] });
		await getPosts(['at://did:plc:x/post/1', 'at://did:plc:x/post/2']);
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getPosts', { uris: ['at://did:plc:x/post/1', 'at://did:plc:x/post/2'] });
	});

	it('getLikes calls atProcedure with app.bsky.feed.getLikes', async () => {
		mockAtProcedure.mockResolvedValueOnce({ uri: 'at://x', likes: [], cursor: 'c' });
		await getLikes('at://did:plc:x/post/1', { limit: 20, cursor: 'abc' });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getLikes', { uri: 'at://did:plc:x/post/1', cid: undefined, limit: 20, cursor: 'abc' });
	});

	it('getRepostedBy calls atProcedure with app.bsky.feed.getRepostedBy', async () => {
		mockAtProcedure.mockResolvedValueOnce({ uri: 'at://x', repostedBy: [] });
		await getRepostedBy('at://did:plc:x/post/1', { limit: 10 });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getRepostedBy', { uri: 'at://did:plc:x/post/1', cid: undefined, limit: 10, cursor: undefined });
	});

	it('getQuotes calls atProcedure with app.bsky.feed.getQuotes', async () => {
		mockAtProcedure.mockResolvedValueOnce({ uri: 'at://x', posts: [] });
		await getQuotes('at://did:plc:x/post/1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getQuotes', { uri: 'at://did:plc:x/post/1', cid: undefined, limit: 50, cursor: undefined });
	});

	it('getActorLikes calls atProcedure with app.bsky.feed.getActorLikes', async () => {
		mockAtProcedure.mockResolvedValueOnce({ feed: [] });
		await getActorLikes('did:plc:alice', { limit: 15 });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getActorLikes', { actor: 'did:plc:alice', limit: 15, cursor: undefined });
	});

	it('getListFeed calls atProcedure with app.bsky.feed.getListFeed', async () => {
		mockAtProcedure.mockResolvedValueOnce({ feed: [] });
		await getListFeed('at://did:plc:x/list/1', { limit: 25 });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getListFeed', { list: 'at://did:plc:x/list/1', limit: 25, cursor: undefined });
	});

	it('getFeed calls atProcedure with app.bsky.feed.getFeed', async () => {
		mockAtProcedure.mockResolvedValueOnce({ feed: [] });
		await getFeed('at://did:plc:x/feed/gen1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getFeed', { feed: 'at://did:plc:x/feed/gen1', limit: 50, cursor: undefined });
	});

	it('getFeedGenerator calls atProcedure with app.bsky.feed.getFeedGenerator', async () => {
		mockAtProcedure.mockResolvedValueOnce({ view: {}, isOnline: true, isValid: true });
		await getFeedGenerator('at://did:plc:x/feed/gen1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getFeedGenerator', { feed: 'at://did:plc:x/feed/gen1' });
	});

	it('getFeedGenerators calls atProcedure with app.bsky.feed.getFeedGenerators', async () => {
		mockAtProcedure.mockResolvedValueOnce({ feeds: [] });
		await getFeedGenerators(['at://did:plc:x/feed/gen1', 'at://did:plc:x/feed/gen2']);
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getFeedGenerators', { feeds: ['at://did:plc:x/feed/gen1', 'at://did:plc:x/feed/gen2'] });
	});

	it('getSuggestedFeeds calls atProcedure with app.bsky.feed.getSuggestedFeeds', async () => {
		mockAtProcedure.mockResolvedValueOnce({ feeds: [] });
		await getSuggestedFeeds({ limit: 10 });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getSuggestedFeeds', { limit: 10, cursor: undefined });
	});

	it('getActorFeeds calls atProcedure with app.bsky.feed.getActorFeeds', async () => {
		mockAtProcedure.mockResolvedValueOnce({ feeds: [] });
		await getActorFeeds('did:plc:alice');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.getActorFeeds', { actor: 'did:plc:alice', limit: 50, cursor: undefined });
	});

	it('sendInteractions calls atProcedure with app.bsky.feed.sendInteractions', async () => {
		const interactions = [
			{ uri: 'at://did:plc:x/post/1', event: 'like' as const },
			{ uri: 'at://did:plc:x/post/2', event: 'view' as const },
		];
		await sendInteractions(interactions);
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.sendInteractions', { interactions });
	});
});

// ─── 3. Actor APIs (6 tests) ─────────────────────────────────────────────────

describe('Actor APIs', () => {
	it('getProfiles calls atProcedure with app.bsky.actor.getProfiles', async () => {
		mockAtProcedure.mockResolvedValueOnce({ profiles: [] });
		await getProfiles(['did:plc:alice', 'did:plc:bob']);
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.actor.getProfiles', { actors: ['did:plc:alice', 'did:plc:bob'] });
	});

	it('getSuggestions calls atProcedure with app.bsky.actor.getSuggestions', async () => {
		mockAtProcedure.mockResolvedValueOnce({ actors: [] });
		await getSuggestions({ limit: 20 });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.actor.getSuggestions', { limit: 20, cursor: undefined });
	});

	it('searchActors calls atQuery with q/limit/cursor', async () => {
		mockAtQuery.mockResolvedValueOnce({ actors: [] });
		await searchActors('alice', { limit: 10, cursor: 'c1' });
		expect(mockAtQuery).toHaveBeenCalledWith('app.bsky.actor.searchActors', { q: 'alice', limit: 10, cursor: 'c1' });
	});

	it('searchActorsTypeahead calls atQuery with q/limit', async () => {
		mockAtQuery.mockResolvedValueOnce({ actors: [] });
		await searchActorsTypeahead('al', { limit: 5 });
		expect(mockAtQuery).toHaveBeenCalledWith('app.bsky.actor.searchActorsTypeahead', { q: 'al', limit: 5 });
	});

	it('getPreferences calls atProcedure with app.bsky.actor.getPreferences', async () => {
		mockAtProcedure.mockResolvedValueOnce({ preferences: [] });
		await getPreferences();
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.actor.getPreferences', {});
	});

	it('putPreferences calls atProcedure with app.bsky.actor.putPreferences', async () => {
		const prefs = [{ $type: 'app.bsky.actor.defs#savedFeedsPrefV2', items: [] }];
		await putPreferences(prefs);
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.actor.putPreferences', { preferences: prefs });
	});
});

// ─── 4. Graph APIs (7 tests) ─────────────────────────────────────────────────

describe('Graph APIs', () => {
	it('getRelationships calls atProcedure with app.bsky.graph.getRelationships', async () => {
		mockAtProcedure.mockResolvedValueOnce({ relationships: [] });
		await getRelationships('did:plc:alice', ['did:plc:bob']);
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.getRelationships', { actor: 'did:plc:alice', others: ['did:plc:bob'] });
	});

	it('getKnownFollowers calls atProcedure with app.bsky.graph.getKnownFollowers', async () => {
		mockAtProcedure.mockResolvedValueOnce({ subject: {}, followers: [] });
		await getKnownFollowers('did:plc:alice', { limit: 30 });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.getKnownFollowers', { actor: 'did:plc:alice', limit: 30, cursor: undefined });
	});

	it('getSuggestedFollowsByActor calls atProcedure', async () => {
		mockAtProcedure.mockResolvedValueOnce({ suggestions: [] });
		await getSuggestedFollowsByActor('did:plc:bob');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.getSuggestedFollowsByActor', { actor: 'did:plc:bob' });
	});

	it('getList calls atProcedure with app.bsky.graph.getList', async () => {
		mockAtProcedure.mockResolvedValueOnce({ list: {}, items: [] });
		await getList('at://did:plc:x/list/1', { limit: 20, cursor: 'c1' });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.getList', { list: 'at://did:plc:x/list/1', limit: 20, cursor: 'c1' });
	});

	it('getLists calls atProcedure with app.bsky.graph.getLists', async () => {
		mockAtProcedure.mockResolvedValueOnce({ lists: [] });
		await getLists('did:plc:alice');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.getLists', { actor: 'did:plc:alice', limit: 50, cursor: undefined });
	});

	it('muteActorList calls atProcedure with app.bsky.graph.muteActorList', async () => {
		await muteActorList('at://did:plc:x/list/1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.muteActorList', { list: 'at://did:plc:x/list/1' });
	});

	it('unmuteActorList calls atProcedure with app.bsky.graph.unmuteActorList', async () => {
		await unmuteActorList('at://did:plc:x/list/1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.unmuteActorList', { list: 'at://did:plc:x/list/1' });
	});
});

// ─── 5. Moderation (11 tests) ────────────────────────────────────────────────

describe('Moderation', () => {
	it('muteActor calls atProcedure with app.bsky.graph.muteActor', async () => {
		await muteActor('did:plc:spammer');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.muteActor', { actor: 'did:plc:spammer' });
	});

	it('unmuteActor calls atProcedure with app.bsky.graph.unmuteActor', async () => {
		await unmuteActor('did:plc:spammer');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.unmuteActor', { actor: 'did:plc:spammer' });
	});

	it('blockActor calls atProcedure with app.bsky.graph.block', async () => {
		await blockActor('did:plc:troll');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.block', { subject: 'did:plc:troll' });
	});

	it('unblockActor calls atProcedure with app.bsky.graph.unblock', async () => {
		await unblockActor('did:plc:troll');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.unblock', { subject: 'did:plc:troll' });
	});

	it('getMutes calls atProcedure with app.bsky.graph.getMutes', async () => {
		mockAtProcedure.mockResolvedValueOnce({ mutes: [] });
		await getMutes({ limit: 25, cursor: 'c1' });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.getMutes', { limit: 25, cursor: 'c1' });
	});

	it('getBlocks calls atProcedure with app.bsky.graph.getBlocks', async () => {
		mockAtProcedure.mockResolvedValueOnce({ blocks: [] });
		await getBlocks({ limit: 10 });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.getBlocks', { limit: 10, cursor: undefined });
	});

	it('muteThread calls atProcedure with app.bsky.graph.muteThread', async () => {
		await muteThread('at://did:plc:x/post/rk1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.muteThread', { root: 'at://did:plc:x/post/rk1' });
	});

	it('unmuteThread calls atProcedure with app.bsky.graph.unmuteThread', async () => {
		await unmuteThread('at://did:plc:x/post/rk1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.unmuteThread', { root: 'at://did:plc:x/post/rk1' });
	});

	it('setThreadgate calls atProcedure with app.bsky.feed.threadgate', async () => {
		const rules = [{ type: 'mentionRule' as const }, { type: 'followingRule' as const }];
		await setThreadgate('at://did:plc:x/post/rk1', rules);
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.threadgate', { post: 'at://did:plc:x/post/rk1', allow: rules });
	});

	it('removeThreadgate calls atProcedure with app.bsky.feed.removeThreadgate', async () => {
		await removeThreadgate('at://did:plc:x/post/rk1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.feed.removeThreadgate', { post: 'at://did:plc:x/post/rk1' });
	});

	it('reportContent calls atProcedure with com.atproto.moderation.createReport', async () => {
		await reportContent({
			reasonType: 'spam',
			reason: 'Spammy post',
			subject: { uri: 'at://did:plc:x/post/rk1', cid: 'cid123' },
		});
		expect(mockAtProcedure).toHaveBeenCalledWith('com.atproto.moderation.createReport', {
			reasonType: 'spam',
			reason: 'Spammy post',
			subject: { uri: 'at://did:plc:x/post/rk1', cid: 'cid123' },
		});
	});
});

// ─── 6. Bookmark / Draft / Video (10 tests) ──────────────────────────────────

describe('Bookmark / Draft / Video', () => {
	it('createBookmark calls atProcedure with app.bsky.bookmark.createBookmark', async () => {
		await createBookmark('at://did:plc:x/post/rk1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.bookmark.createBookmark', { uri: 'at://did:plc:x/post/rk1' });
	});

	it('deleteBookmark calls atProcedure with app.bsky.bookmark.deleteBookmark', async () => {
		await deleteBookmark('at://did:plc:x/post/rk1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.bookmark.deleteBookmark', { uri: 'at://did:plc:x/post/rk1' });
	});

	it('getBookmarks calls atQuery with app.bsky.bookmark.getBookmarks', async () => {
		mockAtQuery.mockResolvedValueOnce({ posts: [] });
		await getBookmarks({ limit: 20, cursor: 'c1' });
		expect(mockAtQuery).toHaveBeenCalledWith('app.bsky.bookmark.getBookmarks', { limit: 20, cursor: 'c1' });
	});

	it('createDraft calls atProcedure with app.bsky.draft.createDraft', async () => {
		mockAtProcedure.mockResolvedValueOnce({ uri: 'at://did:plc:self/draft/1' });
		const res = await createDraft('Draft text', { replyTo: 'at://x/post/1' });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.draft.createDraft', { text: 'Draft text', replyTo: 'at://x/post/1', embed: undefined });
		expect(res.uri).toBe('at://did:plc:self/draft/1');
	});

	it('updateDraft calls atProcedure with app.bsky.draft.updateDraft', async () => {
		await updateDraft('at://did:plc:self/draft/1', 'Updated text');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.draft.updateDraft', { uri: 'at://did:plc:self/draft/1', text: 'Updated text', embed: undefined });
	});

	it('deleteDraft calls atProcedure with app.bsky.draft.deleteDraft', async () => {
		await deleteDraft('at://did:plc:self/draft/1');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.draft.deleteDraft', { uri: 'at://did:plc:self/draft/1' });
	});

	it('getDrafts calls atQuery with app.bsky.draft.getDrafts', async () => {
		mockAtQuery.mockResolvedValueOnce({ drafts: [] });
		await getDrafts();
		expect(mockAtQuery).toHaveBeenCalledWith('app.bsky.draft.getDrafts');
	});

	it('getVideoUploadLimits calls atQuery with app.bsky.video.getUploadLimits', async () => {
		mockAtQuery.mockResolvedValueOnce({ canUpload: true, remainingDailyVideos: 10 });
		const res = await getVideoUploadLimits();
		expect(mockAtQuery).toHaveBeenCalledWith('app.bsky.video.getUploadLimits');
		expect(res.canUpload).toBe(true);
	});

	it('getVideoJobStatus calls atQuery with app.bsky.video.getJobStatus', async () => {
		mockAtQuery.mockResolvedValueOnce({ jobId: 'j1', state: 'completed' });
		const res = await getVideoJobStatus('j1');
		expect(mockAtQuery).toHaveBeenCalledWith('app.bsky.video.getJobStatus', { jobId: 'j1' });
		expect(res.state).toBe('completed');
	});

	it('getRecord calls atQuery with com.atproto.repo.getRecord', async () => {
		mockAtQuery.mockResolvedValueOnce({ uri: 'at://x', cid: 'c1', value: {} });
		await getRecord('did:plc:x', 'app.bsky.feed.post', 'rk1');
		expect(mockAtQuery).toHaveBeenCalledWith('com.atproto.repo.getRecord', { repo: 'did:plc:x', collection: 'app.bsky.feed.post', rkey: 'rk1' });
	});
});

describe('listRecords and queryLabels', () => {
	it('listRecords calls atQuery with com.atproto.repo.listRecords', async () => {
		mockAtQuery.mockResolvedValueOnce({ records: [] });
		await listRecords('did:plc:x', 'app.bsky.feed.post', { limit: 30, cursor: 'c1' });
		expect(mockAtQuery).toHaveBeenCalledWith('com.atproto.repo.listRecords', { repo: 'did:plc:x', collection: 'app.bsky.feed.post', limit: 30, cursor: 'c1' });
	});

	it('queryLabels calls atQuery with com.atproto.label.queryLabels', async () => {
		mockAtQuery.mockResolvedValueOnce({ labels: [] });
		await queryLabels({ uriPatterns: ['at://did:plc:x/*'] });
		expect(mockAtQuery).toHaveBeenCalledWith('com.atproto.label.queryLabels', { uriPatterns: ['at://did:plc:x/*'] });
	});
});

// ─── 7. Notifications (3 tests) ──────────────────────────────────────────────

describe('Notifications', () => {
	it('listNotifications calls atProcedure with app.bsky.notification.listNotifications', async () => {
		mockAtProcedure.mockResolvedValueOnce({ notifications: [], cursor: 'c1' });
		await listNotifications({ limit: 20, cursor: 'abc', reasons: ['like', 'follow'] });
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.notification.listNotifications', { limit: 20, cursor: 'abc', reasons: ['like', 'follow'] });
	});

	it('getNotificationCount calls atProcedure with app.bsky.notification.getUnreadCount', async () => {
		mockAtProcedure.mockResolvedValueOnce({ count: 5 });
		const res = await getNotificationCount();
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.notification.getUnreadCount', {});
		expect(res.count).toBe(5);
	});

	it('updateNotificationSeen calls atProcedure with seenAt', async () => {
		await updateNotificationSeen('2026-01-01T00:00:00Z');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.notification.updateSeen', { seenAt: '2026-01-01T00:00:00Z' });
	});
});

// ─── 8. Sync APIs (3 tests) ──────────────────────────────────────────────────

describe('Sync APIs', () => {
	it('syncGetLatestCommit calls atQuery with com.atproto.sync.getLatestCommit', async () => {
		mockAtQuery.mockResolvedValueOnce({ cid: 'bafy...', rev: '1234' });
		const res = await syncGetLatestCommit('did:plc:alice');
		expect(mockAtQuery).toHaveBeenCalledWith('com.atproto.sync.getLatestCommit', { did: 'did:plc:alice' });
		expect(res.cid).toBe('bafy...');
	});

	it('syncGetRepoStatus calls atQuery with com.atproto.sync.getRepoStatus', async () => {
		mockAtQuery.mockResolvedValueOnce({ did: 'did:plc:alice', active: true });
		const res = await syncGetRepoStatus('did:plc:alice');
		expect(mockAtQuery).toHaveBeenCalledWith('com.atproto.sync.getRepoStatus', { did: 'did:plc:alice' });
		expect(res.active).toBe(true);
	});

	it('syncListRepos calls atQuery with com.atproto.sync.listRepos', async () => {
		mockAtQuery.mockResolvedValueOnce({ repos: [] });
		await syncListRepos({ limit: 100, cursor: 'c1' });
		expect(mockAtQuery).toHaveBeenCalledWith('com.atproto.sync.listRepos', { limit: 100, cursor: 'c1' });
	});
});

// ─── 9. Ozone APIs (3 tests) ─────────────────────────────────────────────────

describe('Ozone APIs', () => {
	it('ozoneListTemplates calls atQuery with tools.ozone.communication.listTemplates', async () => {
		mockAtQuery.mockResolvedValueOnce({ templates: [] });
		await ozoneListTemplates();
		expect(mockAtQuery).toHaveBeenCalledWith('tools.ozone.communication.listTemplates');
	});

	it('ozoneQueryStatuses calls atQuery with tools.ozone.moderation.queryStatuses', async () => {
		mockAtQuery.mockResolvedValueOnce({ subjectStatuses: [] });
		await ozoneQueryStatuses({ limit: 20, takendown: true });
		expect(mockAtQuery).toHaveBeenCalledWith('tools.ozone.moderation.queryStatuses', { limit: 20, takendown: true });
	});

	it('ozoneTeamListMembers calls atQuery with tools.ozone.team.listConvoMembers', async () => {
		mockAtQuery.mockResolvedValueOnce({ members: [] });
		await ozoneTeamListMembers({ limit: 25 });
		expect(mockAtQuery).toHaveBeenCalledWith('tools.ozone.team.listConvoMembers', { limit: 25, cursor: undefined });
	});
});

// ─── 10. Utility helpers (5 tests) ───────────────────────────────────────────

describe('Utility helpers', () => {
	it('decodeMessageBody decodes base64 text/plain', () => {
		const env = { payload: btoa('Hello'), contentType: 'text/plain' } as any;
		expect(decodeMessageBody(env)).toBe('Hello');
	});

	it('decodeMessageBody returns raw payload for non-text/plain', () => {
		const env = { payload: '{"key":"val"}', contentType: 'application/json' } as any;
		expect(decodeMessageBody(env)).toBe('{"key":"val"}');
	});

	it('isEncrypted returns true for non-plaintext encryption', () => {
		expect(isEncrypted({ encryption: 'signal' } as any)).toBe(true);
		expect(isEncrypted({ encryption: 'plaintext' } as any)).toBe(false);
	});

	it('blobUrl builds CDN path for non-URL refs', () => {
		expect(blobUrl('abc123')).toBe('/cdn/blob/abc123');
	});

	it('blobUrl returns HTTP URLs as-is', () => {
		expect(blobUrl('https://example.com/img.png')).toBe('https://example.com/img.png');
	});
});

// ─── 11. Edge cases (4 tests) ────────────────────────────────────────────────

describe('Edge cases', () => {
	it('updateNotificationSeen uses current ISO string when seenAt not provided', async () => {
		await updateNotificationSeen();
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.notification.updateSeen', expect.objectContaining({
			seenAt: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T/),
		}));
	});

	it('getFollowers uses default limit of 50', async () => {
		mockAtProcedure.mockResolvedValueOnce({ followers: [] });
		await getFollowers('did:plc:alice');
		expect(mockAtProcedure).toHaveBeenCalledWith('app.bsky.graph.getFollowers', { actor: 'did:plc:alice', limit: 50, cursor: undefined });
	});

	it('blobUrl returns empty string for empty ref', () => {
		expect(blobUrl('')).toBe('');
	});

	it('reportContent with did subject calls atProcedure', async () => {
		await reportContent({
			reasonType: 'violation',
			subject: { did: 'did:plc:badactor' },
		});
		expect(mockAtProcedure).toHaveBeenCalledWith('com.atproto.moderation.createReport', {
			reasonType: 'violation',
			subject: { did: 'did:plc:badactor' },
		});
	});
});
