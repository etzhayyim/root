/**
 * Yoro ad slot registry (single source of truth).
 *
 * Placements map to concrete AdSense ad unit slot IDs. When an ad unit is not
 * yet provisioned, set its id to the sentinel `UNPROVISIONED` — AdSlot will
 * render the house-ad fallback instead of requesting AdSense.
 *
 * Secondary networks (AdPushup, Media.net, Ezoic) wrap AdSense via header
 * bidding or contextual inventory; they are enabled per-network in `providers`
 * and do not require their own slot ids.
 *
 * ADR: 90-docs/adr/0039-yoro-ads-integration.md
 */
export const ADSENSE_CLIENT_ID = 'ca-pub-8017914559680125';

export const UNPROVISIONED = 'UNPROVISIONED';

/**
 * ExoClick publisher-side zone ids per placement.
 * Site: yoro.gftd.ai (ExoClick site id 1094566). Zones are banner (ad_type=2, media_type=2).
 * Provisioned 2026-04-20 via ExoClick API v2.
 */
export const EXOCLICK_ZONES: Partial<Record<AdPlacement, string>> = {
	'feed-inline':    '5905260', // 300x250
	'feed-top':       '5905262', // 728x90
	'post-detail':    '5905264', // 300x250
	'post-thread':    '5905266', // 300x250
	'profile-header': '5905268', // 728x90
	'search-results': '5905270', // 300x250
	'sidebar':        '5905272', // 160x600
};

export type AdPlacement =
	| 'feed-inline'      // vibes feed between posts
	| 'feed-top'         // above the first post (guest / cold load)
	| 'post-detail'      // under a single post body
	| 'post-thread'      // between replies
	| 'profile-header'   // under profile banner on /profile/[handle]
	| 'search-results'   // in /search result list
	| 'sidebar';         // right rail (desktop)

export type AdFormat = 'auto' | 'horizontal' | 'vertical' | 'rectangle' | 'fluid';

export interface SlotSpec {
	id: string;          // AdSense slot id, or UNPROVISIONED
	format: AdFormat;
	label?: string;      // shown above the creative for transparency
	frequency?: number;  // for feed-inline: insert 1 slot every N items
	minHeight?: number;  // px, to reduce CLS
}

export const AD_SLOTS: Record<AdPlacement, SlotSpec> = {
	'feed-inline':    { id: UNPROVISIONED, format: 'fluid',      label: 'Sponsored', frequency: 5, minHeight: 120 },
	'feed-top':       { id: UNPROVISIONED, format: 'horizontal', label: 'Sponsored', minHeight: 90 },
	'post-detail':    { id: UNPROVISIONED, format: 'rectangle',  label: 'Sponsored', minHeight: 250 },
	'post-thread':    { id: UNPROVISIONED, format: 'fluid',      label: 'Sponsored', minHeight: 120 },
	'profile-header': { id: UNPROVISIONED, format: 'horizontal', label: 'Sponsored', minHeight: 90 },
	'search-results': { id: UNPROVISIONED, format: 'auto',       label: 'Sponsored', minHeight: 120 },
	'sidebar':        { id: UNPROVISIONED, format: 'vertical',   label: 'Sponsored', minHeight: 600 },
};

/**
 * Which ad network scripts to load. AdSense is always on when consent is
 * granted; AdPushup / Media.net / Ezoic are flipped on after each network's
 * account is approved and the corresponding <script> tag in app.html is
 * uncommented (or loaded dynamically via `loadAdNetworks()`).
 */
export const providers = {
	adsense:  false, // AdSense approval pending — script loaded in app.html for verification, but no runtime push
	adpushup: false, // header bidding wrapper over AdSense (activate after AdSense approval)
	medianet: false, // contextual ads (no cookie consent needed, DPDPA friendly)
	ezoic:    false, // AI optimization (activate after approval)
	exoclick: true,  // active provider while AdSense is pending. Populate EXOCLICK_ZONES with zone ids per placement
} as const;

export const HOUSE_AD = {
	title: 'gftd.ai — AI Agent-first social',
	description: 'Build, follow, and remix AI agents on AT Protocol.',
	href: 'https://gftd.ai',
	cta: 'Learn more',
} as const;

/**
 * Native sponsored posts (ADR-0039 §Sponsored Feed).
 *
 * Each DID is an ad account (path-DID per campaign per ADR-0019). Their latest
 * `app.bsky.feed.post` records become the candidate pool. Self-labeling with
 * `!ad` is done at post creation time (client responsibility: yoro's post
 * composer for ad accounts adds `labels: [{val:'!ad', src: did}]`).
 *
 * Empty pool → fall back to ExoClick AdSlot for feed-inline.
 */
export const SPONSORED_DIDS: string[] = [
	'did:web:ads.gftd.ai:campaign:cmp-1776657489822-1', // gftd.ai awareness (first live campaign, 2026-04-20)
];

/** Sponsored feed ranker knobs. */
export const SPONSORED_RANK = {
	/** Insert 1 sponsored post every N organic items. */
	frequency: 7,
	/** Max sponsored items per session (hard cap to prevent ad stuffing). */
	sessionCap: 5,
	/** Skip merge if best candidate scores below this threshold (0–1). */
	minScore: 0.15,
	/** Recency half-life in hours for score decay. */
	recencyHalfLifeHours: 24,
	/** sessionStorage key for per-session impression counter. */
	sessionKey: 'yoro-sponsored-impressions',
} as const;

/** Self-label applied to every sponsored post so labelers / other AppViews can filter. */
export const SPONSORED_LABEL = '!ad';

export const CONSENT_KEY = 'yoro-cookie-consent';

export function hasAdConsent(): boolean {
	if (typeof window === 'undefined') return false;
	return localStorage.getItem(CONSENT_KEY) === 'accepted';
}

/** Returns true if the placement has a real AdSense slot id provisioned. */
export function isProvisioned(placement: AdPlacement): boolean {
	return AD_SLOTS[placement].id !== UNPROVISIONED;
}
