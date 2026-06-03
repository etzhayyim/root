import { describe, it, expect } from 'vitest';
import type {
	PostView, PostAuthor, PostEmbedView, FeedItem, FollowView,
	AuthorProfile, RichTextFacet, FacetFeature, NotificationView, NotificationReason,
	LabelView, SelfLabel, LabelValue,
	ThreadgateView, ThreadgateRule,
	MutedUser, BlockedUser,
	FeedGeneratorView, ListView, StarterPackView,
} from '$lib/atproto-agent';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const author: PostAuthor = {
	did: 'did:plc:alice',
	handle: 'alice.bsky.social',
	displayName: 'Alice',
	avatar: 'https://cdn.example.com/alice.png',
};

const ts = '2026-03-21T00:00:00Z';

// ─── PostAuthor ─────────────────────────────────────────────────────────────

describe('PostAuthor', () => {
	it('constructs with all fields', () => {
		const a: PostAuthor = { did: 'did:plc:bob', handle: 'bob.test', displayName: 'Bob', avatar: 'https://img/b.png' };
		expect(a.did).toBe('did:plc:bob');
		expect(a.handle).toBe('bob.test');
		expect(a.displayName).toBe('Bob');
		expect(a.avatar).toBe('https://img/b.png');
	});

	it('avatar is optional', () => {
		const a: PostAuthor = { did: 'did:plc:carol', handle: 'carol.test', displayName: 'Carol' };
		expect(a.avatar).toBeUndefined();
	});
});

// ─── PostView ───────────────────────────────────────────────────────────────────

describe('PostView', () => {
	it('constructs with all required fields', () => {
		const post: PostView = {
			uri: 'at://did:plc:alice/app.bsky.feed.post/tid1',
			cid: 'bafyabc',
			author,
			text: 'Hello world',
			likeCount: 5,
			repostCount: 2,
			replyCount: 1,
			quoteCount: 0,
			viewCount: 0,
			indexedAt: ts,
			rkey: 'tid1',
		};
		expect(post.uri).toBe('at://did:plc:alice/app.bsky.feed.post/tid1');
		expect(post.text).toBe('Hello world');
		expect(post.likeCount).toBe(5);
		expect(post.quoteCount).toBe(0);
	});

	it('supports reply ref', () => {
		const post: PostView = {
			uri: 'at://did:plc:alice/app.bsky.feed.post/tid2',
			cid: 'bafydef',
			author,
			text: 'This is a reply',
			reply: {
				root: { uri: 'at://did:plc:bob/app.bsky.feed.post/root1', cid: 'cidr' },
				parent: { uri: 'at://did:plc:bob/app.bsky.feed.post/parent1', cid: 'cidp' },
			},
			likeCount: 0, repostCount: 0, replyCount: 0, quoteCount: 0,
			indexedAt: ts, rkey: 'tid2',
		};
		expect(post.reply!.root.uri).toContain('root1');
		expect(post.reply!.parent.cid).toBe('cidp');
	});

	it('supports viewer states', () => {
		const post: PostView = {
			uri: 'at://did:plc:alice/app.bsky.feed.post/tid3',
			cid: 'bafyghi',
			author,
			text: 'Viewer test',
			likeCount: 10, repostCount: 3, replyCount: 0, quoteCount: 1,
			indexedAt: ts, rkey: 'tid3',
			viewerLike: 'at://did:plc:me/app.bsky.feed.like/l1',
			viewerRepost: 'at://did:plc:me/app.bsky.feed.repost/r1',
			viewerBookmarked: true,
			viewerReplyDisabled: false,
			viewerThreadMuted: true,
		};
		expect(post.viewerLike).toContain('like');
		expect(post.viewerRepost).toContain('repost');
		expect(post.viewerBookmarked).toBe(true);
		expect(post.viewerReplyDisabled).toBe(false);
		expect(post.viewerThreadMuted).toBe(true);
	});

	it('supports facets', () => {
		const post: PostView = {
			uri: 'at://did:plc:alice/app.bsky.feed.post/tid4',
			cid: 'bafyjkl',
			author,
			text: 'Hello @bob.test',
			facets: [{
				index: { byteStart: 6, byteEnd: 15 },
				features: [{ $type: 'app.bsky.richtext.facet#mention', did: 'did:plc:bob' }],
			}],
			likeCount: 0, repostCount: 0, replyCount: 0, quoteCount: 0,
			indexedAt: ts, rkey: 'tid4',
		};
		expect(post.facets).toHaveLength(1);
		expect(post.facets![0].index.byteStart).toBe(6);
	});

	it('supports labels', () => {
		const post: PostView = {
			uri: 'at://did:plc:alice/app.bsky.feed.post/tid5',
			cid: 'bafymno',
			author,
			text: 'Labeled post',
			labels: [{ src: 'did:plc:labeler', uri: 'at://did:plc:alice/app.bsky.feed.post/tid5', val: 'nsfw', cts: ts }],
			likeCount: 0, repostCount: 0, replyCount: 0, quoteCount: 0,
			indexedAt: ts, rkey: 'tid5',
		};
		expect(post.labels).toHaveLength(1);
		expect(post.labels![0].val).toBe('nsfw');
	});

	it('supports threadgate', () => {
		const post: PostView = {
			uri: 'at://did:plc:alice/app.bsky.feed.post/tid6',
			cid: 'bafypqr',
			author,
			text: 'Gated thread',
			threadgate: {
				post: 'at://did:plc:alice/app.bsky.feed.post/tid6',
				allow: [{ type: 'mentionRule' }, { type: 'followingRule' }],
				createdAt: ts,
			},
			likeCount: 0, repostCount: 0, replyCount: 0, quoteCount: 0,
			indexedAt: ts, rkey: 'tid6',
		};
		expect(post.threadgate!.allow).toHaveLength(2);
	});

	it('convoId is optional AT Protocol extension', () => {
		const post: PostView = {
			uri: 'at://did:plc:alice/app.bsky.feed.post/tid7',
			cid: 'bafystu',
			author,
			text: 'With convo',
			convoId: 'cvNews',
			likeCount: 0, repostCount: 0, replyCount: 0, quoteCount: 0,
			indexedAt: ts, rkey: 'tid7',
		};
		expect(post.convoId).toBe('cvNews');
	});
});

// ─── PostEmbedView ──────────────────────────────────────────────────────────────

describe('PostEmbedView', () => {
	it('type=images with multiple images', () => {
		const embed: PostEmbedView = {
			type: 'images',
			images: [
				{ thumb: 'https://img/t1.jpg', fullsize: 'https://img/f1.jpg', alt: 'Photo 1' },
				{ thumb: 'https://img/t2.jpg', fullsize: 'https://img/f2.jpg' },
			],
		};
		expect(embed.type).toBe('images');
		expect(embed.images).toHaveLength(2);
		expect(embed.images![0].alt).toBe('Photo 1');
		expect(embed.images![1].alt).toBeUndefined();
	});

	it('type=external with link card', () => {
		const embed: PostEmbedView = {
			type: 'external',
			external: { uri: 'https://example.com', title: 'Example', description: 'A site', thumb: 'https://img/thumb.jpg' },
		};
		expect(embed.type).toBe('external');
		expect(embed.external!.uri).toBe('https://example.com');
		expect(embed.external!.thumb).toBeDefined();
	});

	it('type=record (quote post)', () => {
		const embed: PostEmbedView = {
			type: 'record',
			record: { uri: 'at://did:plc:bob/app.bsky.feed.post/q1', cid: 'cidq1', text: 'Quoted text', author },
		};
		expect(embed.type).toBe('record');
		expect(embed.record!.text).toBe('Quoted text');
		expect(embed.record!.author!.did).toBe('did:plc:alice');
	});

	it('type=video', () => {
		const embed: PostEmbedView = { type: 'video' };
		expect(embed.type).toBe('video');
		expect(embed.images).toBeUndefined();
	});
});

// ─── FeedItem ───────────────────────────────────────────────────────────────

describe('FeedItem', () => {
	const basePost: PostView = {
		uri: 'at://did:plc:alice/app.bsky.feed.post/f1',
		cid: 'cidfi',
		author,
		text: 'Feed post',
		likeCount: 0, repostCount: 0, replyCount: 0, quoteCount: 0,
		indexedAt: ts, rkey: 'f1',
	};

	it('constructs without reason', () => {
		const item: FeedItem = { post: basePost };
		expect(item.post.text).toBe('Feed post');
		expect(item.reason).toBeUndefined();
	});

	it('constructs with repost reason', () => {
		const item: FeedItem = {
			post: basePost,
			reason: {
				type: 'repost',
				by: { did: 'did:plc:carol', handle: 'carol.test', displayName: 'Carol' },
				indexedAt: ts,
			},
		};
		expect(item.reason!.type).toBe('repost');
		expect(item.reason!.by.handle).toBe('carol.test');
		expect(item.reason!.indexedAt).toBe(ts);
	});
});

// ─── FollowView ─────────────────────────────────────────────────────────────────

describe('FollowView', () => {
	it('constructs with all fields', () => {
		const f: FollowView = {
			did: 'did:plc:dave',
			handle: 'dave.test',
			displayName: 'Dave',
			avatar: 'https://img/dave.png',
			followedAt: ts,
		};
		expect(f.did).toBe('did:plc:dave');
		expect(f.followedAt).toBe(ts);
	});

	it('avatar is optional', () => {
		const f: FollowView = { did: 'did:plc:eve', handle: 'eve.test', displayName: 'Eve', followedAt: ts };
		expect(f.avatar).toBeUndefined();
	});
});

// ─── AuthorProfile ──────────────────────────────────────────────────────────

describe('AuthorProfile', () => {
	it('constructs with required fields', () => {
		const p: AuthorProfile = {
			did: 'did:plc:alice',
			handle: 'alice.bsky.social',
			displayName: 'Alice',
			followersCount: 100,
			followsCount: 50,
			postsCount: 200,
		};
		expect(p.followersCount).toBe(100);
		expect(p.postsCount).toBe(200);
	});

	it('supports all viewer flags', () => {
		const p: AuthorProfile = {
			did: 'did:plc:bob',
			handle: 'bob.test',
			displayName: 'Bob',
			avatar: 'https://img/bob.png',
			description: 'I am Bob',
			followersCount: 500,
			followsCount: 200,
			postsCount: 1000,
			viewerFollowing: true,
			viewerFollowedBy: true,
			viewerMuted: false,
			viewerBlocked: undefined,
		};
		expect(p.viewerFollowing).toBe(true);
		expect(p.viewerFollowedBy).toBe(true);
		expect(p.viewerMuted).toBe(false);
		expect(p.viewerBlocked).toBeUndefined();
		expect(p.description).toBe('I am Bob');
	});

	it('supports viewerBlocked as AT URI string', () => {
		const p: AuthorProfile = {
			did: 'did:plc:carol',
			handle: 'carol.test',
			displayName: 'Carol',
			followersCount: 0, followsCount: 0, postsCount: 0,
			viewerBlocked: 'at://did:plc:me/app.bsky.graph.block/b1',
		};
		expect(p.viewerBlocked).toContain('block');
	});

	it('supports content labels', () => {
		const p: AuthorProfile = {
			did: 'did:plc:spam',
			handle: 'spam.test',
			displayName: 'Spam',
			followersCount: 0, followsCount: 0, postsCount: 0,
			labels: [{ src: 'did:plc:labeler', uri: 'at://did:plc:spam', val: '!warn', cts: ts }],
		};
		expect(p.labels).toHaveLength(1);
		expect(p.labels![0].val).toBe('!warn');
	});
});

// ─── RichTextFacet / FacetFeature ─────────────────────────────────────────────────

describe('RichTextFacet', () => {
	it('mention facet', () => {
		const f: RichTextFacet = {
			index: { byteStart: 0, byteEnd: 10 },
			features: [{ $type: 'app.bsky.richtext.facet#mention', did: 'did:plc:alice' }],
		};
		expect(f.features[0].$type).toBe('app.bsky.richtext.facet#mention');
		expect((f.features[0] as { did: string }).did).toBe('did:plc:alice');
	});

	it('link facet', () => {
		const f: RichTextFacet = {
			index: { byteStart: 5, byteEnd: 30 },
			features: [{ $type: 'app.bsky.richtext.facet#link', uri: 'https://example.com' }],
		};
		expect(f.features[0].$type).toBe('app.bsky.richtext.facet#link');
		expect((f.features[0] as { uri: string }).uri).toBe('https://example.com');
	});

	it('tag facet', () => {
		const f: RichTextFacet = {
			index: { byteStart: 0, byteEnd: 7 },
			features: [{ $type: 'app.bsky.richtext.facet#tag', tag: 'atproto' }],
		};
		expect(f.features[0].$type).toBe('app.bsky.richtext.facet#tag');
		expect((f.features[0] as { tag: string }).tag).toBe('atproto');
	});

	it('multiple features in one facet', () => {
		const f: RichTextFacet = {
			index: { byteStart: 0, byteEnd: 20 },
			features: [
				{ $type: 'app.bsky.richtext.facet#mention', did: 'did:plc:x' },
				{ $type: 'app.bsky.richtext.facet#tag', tag: 'test' },
			],
		};
		expect(f.features).toHaveLength(2);
	});
});

// ─── NotificationView ───────────────────────────────────────────────────────────

describe('NotificationView', () => {
	it('like notification', () => {
		const n: NotificationView = {
			uri: 'at://did:plc:bob/app.bsky.feed.like/l1',
			cid: 'cidl1',
			author,
			reason: 'like',
			reasonSubject: 'at://did:plc:me/app.bsky.feed.post/p1',
			record: {},
			isRead: false,
			indexedAt: ts,
		};
		expect(n.reason).toBe('like');
		expect(n.isRead).toBe(false);
	});

	it('repost notification', () => {
		const n: NotificationView = {
			uri: 'at://did:plc:bob/app.bsky.feed.repost/r1',
			cid: 'cidr1',
			author,
			reason: 'repost',
			reasonSubject: 'at://did:plc:me/app.bsky.feed.post/p2',
			record: {},
			isRead: true,
			indexedAt: ts,
		};
		expect(n.reason).toBe('repost');
		expect(n.isRead).toBe(true);
	});

	it('follow notification', () => {
		const n: NotificationView = {
			uri: 'at://did:plc:carol/app.bsky.graph.follow/f1',
			cid: 'cidf1',
			author: { did: 'did:plc:carol', handle: 'carol.test', displayName: 'Carol' },
			reason: 'follow',
			record: {},
			isRead: false,
			indexedAt: ts,
		};
		expect(n.reason).toBe('follow');
		expect(n.reasonSubject).toBeUndefined();
	});

	it('mention notification', () => {
		const n: NotificationView = {
			uri: 'at://did:plc:bob/app.bsky.feed.post/m1',
			cid: 'cidm1',
			author,
			reason: 'mention',
			record: { text: 'Hey @me' },
			isRead: false,
			indexedAt: ts,
		};
		expect(n.reason).toBe('mention');
	});

	it('reply notification', () => {
		const n: NotificationView = {
			uri: 'at://did:plc:bob/app.bsky.feed.post/rp1',
			cid: 'cidrp1',
			author,
			reason: 'reply',
			reasonSubject: 'at://did:plc:me/app.bsky.feed.post/p3',
			record: { text: 'Great post!' },
			isRead: true,
			indexedAt: ts,
		};
		expect(n.reason).toBe('reply');
	});

	it('quote notification', () => {
		const n: NotificationView = {
			uri: 'at://did:plc:bob/app.bsky.feed.post/q1',
			cid: 'cidq1',
			author,
			reason: 'quote',
			reasonSubject: 'at://did:plc:me/app.bsky.feed.post/p4',
			record: {},
			isRead: false,
			indexedAt: ts,
		};
		expect(n.reason).toBe('quote');
	});

	it('all 6 reason types are valid', () => {
		const reasons: NotificationReason[] = ['like', 'repost', 'follow', 'mention', 'reply', 'quote'];
		expect(reasons).toHaveLength(6);
	});
});

// ─── LabelView / SelfLabel / LabelValue ───────────────────────────────────────

describe('LabelView', () => {
	it('constructs with required fields', () => {
		const l: LabelView = {
			src: 'did:plc:labeler',
			uri: 'at://did:plc:alice/app.bsky.feed.post/p1',
			val: 'nsfw',
			cts: ts,
		};
		expect(l.src).toBe('did:plc:labeler');
		expect(l.val).toBe('nsfw');
	});

	it('supports optional cid and neg', () => {
		const l: LabelView = {
			src: 'did:plc:labeler',
			uri: 'at://did:plc:alice/app.bsky.feed.post/p2',
			cid: 'bafylabel',
			val: 'gore',
			neg: true,
			cts: ts,
		};
		expect(l.cid).toBe('bafylabel');
		expect(l.neg).toBe(true);
	});
});

describe('SelfLabel', () => {
	it('constructs with val only', () => {
		const sl: SelfLabel = { val: 'nsfw' };
		expect(sl.val).toBe('nsfw');
	});

	it('accepts any string value', () => {
		const sl: SelfLabel = { val: 'spoiler' };
		expect(sl.val).toBe('spoiler');
	});
});

describe('LabelValue', () => {
	it('covers all known label values', () => {
		const values: LabelValue[] = [
			'nsfw', 'nudity', 'porn', 'sexual',
			'gore', 'graphic-media',
			'spoiler',
			'!warn', '!hide', '!no-unauthenticated',
		];
		expect(values).toHaveLength(10);
	});
});

// ─── ThreadgateView / ThreadgateRule ───────────────────────────────────────────

describe('ThreadgateView', () => {
	it('constructs with empty allow (nobody can reply)', () => {
		const tg: ThreadgateView = {
			post: 'at://did:plc:alice/app.bsky.feed.post/p1',
			allow: [],
			createdAt: ts,
		};
		expect(tg.allow).toHaveLength(0);
	});

	it('mentionRule allows mentioned users', () => {
		const rule: ThreadgateRule = { type: 'mentionRule' };
		const tg: ThreadgateView = {
			post: 'at://did:plc:alice/app.bsky.feed.post/p2',
			allow: [rule],
			createdAt: ts,
		};
		expect(tg.allow[0].type).toBe('mentionRule');
	});

	it('followingRule allows followed users', () => {
		const rule: ThreadgateRule = { type: 'followingRule' };
		expect(rule.type).toBe('followingRule');
	});

	it('listRule references a list URI', () => {
		const rule: ThreadgateRule = { type: 'listRule', list: 'at://did:plc:alice/app.bsky.graph.list/trusted' };
		expect(rule.type).toBe('listRule');
		expect((rule as { list: string }).list).toContain('trusted');
	});

	it('combines multiple rules', () => {
		const tg: ThreadgateView = {
			post: 'at://did:plc:alice/app.bsky.feed.post/p3',
			allow: [
				{ type: 'mentionRule' },
				{ type: 'followingRule' },
				{ type: 'listRule', list: 'at://did:plc:alice/app.bsky.graph.list/vip' },
			],
			createdAt: ts,
		};
		expect(tg.allow).toHaveLength(3);
	});
});

// ─── MutedUser ──────────────────────────────────────────────────────────────

describe('MutedUser', () => {
	it('constructs with all fields', () => {
		const m: MutedUser = {
			did: 'did:plc:spammer',
			handle: 'spammer.test',
			displayName: 'Spammer',
			avatar: 'https://img/spam.png',
			mutedAt: ts,
		};
		expect(m.did).toBe('did:plc:spammer');
		expect(m.mutedAt).toBe(ts);
	});

	it('avatar is optional', () => {
		const m: MutedUser = { did: 'did:plc:x', handle: 'x.test', displayName: 'X', mutedAt: ts };
		expect(m.avatar).toBeUndefined();
	});
});

// ─── BlockedUser ────────────────────────────────────────────────────────────

describe('BlockedUser', () => {
	it('constructs with all fields', () => {
		const b: BlockedUser = {
			did: 'did:plc:troll',
			handle: 'troll.test',
			displayName: 'Troll',
			avatar: 'https://img/troll.png',
			blockedAt: ts,
		};
		expect(b.did).toBe('did:plc:troll');
		expect(b.blockedAt).toBe(ts);
	});

	it('avatar is optional', () => {
		const b: BlockedUser = { did: 'did:plc:y', handle: 'y.test', displayName: 'Y', blockedAt: ts };
		expect(b.avatar).toBeUndefined();
	});
});

// ─── FeedGeneratorView ──────────────────────────────────────────────────────

describe('FeedGeneratorView', () => {
	it('constructs with all required fields', () => {
		const fg: FeedGeneratorView = {
			uri: 'at://did:plc:alice/app.bsky.feed.generator/timeline',
			cid: 'cidfg1',
			did: 'did:plc:feedgen',
			creator: author,
			displayName: 'Timeline',
			indexedAt: ts,
		};
		expect(fg.uri).toContain('generator');
		expect(fg.displayName).toBe('Timeline');
	});

	it('supports optional fields', () => {
		const fg: FeedGeneratorView = {
			uri: 'at://did:plc:alice/app.bsky.feed.generator/popular',
			cid: 'cidfg2',
			did: 'did:plc:feedgen',
			creator: author,
			displayName: 'Popular',
			description: 'Most popular posts',
			avatar: 'https://img/feed.png',
			likeCount: 1234,
			indexedAt: ts,
		};
		expect(fg.description).toBe('Most popular posts');
		expect(fg.likeCount).toBe(1234);
		expect(fg.avatar).toBeDefined();
	});
});

// ─── ListView ───────────────────────────────────────────────────────────────

describe('ListView', () => {
	it('curatelist purpose', () => {
		const lv: ListView = {
			uri: 'at://did:plc:alice/app.bsky.graph.list/favorites',
			cid: 'cidlv1',
			creator: author,
			name: 'Favorites',
			purpose: 'curatelist',
			indexedAt: ts,
		};
		expect(lv.purpose).toBe('curatelist');
		expect(lv.name).toBe('Favorites');
	});

	it('modlist purpose', () => {
		const lv: ListView = {
			uri: 'at://did:plc:alice/app.bsky.graph.list/blocklist',
			cid: 'cidlv2',
			creator: author,
			name: 'Block List',
			purpose: 'modlist',
			description: 'Users to mute/block',
			listItemCount: 42,
			indexedAt: ts,
		};
		expect(lv.purpose).toBe('modlist');
		expect(lv.listItemCount).toBe(42);
	});

	it('referencelist purpose', () => {
		const lv: ListView = {
			uri: 'at://did:plc:alice/app.bsky.graph.list/refs',
			cid: 'cidlv3',
			creator: author,
			name: 'References',
			purpose: 'referencelist',
			indexedAt: ts,
		};
		expect(lv.purpose).toBe('referencelist');
	});

	it('supports viewer muted and blocked', () => {
		const lv: ListView = {
			uri: 'at://did:plc:alice/app.bsky.graph.list/mod1',
			cid: 'cidlv4',
			creator: author,
			name: 'Mod List',
			purpose: 'modlist',
			indexedAt: ts,
			viewerMuted: true,
			viewerBlocked: 'at://did:plc:me/app.bsky.graph.listblock/lb1',
		};
		expect(lv.viewerMuted).toBe(true);
		expect(lv.viewerBlocked).toContain('listblock');
	});
});

// ─── StarterPackView ────────────────────────────────────────────────────────

describe('StarterPackView', () => {
	it('constructs with required fields', () => {
		const sp: StarterPackView = {
			uri: 'at://did:plc:alice/app.bsky.graph.starterpack/sp1',
			cid: 'cidsp1',
			creator: author,
			name: 'Welcome Pack',
			indexedAt: ts,
		};
		expect(sp.name).toBe('Welcome Pack');
		expect(sp.uri).toContain('starterpack');
	});

	it('supports all optional fields', () => {
		const sp: StarterPackView = {
			uri: 'at://did:plc:alice/app.bsky.graph.starterpack/sp2',
			cid: 'cidsp2',
			creator: author,
			name: 'Dev Pack',
			description: 'Starter pack for developers',
			list: 'at://did:plc:alice/app.bsky.graph.list/devs',
			listItemCount: 25,
			joinedWeekCount: 10,
			joinedAllTimeCount: 500,
			indexedAt: ts,
		};
		expect(sp.description).toBe('Starter pack for developers');
		expect(sp.listItemCount).toBe(25);
		expect(sp.joinedWeekCount).toBe(10);
		expect(sp.joinedAllTimeCount).toBe(500);
		expect(sp.list).toContain('devs');
	});
});
