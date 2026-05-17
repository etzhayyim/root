/**
 * Native sponsored posts: fetch candidates, rank per viewer, merge into feed.
 *
 * Federation model: Option A — each sponsored item is a regular
 * `app.bsky.feed.post` from an ad-account DID, self-labeled `!ad`. It flows
 * through the normal firehose, and other AppViews can filter via labelers.
 *
 * Ranker is intentionally dumb (client-side heuristic). An AppView-side
 * auction / ML ranker is a future follow-up; see advectors project.
 *
 * ADR: 90-docs/adr/0039-yoro-ads-integration.md §Sponsored Feed
 */
import { getAuthorFeed } from '$lib/atproto-agent';
import type { FeedItem, PostView } from '$lib/atproto-agent';
import { SPONSORED_DIDS, SPONSORED_RANK, SPONSORED_LABEL } from './config';

export interface SponsoredContext {
	/** Viewer's followed DIDs (for affinity scoring). */
	followedDids: Set<string>;
	/** Viewer's recently liked post authors (secondary signal). */
	recentLikedAuthors: Set<string>;
}

/** Fetch the latest `!ad`-labeled post from each SPONSORED_DID. */
export async function loadSponsoredCandidates(): Promise<PostView[]> {
	if (SPONSORED_DIDS.length === 0) return [];
	const results = await Promise.all(
		SPONSORED_DIDS.map((did) =>
			getAuthorFeed(did, { limit: 3 })
				.then((r: { feed: FeedItem[] }) => r.feed.map((f) => f.post).filter(hasAdLabel))
				.catch((_err) => [] as PostView[]),
		),
	);
	// One candidate per advertiser (freshest).
	return results.map((posts) => posts[0]).filter((p): p is PostView => !!p);
}

function hasAdLabel(post: PostView): boolean {
	return (post.labels ?? []).some((l: any) => l?.val === SPONSORED_LABEL);
}

/** Score a candidate post for this viewer. Returns 0..1. */
export function scoreCandidate(post: PostView, ctx: SponsoredContext): number {
	let score = 0;

	// Affinity: viewer follows the advertiser OR overlaps on liked-authors.
	if (ctx.followedDids.has(post.author.did)) score += 0.5;
	if (ctx.recentLikedAuthors.has(post.author.did)) score += 0.2;

	// Recency decay (exponential half-life).
	const ageH = (Date.now() - new Date(post.indexedAt).getTime()) / 3_600_000;
	const recency = Math.pow(0.5, ageH / SPONSORED_RANK.recencyHalfLifeHours);
	score += 0.3 * recency;

	return Math.min(1, score);
}

/** Session impression cap (sessionStorage). */
function sessionImpressions(): number {
	if (typeof window === 'undefined') return 0;
	return Number(sessionStorage.getItem(SPONSORED_RANK.sessionKey) ?? '0');
}
function bumpImpressions(n: number) {
	if (typeof window === 'undefined') return;
	sessionStorage.setItem(SPONSORED_RANK.sessionKey, String(sessionImpressions() + n));
}

/**
 * Merge sponsored candidates into an organic feed. Returns the new feed and
 * the set of post URIs that are sponsored (caller uses this to render the
 * Sponsored pill in the existing post UI — no new component needed).
 */
export function mergeSponsored(
	organic: FeedItem[],
	candidates: PostView[],
	ctx: SponsoredContext,
): { feed: FeedItem[]; sponsoredUris: Set<string> } {
	const sponsoredUris = new Set<string>();
	if (candidates.length === 0 || organic.length === 0) {
		return { feed: organic, sponsoredUris };
	}

	const remainingBudget = Math.max(0, SPONSORED_RANK.sessionCap - sessionImpressions());
	if (remainingBudget === 0) return { feed: organic, sponsoredUris };

	// Rank, drop below threshold, keep only as many as the budget allows.
	const ranked = candidates
		.map((post) => ({ post, score: scoreCandidate(post, ctx) }))
		.filter((c) => c.score >= SPONSORED_RANK.minScore)
		.sort((a, b) => b.score - a.score)
		.slice(0, remainingBudget);
	if (ranked.length === 0) return { feed: organic, sponsoredUris };

	// Insert one sponsored at every `frequency` boundary after the first 2 organic.
	const feed: FeedItem[] = [];
	let nextInsertAt = SPONSORED_RANK.frequency;
	let rankedIdx = 0;
	for (let i = 0; i < organic.length; i++) {
		feed.push(organic[i]);
		if (i + 1 === nextInsertAt && rankedIdx < ranked.length) {
			const { post } = ranked[rankedIdx++];
			feed.push({ post });
			sponsoredUris.add(post.uri);
			nextInsertAt += SPONSORED_RANK.frequency;
		}
	}

	bumpImpressions(sponsoredUris.size);
	return { feed, sponsoredUris };
}
