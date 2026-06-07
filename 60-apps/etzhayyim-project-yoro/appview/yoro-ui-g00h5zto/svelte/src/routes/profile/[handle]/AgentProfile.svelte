<script lang="ts">
	import { Avatar, Skeleton, Badge, Chip } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { RichText, PostEmbed, ContentLabel, convos, normalizedPostEmbed, postRkey, postRouteActor } from '$lib/w';
	import { getAuthorFeed as getAuthorFeedXrpc, getFollows, getFollowers, followUser, atProcedure, sendProjectMessage, getCurrentDID } from '$lib/atproto-agent';
	import * as localFeed from '$lib/graph/feed';
	import { isSignedIn } from '$lib/auth';
	import type { FollowView } from '$lib/atproto-agent';
	import { unfollowUser } from '$lib/atproto-agent';
	import type { ActorContext } from '$lib/actor';
	import { graphSql, sqlString } from '$lib/graph-sql';
	import { fade } from 'svelte/transition';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import type { Convo, FeedItem } from '$lib/atproto-agent';
	import LiveStage from './LiveStage.svelte';
	import ProjectorGuestChat from './ProjectorGuestChat.svelte';
	// BpmnDiagram is LAZY-loaded (see the {#await} where it is used). It statically
	// imports bpmn-js CSS via BARE specifiers, and bpmn-js is externalized in the
	// build (vite.config rollupOptions.external) — so a STATIC import here placed an
	// unresolvable bare module specifier on the profile route's critical module
	// graph, throwing at module-eval and 500-ing EVERY profile page in the browser
	// (SSR was clean). Lazy import + {:catch} keeps any failure contained to the
	// rare BPMN "Process" tab instead of breaking the whole profile.
	import { BeliefKarmaTab } from '$lib/gamification';
	import { ResourceFlowTab } from '$lib/fiscal';

	interface Props {
		did: string;
		actor: {
			nanoid?: string;
			name?: string;
			description?: string;
			did?: string;
			protocols?: string;
			tools?: string;
			version?: string;
			createdAt?: string;
			subPath?: string;
			avatar?: string;
			uiType?: string;
			embedUrl?: string;
			performerType?: string;
			heroSurface?: string;
			heroKind?: string;
			heroType?: string;
			heroDisabled?: boolean;
			// Gov / civic-actor extensions (kotodama.jsonld profile.*)
			category?: string;
			country?: string;
			addresses?: Array<{kind?: string; label?: string; streetAddress?: string; addressLocality?: string; addressRegion?: string; postalCode?: string; country?: string; latlng?: string}>;
			contacts?: Array<{kind?: string; uri?: string; label?: string; lang?: string[]}>;
			desks?: Array<{kind?: string; label?: string; uri?: string; tel?: string; basis?: string}>;
			procedures?: Array<{id?: string; title?: string; titleLocal?: string; authority?: string; basis?: string; portalUri?: string; bpmnRef?: string; bpmn?: string; dmn?: string; dmnRef?: string; form?: string; formRef?: string; xrpcRef?: string}>;
			documentTemplates?: Array<{id?: string; title?: string; titleLocal?: string; authority?: string; basis?: string; uri?: string}>;
			ministryCount?: number;
			contractCount?: number;
			bpmnCount?: number;
			dataSourceRef?: string;
			complianceFrameworks?: string[];
			// Server-authoritative counts from app.bsky.actor.getProfile (mv_actor_social_stats).
			// When present, used as primary source for the stats badges; client lazy-load
			// (loadPosts/loadFollows) is a fallback for environments where the MV lags.
			postsCount?: number;
			followersCount?: number;
			followsCount?: number;
		};
		capabilities: Array<{
			id?: string;
			description?: string;
			tags?: string;
			phase?: string;
		}>;
		performer: {
			id?: string;
			name?: string;
			kind?: string;
			performerType?: string;
			parentId?: string;
			description?: string;
			heroSurface?: string;
			heroKind?: string;
			heroType?: string;
			heroDisabled?: boolean;
		};
		publicConvos: Convo[];
		initialFollowing?: boolean;
		/** GCC token balance in wei (decimal string). Null = not loaded. "0" = no balance. */
		gccBalance?: string | null;
		/** Activated smart-account address on chain-260425. Null if not activated. */
		gccSmartAccount?: string | null;
	}

	let { did, actor, capabilities, performer, publicConvos, initialFollowing = false, gccBalance = null, gccSmartAccount = null }: Props = $props();

	// Default tab per performerType: all types default to posts (投稿)
	let activeTab = $state('posts');
	let feedItems = $state<FeedItem[]>([]);
	let postsLoading = $state(false);
	let postsLoaded = $state(false);
	let neighbors = $state<Array<{ nodeId: string; label: string; nsPrefix: string; rel: string; description?: string }>>([]);
	let neighborsLoading = $state(false);
	let neighborsLoaded = $state(false);
	let knowledgeGraph = $state<{
		nodes: Array<{ id: string; label: string; nsPrefix: string; description?: string }>;
		edges: Array<{ source: string; target: string; rel: string }>;
	}>({ nodes: [], edges: [] });
	let knowledgeAccessSummary = $state<{ viewerDid?: string; viewerRoles: string[]; visibleCount: number; totalCount: number }>({
		viewerRoles: [],
		visibleCount: 0,
		totalCount: 0,
	});
	let installed = $state(false);
	let mcpTools = $state<Array<{ name: string; description: string; inputSchema?: Record<string, unknown> }>>([]);
	let mcpLoading = $state(false);
	let mcpLoaded = $state(false);
	let follows = $state<FollowView[]>([]);
	let followers = $state<FollowView[]>([]);
	let followsLoading = $state(false);
	let followsLoaded = $state(false);
	let governanceData = $state<{ deps: Array<Record<string, any>>; governance: Array<Record<string, any>>; compliance: Array<Record<string, any>> }>({ deps: [], governance: [], compliance: [] });
	let governanceLoading = $state(false);
	let governanceLoaded = $state(false);
	/** Web pages hosted by this domain DID (canonical + legacy aliases). */
	let domainPages = $state<Array<{ url: string; title: string; domain: string; outlink_count: number; screenshotBlobRef?: string; contentType?: string }>>([]);
	let domainPageCount = $state(0);
	let domainLinkCount = $state(0);
	let domainPagesLoading = $state(false);
	let domainPagesLoaded = $state(false);
	let expandedPageUrl = $state<string | null>(null);
	let expandedWetText = $state('');
	let expandedWetLoading = $state(false);

	function compactText(value: unknown): string {
		return typeof value === 'string' ? value.trim() : '';
	}

	function toRoleLabel(value: string): string {
		return value
			.replace(/[-_]+/g, ' ')
			.replace(/\s+/g, ' ')
			.trim();
	}

	function deriveAgentRoleFromDid(actorDid: string): string {
		if (!actorDid.startsWith('did:web:')) return 'AI agent';
		const didParts = actorDid.replace('did:web:', '').split(':');
		const rolePart = didParts.slice(1).join(' ');
		const roleLabel = toRoleLabel(rolePart);
		return roleLabel ? `${roleLabel} agent` : 'AI agent';
	}

	function normalizedHeroPreference(): string | null {
		const raw = (
			actor.heroSurface ??
			actor.heroKind ??
			actor.heroType ??
			performer.heroSurface ??
			performer.heroKind ??
			performer.heroType ??
			''
		).trim().toLowerCase();
		if (!raw) return null;
		if (['none', 'off', 'disabled', 'compact', 'minimal'].includes(raw)) return 'none';
		if (['baminiku', 'live', 'stage', 'persona'].includes(raw)) return 'baminiku';
		if (['game'].includes(raw)) return 'game';
		if (['iframe', 'embed', 'app', 'web'].includes(raw)) return 'iframe';
		return null;
	}

	const heroPreference = $derived(normalizedHeroPreference());
	const heroDisabled = $derived(Boolean(actor.heroDisabled ?? performer.heroDisabled) || heroPreference === 'none');
	const descriptionText = $derived(compactText(actor.description));
	const roleSubtitle = $derived.by((): string => {
		if (descriptionText) return descriptionText;
		const performerType = compactText(performer.performerType).toLowerCase();
		if (performerType === 'system') return 'System agent';
		if (performerType === 'organization') return 'Organization agent';
		if (performerType === 'person') return 'Personal agent';
		return deriveAgentRoleFromDid(did);
	});

	// Hero kind resolution: performerType + heroPreference + capability
	//
	//   preference \ performerType | person      | service       | system       | organization
	//   ──────────────────────────────────────────────────────────────────────────────────────────
	//   disabled / 'none'          | none        | none          | none         | none
	//   'baminiku'                 | baminiku    | baminiku      | baminiku     | baminiku
	//   'iframe'                   | iframe*     | iframe*       | iframe*      | iframe*
	//   null (auto)                | baminiku    | iframe*/app   | iframe*/stat | iframe*/org
	//   * iframe requires embedUrl; fallback = type-specific hero (app-card / status / org-banner)
	//   'none' = no hero at all (compact header only, no empty box)
	const heroKind = $derived.by((): 'baminiku' | 'iframe' | 'game' | 'app-card' | 'status' | 'org-banner' | 'none' => {
		if (heroDisabled) return 'none';
		const hasEmbed = !!appPreview?.embedUrl;
		if (heroPreference === 'baminiku') return 'baminiku';
		if (heroPreference === 'game') return hasEmbed ? 'game' : 'none';
		if (heroPreference === 'iframe') return hasEmbed ? 'iframe' : 'none';
		// Auto-detect: uiType === 'game' from /_app/meta
		if (appPreview?.uiType === 'game' && hasEmbed) return 'game';
		// Auto-detect by performerType
		const pt = performer.performerType;
		if (pt === 'person') return 'baminiku';
		if (pt === 'organization') return hasEmbed ? 'iframe' : 'org-banner';
		if (pt === 'system') return hasEmbed ? 'iframe' : 'status';
		// service (default)
		return hasEmbed ? 'iframe' : 'app-card';
	});

	/** Whether this agent is a utility service that supports contract subscription. */
	const isContractableUtility = $derived(
		did.includes('dk3n7k8p') || did.includes('denki.etzhayyim.com') ||
		did.includes('sd9w2t4r') || did.includes('suido.etzhayyim.com') ||
		did.includes('gs5a6s1m') || did.includes('gas.etzhayyim.com')
	);

	// Gov / civic profile detection
	const hasGovInfo = $derived(
		(actor.addresses?.length ?? 0) > 0 ||
		(actor.desks?.length ?? 0) > 0 ||
		(actor.procedures?.length ?? 0) > 0 ||
		(actor.documentTemplates?.length ?? 0) > 0 ||
		actor.category === 'government'
	);
	const govTab = $derived(hasGovInfo ? [{ id: 'gov', label: actor.category === 'government' ? '行政' : '案内' }] : []);

	// BPMN process tab — generic: any actor that publishes a BPMN manifest
	// (<app-base>/_app/bpmn.json, or actor.bpmnUrl, or a same-origin static
	// fallback) gets a read-only "プロセス" tab rendering its BPMN with bpmn-js.
	type BpmnProcess = { id: string; name: string; company?: string; kind?: string; xml: string };
	let bpmnManifest = $state<{ total: number; processes: BpmnProcess[] } | null>(null);
	let bpmnLoading = $state(false);
	let selectedBpmnId = $state('');
	const bpmnTab = $derived(
		bpmnManifest && bpmnManifest.processes.length > 0 ? [{ id: 'bpmn', label: 'プロセス' }] : []
	);
	const selectedBpmnProcess = $derived(
		bpmnManifest?.processes.find((p) => p.id === selectedBpmnId) ?? null
	);

	const agentTabs = $derived((() => {
		switch (performer.performerType) {
			case 'person':
				return [
					{ id: 'posts', label: '投稿' },
					{ id: 'app', label: 'チャット' },
					...bpmnTab,
					{ id: 'tools', label: 'ツール' },
					{ id: 'graph', label: 'ナリッジグラフ' },
					{ id: 'follows', label: 'フォロー' },
					{ id: 'karma', label: 'カルマ' },
					{ id: 'flow', label: 'Resource Flow' },
				];
			case 'organization':
				return [
					{ id: 'posts', label: '投稿' },
					{ id: 'overview', label: '概要' },
					...bpmnTab,
					...govTab,
					{ id: 'tools', label: 'ツール' },
					{ id: 'governance', label: 'ガバナンス' },
					{ id: 'graph', label: 'ナリッジグラフ' },
					{ id: 'follows', label: 'フォロー' },
					{ id: 'karma', label: 'カルマ' },
					{ id: 'flow', label: 'Resource Flow' },
				];
			case 'system':
				return [
					{ id: 'posts', label: 'ログ' },
					{ id: 'overview', label: 'ステータス' },
					...bpmnTab,
					{ id: 'tools', label: 'ツール' },
					{ id: 'graph', label: 'ナリッジグラフ' },
					{ id: 'follows', label: 'フォロー' },
					{ id: 'karma', label: 'カルマ' },
					{ id: 'flow', label: 'Resource Flow' },
				];
			default: // 'service'
				return [
					{ id: 'posts', label: '投稿' },
					...govTab,
					...bpmnTab,
					...(isContractableUtility ? [{ id: 'contract', label: '契約' }] : []),
					{ id: 'tools', label: 'ツール' },
					{ id: 'graph', label: 'ナリッジグラフ' },
					{ id: 'governance', label: 'ガバナンス' },
					{ id: 'follows', label: 'フォロー' },
					{ id: 'karma', label: 'カルマ' },
					{ id: 'flow', label: 'Resource Flow' },
				];
		}
	})());

	// App preview: 4-tier uiType embed
	let appPreview = $state<{
		uiType: string;
		nanoid: string;
		esmUrl?: string;
		elementTag?: string;
		elementUrl?: string;
		embedUrl?: string;
		capabilities?: string[];
		screenshotCid?: string;
	} | null>(null);
	let appLoading = $state(false);
	// Auto-expand app embed when redirected from subdomain (?app=1)
	const autoEmbed = $derived(($page.url as URL).searchParams.has('app'));
	let showAppEmbed = $state(false);
	let miniAppCtx = $state<ActorContext | null>(null);

	function getFallbackCtx(): ActorContext {
		const nn = appPreview?.nanoid ?? '';
		return {
			nanoid: nn, name: actor.name ?? 'App', userId: '', actorId: '', orgId: '',
			wSend: async () => {}, wQuery: async () => null,
			backend: { call: async () => { throw 'preview mode'; } },
			cypher: { exec: async () => {}, query: async () => [] },
			navigate: () => {}, remoteCall: async () => new Uint8Array(0),
		} as ActorContext;
	}

	// Detect sub-DID profile (per-game, per-entity) — PDS provides all data
	const isSubDid = $derived(!!actor.subPath);

	/** Real nanoid is 8 lowercase alphanumeric chars */
	const NANOID_RE = /^[a-z0-9]{8}$/;
	const TRUSTED_EMBED_HOSTS = new Set([
		'yoro.etzhayyim.com',
	]);

	function isTrustedEmbedUrl(url: string | undefined | null): url is string {
		if (!url) return false;
		try {
			const parsed = new URL(url);
			if (parsed.protocol !== 'https:') return false;
			return parsed.hostname.endsWith('.etzhayyim.com') || TRUSTED_EMBED_HOSTS.has(parsed.hostname);
		} catch {
			return false;
		}
	}

	/** Fallback: derive appPreview from /_app/meta (host-sdk standard endpoint) */
	async function loadAppPreviewFromMeta(appHost: string) {
		const nn = actor.nanoid ?? '';

		// Build candidate hosts: vanity host, then nanoid host (if different), then discovered nanoid
		const tried = new Set<string>();

		async function tryHost(host: string): Promise<boolean> {
			if (!host || tried.has(host)) return false;
			tried.add(host);
			try {
				const metaResp = await fetch(`https://${host}/_app/meta`, {
					headers: { Accept: 'application/json' },
					signal: AbortSignal.timeout(1000),
				});
				if (!metaResp.ok) return false;
				const meta = await metaResp.json();
				const rawUi = meta.uiMode ?? meta.uiType ?? meta.ui ?? 'appview';
				const uiMap: Record<string, string> = { canvas: 'appview', custom: 'esm', miniapp: 'esm', full: 'iframe', fullapp: 'iframe' };
				const normalizedUi = uiMap[rawUi] ?? rawUi;
				const metaNanoid = meta.appId ?? meta.nanoid ?? '';
				const deploySha = meta.deploy_sha ?? '';

				// Skip dispatcher-like responses (no deploy_sha + appview = no real app content)
				// But accept game/iframe uiType even without deploy_sha (real app with meaningful uiType)
				if (!deploySha && normalizedUi === 'appview') {
					// Try the real nanoid host if meta returns a valid appId
					if (metaNanoid && NANOID_RE.test(metaNanoid)) {
						const realHost = `${metaNanoid}.etzhayyim.com`;
						if (await tryHost(realHost)) return true;
					}
					return false;
				}

				const canInlineEmbed = did.startsWith('did:web:') && host !== 'atproto.etzhayyim.com';
				const isGame = normalizedUi === 'game';
				const previewUi = isGame ? 'game' : ((normalizedUi !== 'appview' || canInlineEmbed) ? 'iframe' : 'appview');
				// Embed URL: prefer /_app/meta embedUrl, fallback to ?embed=1
				const embedNanoid = NANOID_RE.test(metaNanoid) ? metaNanoid : (NANOID_RE.test(nn) ? nn : '');
				const embedHost = embedNanoid ? `${embedNanoid}.etzhayyim.com` : host;
				const metaEmbedUrl = (meta as any).embedUrl as string | undefined;
				const fallbackEmbedUrl = `https://${embedHost}/?embed=1${actor.subPath ? `&entity=${encodeURIComponent(actor.subPath)}` : ''}`;
				const embedUrl = isTrustedEmbedUrl(metaEmbedUrl) ? metaEmbedUrl : fallbackEmbedUrl;
				appPreview = {
					uiType: previewUi,
					nanoid: metaNanoid || nn,
					embedUrl,
					capabilities: meta.capabilities,
				};
				if (metaNanoid && !actor.nanoid) actor.nanoid = metaNanoid;
				return true;
			} catch (e) {
				console.warn(`agent profile: /_app/meta from ${host} failed`, e);
				return false;
			}
		}

		// Try vanity host first
		if (await tryHost(appHost)) return;
		// Try actor nanoid host
		const nanoidHost = nn ? `${nn}.etzhayyim.com` : '';
		if (nanoidHost !== appHost && await tryHost(nanoidHost)) return;

		appPreview = { uiType: 'appview', nanoid: nn };
	}

	/**
	 * Discover an actor's BPMN manifest (generic contract). Tries, in order:
	 *   1. actor.bpmnUrl (explicit field on the PDS profile record)
	 *   2. <app-base>/_app/bpmn.json  (app origin from embedUrl, else did:web host)
	 *   3. /actor-bpmn/<handle>.json  (same-origin static fallback, appview-bundled)
	 * The manifest is `{ total, processes: [{ id, name, company?, kind?, xml }] }`.
	 * If found, the "プロセス" tab appears and renders each process with bpmn-js.
	 */
	async function loadBpmnManifest() {
		if (bpmnManifest || bpmnLoading) return;
		bpmnLoading = true;
		try {
			const urls: string[] = [];
			const explicit = (actor as { bpmnUrl?: string }).bpmnUrl;
			if (explicit) urls.push(explicit);
			let base = '';
			if (appPreview?.embedUrl) {
				try { base = new URL(appPreview.embedUrl).origin; } catch { /* ignore */ }
			}
			if (!base && did.startsWith('did:web:')) {
				base = `https://${did.replace('did:web:', '').split(':')[0]}`;
			}
			if (base) urls.push(`${base}/_app/bpmn.json`);
			const handle = did.startsWith('did:web:') ? (did.split(':').pop() ?? '') : (actor.nanoid ?? '');
			if (handle) urls.push(`/actor-bpmn/${handle}.json`);

			for (const u of urls) {
				try {
					const r = await fetch(u);
					if (!r.ok) continue;
					const m = await r.json();
					if (m && Array.isArray(m.processes) && m.processes.length > 0) {
						bpmnManifest = { total: m.total ?? m.processes.length, processes: m.processes };
						selectedBpmnId = m.processes[0].id;
						return;
					}
				} catch { /* try next candidate */ }
			}
		} finally {
			bpmnLoading = false;
		}
	}

	async function loadAppPreview() {
		if (appPreview || appLoading) return;
		appLoading = true;
		try {
			// Fast path: profile already has embedUrl from PDS (no /_app/meta fetch needed)
			const profileEmbed = actor.embedUrl;
			const profileUiType = actor.uiType;
			if (isTrustedEmbedUrl(profileEmbed) && profileUiType) {
				const uiMap: Record<string, string> = { canvas: 'appview', custom: 'esm', miniapp: 'esm', full: 'iframe', fullapp: 'iframe' };
				const normalizedUi = uiMap[profileUiType] ?? profileUiType;
				const previewUi = normalizedUi === 'game' ? 'game' : (normalizedUi === 'iframe' ? 'iframe' : 'appview');
				appPreview = {
					uiType: previewUi,
					nanoid: actor.nanoid ?? '',
					embedUrl: profileEmbed,
				};
				return;
			}

			// Derive app base URL from did:web: — handle sub-path DIDs (colon = path separator)
			let appHost: string;
			if (did.startsWith('did:web:')) {
				const didParts = did.replace('did:web:', '').split(':');
				appHost = didParts[0];
			} else {
				appHost = `${actor.nanoid}.etzhayyim.com`;
			}
				// atproto.etzhayyim.com is the data gateway, not an App — skip manifest
			if (appHost === 'atproto.etzhayyim.com') {
				appPreview = { uiType: 'appview', nanoid: actor.nanoid ?? '' };
				return;
			}
			await loadAppPreviewFromMeta(appHost);
		} catch (e) {
			console.warn('agent profile: loadAppPreview failed, trying /_app/meta', e);
			try {
				const appHost = did.startsWith('did:web:') ? did.replace('did:web:', '').split(':')[0] : `${actor.nanoid}.etzhayyim.com`;
				if (appHost !== 'atproto.etzhayyim.com') await loadAppPreviewFromMeta(appHost);
				else appPreview = { uiType: 'appview', nanoid: actor.nanoid ?? '' };
			} catch {
				appPreview = { uiType: 'appview', nanoid: actor.nanoid ?? '' };
			}
		} finally {
			appLoading = false;
		}
	}

	// Parse tools from actor.tools (JSON string or comma-separated)
	function parseTools(toolsStr: string | undefined): string[] {
		if (!toolsStr) return [];
		try {
			const parsed = JSON.parse(toolsStr);
			if (Array.isArray(parsed)) return parsed;
		} catch { /* not JSON */ }
		return toolsStr.split(',').map((t: string) => t.trim()).filter(Boolean);
	}

	// Parse tags from capability.tags
	function parseTags(tagsStr: string | undefined): string[] {
		if (!tagsStr) return [];
		try {
			const parsed = JSON.parse(tagsStr);
			if (Array.isArray(parsed)) return parsed;
		} catch { /* not JSON */ }
		return tagsStr.split(',').map((t: string) => t.trim()).filter(Boolean);
	}

	// Parse protocols
	function parseProtocols(protocolsStr: string | undefined): string[] {
		if (!protocolsStr) return [];
		try {
			const parsed = JSON.parse(protocolsStr);
			if (Array.isArray(parsed)) return parsed;
		} catch { /* not JSON */ }
		return protocolsStr.split(',').map((t: string) => t.trim()).filter(Boolean);
	}

	const tools = $derived(parseTools(actor.tools));
	const protocols = $derived(parseProtocols(actor.protocols));
	const knowledgeCount = $derived(Math.max(neighbors.length, domainPageCount));
	// Stats: server-authoritative counts (mv_actor_social_stats via getProfile)
	// take precedence, but only when they're non-zero. A stale MV returning 0 for
	// a DID with posts would otherwise win against the client lazy-load
	// (which `loadPosts()` populates). `??` falls back only on null/undefined —
	// wrong for us, since the MV legitimately returns the number 0 for both
	// "no posts" and "not yet aggregated" cases. Prefer server when >0, fall back
	// to client-loaded array length otherwise. (ADR-2604241038 contract 4.)
	const postsCountDisplay = $derived(
		actor.postsCount && actor.postsCount > 0 ? actor.postsCount : feedItems.length,
	);
	const followersCountDisplay = $derived(
		actor.followersCount && actor.followersCount > 0 ? actor.followersCount : followers.length,
	);
	const followsCountDisplay = $derived(
		actor.followsCount && actor.followsCount > 0 ? actor.followsCount : follows.length,
	);
	const isColdStart = $derived(
		postsCountDisplay === 0 &&
		followersCountDisplay === 0 &&
		followsCountDisplay === 0 &&
		knowledgeCount === 0,
	);

	const gccBalanceFormatted = $derived.by(() => {
		if (gccBalance === null || gccBalance === '0') return null;
		try {
			const gcc = Number(BigInt(gccBalance)) / 1e18;
			return gcc.toLocaleString('ja-JP', { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + ' GCC';
		} catch { return null; }
	});

	/** Fetch MCP tools via PDS MCP gateway, fallback to PDS getProfile capabilities. */
	async function loadMcpTools() {
		if (mcpLoaded || mcpLoading) return;
		mcpLoading = true;
		try {
			let appName = actor.nanoid ?? '';
			if (did.startsWith('did:web:')) {
				const host = did.replace('did:web:', '').split(':')[0];
				const m = host.match(/^([^.]+)\.etzhayyim\.ai$/);
				if (m) appName = m[1];
			}
				if (!appName) { mcpLoaded = true; return; }
				const viewerDid = await getCurrentDID().catch(() => '');

				// Browser traffic enters the SvelteKit BFF; the server routes to agentgateway's MCP router.
				const resp = await fetch('/api/mcp', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						jsonrpc: '2.0',
						id: Date.now(),
						method: 'tools/list',
						params: viewerDid ? { app: appName, did: viewerDid } : { app: appName },
					}),
					signal: AbortSignal.timeout(2000),
				});
			if (resp.ok) {
				const data = await resp.json();
				const toolsList = data?.result?.tools;
				if (Array.isArray(toolsList) && toolsList.length > 0) {
					mcpTools = toolsList.map((t: any) => ({
						name: String(t.name ?? ''),
						description: String(t.description ?? ''),
						inputSchema: t.inputSchema,
					}));
				}
			}

			// PDS getProfile capabilities (already fetched, no extra roundtrip)
			if (mcpTools.length === 0 && capabilities.length > 0) {
				mcpTools = capabilities
					.filter((c) => c.id || c.description)
					.map((c) => ({
						name: `${appName}.${c.id ?? 'capability'}`,
						description: String(c.description ?? c.id ?? ''),
					}));
			}
		} catch (e) {
			console.warn('agent profile: loadMcpTools failed', e);
		} finally {
			mcpLoading = false;
			mcpLoaded = true;
		}
	}

	function timeAgo(ts: string): string {
		const date = new Date(ts);
		if (Number.isNaN(date.getTime())) return 'now';
		const diff = Date.now() - date.getTime();
		const mins = Math.max(0, Math.floor(diff / 60000));
		if (mins < 60) return `${mins}分`;
		const hrs = Math.floor(mins / 60);
		if (hrs < 24) return `${hrs}時間`;
		return `${Math.floor(hrs / 24)}日`;
	}

	// Eagerly load posts (default tab) + app preview + MCP tools + follows (for stats)
	$effect(() => {
		if (!postsLoaded && !postsLoading) {
			void loadPosts();
		}
		if (!appPreview && !appLoading) {
			void loadAppPreview();
		}
		if (!bpmnManifest && !bpmnLoading) {
			void loadBpmnManifest();
		}
		if (!mcpLoaded && !mcpLoading) {
			void loadMcpTools();
		}
		if (!followsLoaded && !followsLoading) {
			void loadFollows();
		}
		if (!neighborsLoaded && !neighborsLoading) {
			void loadGraph();
		}
		if (!domainPagesLoaded && !domainPagesLoading && domainDidCandidatesFromDid(did).length > 0) {
			void loadDomainPages();
		}
	});

	// Auto-expand iframe when redirected from subdomain and app preview is ready
	$effect(() => {
		if (heroKind === 'iframe' || heroKind === 'game') {
			showAppEmbed = false;
			return;
		}
		if (autoEmbed && (appPreview?.uiType === 'iframe' || appPreview?.uiType === 'game') && !showAppEmbed) {
			showAppEmbed = true;
		}
	});

	$effect(() => {
		if (activeTab === 'app' && !appPreview && !appLoading) {
			void loadAppPreview();
		}
		if ((activeTab === 'posts' || activeTab === 'app') && !postsLoaded && !postsLoading) {
			void loadPosts();
		}
		if (activeTab === 'graph' && !neighborsLoaded && !neighborsLoading) {
			void loadGraph();
		}
		if (activeTab === 'graph' && !domainPagesLoaded && !domainPagesLoading && domainDidCandidatesFromDid(did).length > 0) {
			void loadDomainPages();
		}
		if ((activeTab === 'capabilities' || activeTab === 'tools') && !mcpLoaded && !mcpLoading) {
			void loadMcpTools();
		}
		if (activeTab === 'follows' && !followsLoaded && !followsLoading) {
			void loadFollows();
		}
		if (activeTab === 'governance' && !governanceLoaded && !governanceLoading) {
			void loadGovernance();
		}
	});

	let installBusy = $state(false);
	let followBusy = $state(false);
	let following = $state(initialFollowing);

	// Sync following state when prop changes (e.g., profile reload)
	$effect(() => { following = initialFollowing; });

	async function handleFollow() {
		if (followBusy) return;
		followBusy = true;
		try {
			if (following) {
				await unfollowUser(did);
				following = false;
			} else {
				await followUser(did);
				following = true;
			}
		} catch (e) {
			console.warn('follow toggle failed', e);
		} finally {
			followBusy = false;
		}
	}

	async function handleInstall() {
		if (installBusy) return;
		installBusy = true;
		try {
			// Follow the app DID if not already following
			if (!following) {
				await followUser(did);
				following = true;
			}
			// Create project convo (com.etzhayyim.projector) instead of DM
			const res = await atProcedure<Record<string, unknown>>('com.etzhayyim.projector.newProjectConvo', {
				name: actor.name || did,
				members: [did],
			}).catch((e: unknown) => {
				console.warn('install: newProjectConvo failed', e);
				return null;
			});
			const convoId = (res as Record<string, unknown> | null)?.convoId as string | undefined;
			if (convoId) {
				convos.refresh();
				installed = true;
				await goto(`/projects/${encodeURIComponent(convoId)}`, { keepFocus: true, noScroll: true });
			}
		} catch (e) {
			console.warn('install: background tasks failed', e);
		} finally {
			installBusy = false;
		}
	}

	let contractBusy = $state(false);

	/** Follow + project convo + send /subscribe → navigate to convo for contract negotiation. */
	async function handleContract() {
		if (contractBusy) return;
		contractBusy = true;
		try {
			if (!following) {
				await followUser(did);
				following = true;
			}
			// Create project convo (com.etzhayyim.projector) instead of DM
			const res = await atProcedure<Record<string, unknown>>('com.etzhayyim.projector.newProjectConvo', {
				name: actor.name || did,
				members: [did],
			}).catch((e: unknown) => {
				console.warn('contract: newProjectConvo failed', e);
				return null;
			});
			const convoId = (res as Record<string, unknown> | null)?.convoId as string | undefined;
			if (convoId) {
				await sendProjectMessage(convoId, '/subscribe').catch((e: unknown) =>
					console.warn('contract: sendProjectMessage failed', e),
				);
				convos.refresh();
				installed = true;
				await goto(`/projects/${encodeURIComponent(convoId)}`, { keepFocus: true, noScroll: true });
			}
		} catch (e) {
			console.warn('contract: failed', e);
		} finally {
			contractBusy = false;
		}
	}

	async function loadPosts() {
		postsLoading = true;
		try {
			const result = await localFeed.getAuthorFeed(did, { limit: 50 });
			let items = Array.isArray(result) ? result : (result?.feed ?? []);
			if (items.length === 0) {
				items = await loadPostsFromListRecords();
			}
			const seenKeys = new Set<string>();
			const seenTexts = new Set<string>();
			feedItems = items.filter((item) => {
				const key = item?.post?.uri || `${item?.post?.author?.did || ''}/${item?.post?.rkey || ''}`;
				if (!key || seenKeys.has(key)) return false;
				seenKeys.add(key);
				// Also dedup by text content to catch duplicate posts from shinka reruns.
				const record = item?.post?.record as Record<string, any> | undefined;
				const text = String(item?.post?.text ?? record?.text ?? '').trim().slice(0, 100);
				const textKey = `${item?.post?.author?.did || ''}:${text}`;
				if (text && seenTexts.has(textKey)) return false;
				if (text) seenTexts.add(textKey);
				return true;
			});
		} catch (e) { console.error('agent profile: loadPosts failed', e); feedItems = []; }
		finally { postsLoading = false; postsLoaded = true; }
	}

	function extractRkeyFromAtUri(uri: string): string {
		if (!uri) return '';
		const parts = uri.split('/');
		return parts[parts.length - 1] ?? '';
	}

	async function loadPostsFromListRecords(): Promise<FeedItem[]> {
		try {
			const url = new URL('https://atproto.etzhayyim.com/xrpc/com.atproto.repo.listRecords');
			url.searchParams.set('repo', did);
			url.searchParams.set('collection', 'app.bsky.feed.post');
			url.searchParams.set('limit', '50');
			const response = await fetch(url.toString(), { headers: { Accept: 'application/json' } });
			if (!response.ok) return [];
			const body = await response.json() as {
				records?: Array<{
					uri?: string;
					cid?: string;
					value?: {
						text?: string;
						createdAt?: string;
						facets?: unknown[];
					};
				}>;
			};
			const rows = Array.isArray(body.records) ? body.records : [];
			return rows
				.map((row): FeedItem | null => {
					const uri = row?.uri ?? '';
					const value = row?.value ?? {};
					const rkey = extractRkeyFromAtUri(uri);
					if (!uri || !rkey) return null;
					return {
						post: {
							uri,
							cid: row?.cid ?? '',
							author: {
								did,
								handle: did,
								displayName: actor.name ?? did,
								avatar: actor.avatar,
							},
							text: typeof value.text === 'string' ? value.text : '',
							likeCount: 0,
							repostCount: 0,
							replyCount: 0,
							viewCount: 0,
							quoteCount: 0,
							indexedAt: typeof value.createdAt === 'string' && value.createdAt ? value.createdAt : new Date().toISOString(),
							rkey,
							facets: Array.isArray(value.facets) ? value.facets as any : [],
						},
					};
				})
				.filter((item): item is FeedItem => item !== null)
				.sort((a, b) => (a.post.indexedAt < b.post.indexedAt ? 1 : -1));
		} catch (error) {
			console.warn('agent profile: loadPostsFromListRecords failed', error);
			return [];
		}
	}

	/** Convert positional rows + columns into named objects */
	function rowsToObjects(columns: string[], rows: any[]): any[] {
		if (!columns?.length || !rows?.length) return [];
		return rows.map((row: any) => {
			if (!Array.isArray(row)) return row; // already an object
			const obj: any = {};
			columns.forEach((col, i) => { obj[col] = row[i] ?? null; });
			return obj;
		});
	}

	function normalizeRoleValue(input: unknown): string[] {
		if (!input) return [];
		if (Array.isArray(input)) return input.map((v) => String(v).trim().toLowerCase()).filter(Boolean);
		if (typeof input === 'string') {
			const s = input.trim();
			if (!s) return [];
			try {
				const parsed = JSON.parse(s);
				if (Array.isArray(parsed)) return parsed.map((v) => String(v).trim().toLowerCase()).filter(Boolean);
			} catch {
				/* ignore */
			}
			if (s.includes(',')) return s.split(',').map((v) => v.trim().toLowerCase()).filter(Boolean);
			return [s.toLowerCase()];
		}
		return [String(input).trim().toLowerCase()].filter(Boolean);
	}

	function normalizeVisibility(input: unknown): string {
		return String(input ?? '').trim().toLowerCase();
	}

	function collectRowRoles(row: Record<string, unknown>): string[] {
		return Array.from(new Set([
			...normalizeRoleValue(row.required_roles),
			...normalizeRoleValue(row.required_role),
			...normalizeRoleValue(row.allowed_roles),
			...normalizeRoleValue(row.rbac_roles),
			...normalizeRoleValue(row.view_roles),
			...normalizeRoleValue(row.roles),
			...normalizeRoleValue(row.edge_required_roles),
			...normalizeRoleValue(row.edge_allowed_roles),
		]));
	}

	function rowHasRaciAccess(row: Record<string, unknown>, viewerDid: string): boolean {
		const rawCandidates: unknown[] = [row.raci_json, row.raci, row.edge_raci_json, row.edge_raci];
		for (const raw of rawCandidates) {
			if (!raw) continue;
			try {
				const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
				const items = Array.isArray(parsed) ? parsed : [];
				if (items.some((it: any) => String(it?.did ?? it?.value ?? '').trim().toLowerCase() === viewerDid.toLowerCase())) {
					return true;
				}
			} catch {
				/* ignore malformed JSON */
			}
		}
		return false;
	}

	function canViewKnowledgeRow(
		row: Record<string, unknown>,
		viewerDid: string | null,
		viewerRoles: string[],
		isOwner: boolean,
		canViewAsFollower: boolean,
	): boolean {
		if (isOwner) return true;

		const visibility = normalizeVisibility(row.visibility || row.edge_visibility || row.access || row.edge_access || 'public');
		const rowRoles = collectRowRoles(row);
		const hasRole = rowRoles.length > 0 && rowRoles.some((r) => viewerRoles.includes(r));
		const hasRaci = !!viewerDid && rowHasRaciAccess(row, viewerDid);

		if (!visibility || visibility === 'public' || visibility === 'open') return true;
		if (visibility === 'followers') return canViewAsFollower;
		if (visibility === 'private' || visibility === 'owner') return false;
		if (visibility === 'raci') return hasRaci || hasRole;
		if (visibility === 'rbac') return hasRole;
		if (['internal', 'restricted', 'protected'].includes(visibility)) return hasRole || hasRaci;
		return hasRole || hasRaci;
	}

	function buildKnowledgeGraph(
		rootDid: string,
		rows: Array<Record<string, unknown>>,
	): {
		nodes: Array<{ id: string; label: string; nsPrefix: string; description?: string }>;
		edges: Array<{ source: string; target: string; rel: string }>;
	} {
		const nodeMap = new Map<string, { id: string; label: string; nsPrefix: string; description?: string }>();
		nodeMap.set(rootDid, {
			id: rootDid,
			label: actor.name ?? rootDid.replace(/^did:web:/, ''),
			nsPrefix: 'ACT',
			description: actor.description ?? '',
		});

		const edges: Array<{ source: string; target: string; rel: string }> = [];

		for (const row of rows) {
			const nodeId = String(row.nodeId ?? row.targetDid ?? row.did ?? '').trim();
			if (!nodeId) continue;
			const label = String(row.label ?? row.display_name ?? nodeId).trim();
			const nsPrefix = String(row.nsPrefix ?? row.nodeLabel ?? 'KNW').trim();
			const description = String(row.description ?? '').trim();
			if (!nodeMap.has(nodeId)) {
				nodeMap.set(nodeId, { id: nodeId, label, nsPrefix, description });
			}
			edges.push({
				source: rootDid,
				target: nodeId,
				rel: String(row.rel ?? row.relation ?? 'RELATED_TO').trim() || 'RELATED_TO',
			});
		}

		return {
			nodes: Array.from(nodeMap.values()),
			edges,
		};
	}

	const knowledgeGraphSvg = $derived.by(() => {
		const width = 760;
		const height = 420;
		const cx = width / 2;
		const cy = height / 2;
		const radius = Math.min(width, height) * 0.33;
		const allNodes = knowledgeGraph.nodes;
		const outer = allNodes.filter((n) => n.id !== did);
		const outerCount = Math.max(outer.length, 1);
		const positions = new Map<string, { x: number; y: number }>();
		positions.set(did, { x: cx, y: cy });
		outer.forEach((n, i) => {
			const angle = (Math.PI * 2 * i) / outerCount - Math.PI / 2;
			positions.set(n.id, { x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius });
		});
		const escapeXml = (s: string) =>
			s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
		const label = (s: string, max = 16) => (s.length > max ? `${s.slice(0, max - 1)}…` : s);

		const edgeLayer = knowledgeGraph.edges
			.map((e) => {
				const a = positions.get(e.source);
				const b = positions.get(e.target);
				if (!a || !b) return '';
				return `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" stroke="rgba(17,133,254,0.35)" stroke-width="1.5" />`;
			})
			.join('');
		const edgeLabels = knowledgeGraph.edges
			.map((e) => {
				const a = positions.get(e.source);
				const b = positions.get(e.target);
				if (!a || !b) return '';
				const mx = (a.x + b.x) / 2;
				const my = (a.y + b.y) / 2;
				return `<text x="${mx}" y="${my - 6}" font-size="10" text-anchor="middle" fill="rgba(148,163,184,0.9)">${escapeXml(label(e.rel, 14))}</text>`;
			})
			.join('');
		const nodeLayer = allNodes
			.map((n) => {
				const p = positions.get(n.id);
				if (!p) return '';
				const isRoot = n.id === did;
				const fill = isRoot ? '#1185FE' : 'rgba(17,133,254,0.18)';
				const stroke = isRoot ? 'rgba(255,255,255,0.9)' : 'rgba(17,133,254,0.55)';
				const text = isRoot ? '#ffffff' : '#e2e8f0';
				return `<g>
					<circle cx="${p.x}" cy="${p.y}" r="${isRoot ? 22 : 16}" fill="${fill}" stroke="${stroke}" stroke-width="${isRoot ? 2 : 1.2}" />
					<text x="${p.x}" y="${p.y + 4}" font-size="${isRoot ? 11 : 10}" text-anchor="middle" fill="${text}" font-weight="${isRoot ? 700 : 600}">${escapeXml(label(n.nsPrefix || 'KNW', 4).toUpperCase())}</text>
					<text x="${p.x}" y="${p.y + (isRoot ? 38 : 30)}" font-size="11" text-anchor="middle" fill="rgba(203,213,225,0.95)">${escapeXml(label(n.label || n.id, 18))}</text>
				</g>`;
			})
			.join('');

		return `<svg viewBox="0 0 ${width} ${height}" width="100%" height="100%" role="img" aria-label="Knowledge graph">${edgeLayer}${edgeLabels}${nodeLayer}</svg>`;
	});

	function splitDidWeb(d: string): { host: string; path: string[] } | null {
		if (!d.startsWith('did:web:')) return null;
		const rest = d.slice('did:web:'.length);
		const colonIdx = rest.indexOf(':');
		const slashIdx = rest.indexOf('/');
		const hasColon = colonIdx >= 0;
		const hasSlash = slashIdx >= 0;
		if (!hasColon && !hasSlash) return { host: rest, path: [] };
		if (hasColon && (!hasSlash || colonIdx < slashIdx)) {
			return {
				host: rest.slice(0, colonIdx),
				path: rest.slice(colonIdx + 1).split(':').map((s) => s.trim()).filter(Boolean),
			};
		}
		return {
			host: rest.slice(0, slashIdx),
			path: rest.slice(slashIdx + 1).split('/').map((s) => s.trim()).filter(Boolean),
		};
	}

	function domainDidCandidatesFromDid(d: string): string[] {
		const parsed = splitDidWeb(d);
		if (!parsed) return [];
		const mkDid = (host: string, path: string[]) => path.length > 0 ? `did:web:${host}:${path.join(':')}` : `did:web:${host}`;
		const out: string[] = [];
		const pushSiteAliases = (slug: string, tail: string[]) => {
			out.push(mkDid('site.etzhayyim.com', [slug, ...tail]));
			out.push(mkDid('w3bpg001.etzhayyim.com', [slug, ...tail]));
		};

		if (parsed.host === 'site.etzhayyim.com' && parsed.path.length > 0) {
			const [slug, ...tail] = parsed.path;
			const canonicalHost = slug.endsWith('.etzhayyim.com') ? slug : `${slug}.etzhayyim.com`;
			out.push(mkDid(canonicalHost, tail));
			pushSiteAliases(slug, tail);
			return Array.from(new Set(out));
		}

		if (parsed.host === 'w3bpg001.etzhayyim.com' && parsed.path.length > 0) {
			const [slug, ...tail] = parsed.path;
			const canonicalHost = slug.endsWith('.etzhayyim.com') ? slug : `${slug}.etzhayyim.com`;
			out.push(mkDid(canonicalHost, tail));
			pushSiteAliases(slug, tail);
			return Array.from(new Set(out));
		}

		if (parsed.host.endsWith('.etzhayyim.com') && parsed.host !== 'atproto.etzhayyim.com') {
			const slug = parsed.host.replace(/\.etzhayyim\.ai$/, '');
			out.push(mkDid(parsed.host, parsed.path));
			pushSiteAliases(slug, parsed.path);
		}

		return Array.from(new Set(out));
	}

	function domainHintFromDid(d: string): string | null {
		const parsed = splitDidWeb(domainDidCandidatesFromDid(d)[0] ?? d);
		if (!parsed) return null;
		if (parsed.host === 'site.etzhayyim.com') {
			return parsed.path[0] ? parsed.path[0].replace(/-/g, '.') : null;
		}
		if (parsed.host.endsWith('.etzhayyim.com')) {
			return parsed.host.replace(/\.etzhayyim\.ai$/, '').replace(/-/g, '.');
		}
		return null;
	}

	/** Load web pages + link stats for domain DIDs (canonical + legacy aliases). */
	async function loadDomainPages() {
		domainPagesLoading = true;
		const didCandidates = domainDidCandidatesFromDid(did);
		if (didCandidates.length === 0) {
			domainPagesLoaded = true;
			domainPagesLoading = false;
			return;
		}
		const domainHint = domainHintFromDid(did);
		const domainWhere = domainHint ? `domain = ${sqlString(domainHint)} AND ` : '';
		const ownerDidWhere = didCandidates
			.map((candidateDid) => `(owner_did = ${sqlString(candidateDid)} OR owner_did LIKE ${sqlString(`${candidateDid}:%`)})`)
			.join(' OR ');
		try {
			const [pageRows, countRows] = await Promise.all([
				graphSql<Record<string, unknown>>(`
					SELECT url, title, domain, outlink_count, content_type
					FROM vertex_page
					WHERE ${domainWhere}(${ownerDidWhere})
					LIMIT 50
				`).catch(() => []),
				domainHint
					? graphSql<Record<string, unknown>>(`
						SELECT page_count AS cnt
						FROM view_cc_domain_page_count_canonical
						WHERE domain = ${sqlString(domainHint)}
						LIMIT 1
					`).catch(() => [])
					: graphSql<Record<string, unknown>>(`
						SELECT count(*) AS cnt
						FROM vertex_page
						WHERE ${domainWhere}(${ownerDidWhere})
					`).catch(() => []),
			]);
			domainPages = pageRows.map((r) => ({
				url: String(r.url ?? ''),
				title: String(r.title ?? ''),
				domain: String(r.domain ?? ''),
				outlink_count: Number(r.outlink_count ?? 0),
				contentType: r.content_type ? String(r.content_type) : undefined,
			})).filter((p) => p.url);
			domainPageCount = Number(countRows[0]?.cnt ?? 0);
			// Build graph nodes from pages
			if (domainPages.length > 0) {
				const pageNodes = domainPages.slice(0, 20).map((p) => ({
					id: p.url,
					label: p.title || new URL(p.url).pathname.slice(0, 40),
					nsPrefix: 'PAGE',
					description: p.url,
				}));
				const pageEdges = pageNodes.map((n) => ({
					source: did,
					target: n.id,
					rel: 'HOSTS_PAGE',
				}));
				knowledgeGraph = {
					nodes: [{ id: did, label: did.split(':').pop() ?? did, nsPrefix: 'DOM', description: '' }, ...pageNodes],
					edges: pageEdges,
				};
				neighbors = pageNodes.map((n) => ({
					nodeId: n.id, label: n.label, nsPrefix: 'PAGE', rel: 'HOSTS_PAGE', description: n.description,
				}));
			}
		} catch (e) {
			console.warn('loadDomainPages failed', e);
		} finally {
			domainPagesLoaded = true;
			domainPagesLoading = false;
		}
	}

	async function togglePageDetail(url: string) {
		if (expandedPageUrl === url) { expandedPageUrl = null; expandedWetText = ''; return; }
		expandedPageUrl = url; expandedWetText = ''; expandedWetLoading = true;
		try {
			const rows = await graphSql<Record<string, unknown>>(`
				SELECT markdown, chunk_index
				FROM vertex_wet_chunk
				WHERE url = ${sqlString(url)}
				ORDER BY chunk_index
				LIMIT 20
			`);
			expandedWetText = rows.map((r) => String(r.markdown ?? '')).join('\n\n');
		} catch (e) { expandedWetText = '(テキスト取得失敗)'; console.warn('loadWetText failed', e); }
		finally { expandedWetLoading = false; }
	}

	async function loadGraph() {
		neighborsLoading = true;
		try {
			const viewerDid = await getCurrentDID().catch((error) => {
				console.warn('[silent-fail] AgentProfile.svelte: getCurrentDID failed', error);
				return null;
			});
			const primary = await atProcedure<any>('com.etzhayyim.pds.getEntityGraph', {
				mode: 'knowledgeGraph',
				did,
				limit: 150,
				useGraphRag: true,
				graphRagK: 12,
			}).catch((error) => {
				console.warn('[silent-fail] AgentProfile.svelte: primary graph fetch failed', error);
				return null;
			});
			const hasPrimaryNeighbors = Array.isArray(primary?.neighbors) && primary.neighbors.length > 0;
			if (hasPrimaryNeighbors) {
				neighbors = primary.neighbors.map((row: Record<string, unknown>) => ({
					nodeId: String(row.nodeId ?? ''),
					label: String(row.label ?? row.nodeId ?? ''),
					description: String(row.description ?? ''),
					nsPrefix: String(row.nsPrefix ?? 'KNW'),
					rel: String(row.rel ?? 'RELATED_TO'),
				}));
				const visibleRows = neighbors.map((n) => ({
					nodeId: n.nodeId,
					label: n.label,
					description: n.description,
					nsPrefix: n.nsPrefix,
					rel: n.rel,
				}));
				knowledgeGraph = buildKnowledgeGraph(did, visibleRows);
				knowledgeAccessSummary = {
					viewerDid: primary?.access?.viewerDid ?? viewerDid ?? undefined,
					viewerRoles: Array.isArray(primary?.access?.viewerRoles) ? primary.access.viewerRoles : [],
					visibleCount: Number(primary?.access?.visibleCount ?? neighbors.length),
					totalCount: Number(primary?.access?.totalCount ?? neighbors.length),
				};
			} else {
				neighbors = [];
				knowledgeGraph = { nodes: [], edges: [] };
				knowledgeAccessSummary = {
					viewerDid: viewerDid ?? undefined,
					viewerRoles: [],
					visibleCount: 0,
					totalCount: 0,
				};
			}
		} catch (e) { console.warn('agent profile: loadGraph failed', e); neighbors = []; }
		finally { neighborsLoading = false; neighborsLoaded = true; }
	}

	async function loadFollows() {
		followsLoading = true;
		try {
			const [followsRes, followersRes] = await Promise.allSettled([
				getFollows(did, { limit: 50 }),
				getFollowers(did, { limit: 50 }),
			]);
			follows = followsRes.status === 'fulfilled' ? (followsRes.value.follows ?? []) : [];
			followers = followersRes.status === 'fulfilled' ? (followersRes.value.followers ?? []) : [];
		} catch (e) { console.warn('agent profile: loadFollows failed', e); }
		finally { followsLoading = false; followsLoaded = true; }
	}

	let roleBindings = $state<any[]>([]);

	async function loadGovernance() {
		governanceLoading = true;
		try {
			const hostFromDid = did.startsWith('did:web:') ? did.replace(/^did:web:/, '').split(':')[0] : '';
			const candidateNanoid = actor.nanoid ?? hostFromDid.replace(/\.etzhayyim\.ai$/, '');
			const didCandidates = Array.from(
				new Set([
					did,
					actor.did ?? '',
					hostFromDid ? `did:web:${hostFromDid}` : '',
					hostFromDid ? `did:web:${hostFromDid.replace(/\.etzhayyim\.ai$/, '')}.etzhayyim.com` : '',
				].filter(Boolean)),
			);
			const governanceRows = await Promise.all([
				Promise.all(didCandidates.map((candidateDid) =>
					graphSql<Record<string, unknown>>(`
						SELECT value_json
						FROM vertex_agent_governance_rule
						WHERE repo = ${sqlString(candidateDid)}
						LIMIT 50
					`).catch(() => []),
				)).then((batches) => batches.flat()),
				graphSql<Record<string, unknown>>(`
					SELECT value_json
					FROM vertex_agent_role_binding
					WHERE app_id = ${sqlString(candidateNanoid)}
					LIMIT 50
				`).catch(() => []),
				Promise.all(didCandidates.map((candidateDid) =>
					graphSql<Record<string, unknown>>(`
						SELECT vertex_id, label, name, kind, standard
						FROM vertex_governance
						WHERE repo = ${sqlString(candidateDid)}
							OR owner_did = ${sqlString(candidateDid)}
						LIMIT 100
					`).catch(() => []),
				)).then((batches) => batches.flat()),
				Promise.all(didCandidates.map((candidateDid) =>
					graphSql<Record<string, unknown>>(`
						SELECT e.label AS rel, e.dst_vid AS did, a.display_name AS display_name, a.handle AS handle
						FROM edge_governance e
						LEFT JOIN vertex_actor a ON a.did = e.dst_vid
						WHERE e.src_vid = ${sqlString(candidateDid)}
							AND e.dst_vid LIKE 'did:%'
						LIMIT 100
					`).catch(() => []),
				)).then((batches) => batches.flat()),
			]);
			const govRows = governanceRows[2].map((row) => ({
				label: String(row.label ?? 'GovernancePolicy'),
				name: String(row.name ?? ''),
				kind: String(row.kind ?? ''),
				standard: String(row.standard ?? ''),
				rel: 'GovernedBy',
			})).filter((row) => row.name || row.kind || row.standard);
			const depsRows = governanceRows[3].map((row) => ({
				did: String(row.did ?? ''),
				name: String(row.display_name ?? row.handle ?? row.did ?? ''),
				relationship: String(row.rel ?? 'GovernedBy'),
				label: 'Actor',
			})).filter((row) => row.did && !didCandidates.includes(row.did));
			const raciRows = governanceRows[0].map((row) => {
				try {
					const parsed = JSON.parse(String(row.value_json ?? '{}'));
					return { ...parsed, kind: 'raci', label: 'GovernanceRule' };
				} catch {
					return null;
				}
			}).filter(Boolean) as any[];
			roleBindings = governanceRows[1].map((row) => {
				try {
					return JSON.parse(String(row.value_json ?? '{}'));
				} catch {
					return null;
				}
			}).filter(Boolean) as any[];
			const uniqueByKey = (rows: any[], keyFn: (r: any) => string) => {
				const m = new Map<string, any>();
				for (const row of rows) {
					const k = keyFn(row);
					if (!m.has(k)) m.set(k, row);
				}
				return Array.from(m.values());
			};
			const mergedGovRows = uniqueByKey(
				govRows,
				(r: any) => `${r.rel ?? ''}|${r.label ?? ''}|${r.name ?? ''}|${r.type ?? ''}|${r.standard ?? ''}`,
			);
			const mergedRaciRows = uniqueByKey(
				raciRows.map((r: any) => ({ ...r, kind: 'raci', label: 'GovernanceRule' })),
				(r: any) => `${r.command ?? ''}|${r.bpmn_task_id ?? ''}|${r.ocel_event_type ?? ''}`,
			);
			governanceData = {
				governance: [
					...mergedGovRows.filter((r: any) =>
						r.rel === 'GovernedBy' ||
						r.rel === 'HAS_GOVERNANCE' ||
						r.label === 'GovernancePolicy' ||
						r.label === 'Policy' ||
						r.label === 'Governance' ||
						r.kind === 'governance',
					),
					...mergedRaciRows,
				],
				compliance: mergedGovRows.filter((r: any) =>
					r.rel === 'CompliesWith' ||
					r.rel === 'IMPLEMENTS' ||
					r.label === 'GovernancePolicy' ||
					r.label === 'ComplianceStandard' ||
					r.label === 'Standard' ||
					r.kind === 'compliance',
				),
				deps: depsRows,
			};
		} catch (e) { console.warn('agent profile: loadGovernance failed', e); }
		finally { governanceLoading = false; governanceLoaded = true; }
	}
</script>

<!-- Hero: type-aware rendering (baminiku / iframe / org-banner / status / app-card / none) -->
<div in:fade={staggerFade(0, { duration: 300 })}>
	{#if heroKind !== 'none'}
		<div class="px-2 pt-2">
			{#if heroKind === 'game' && appPreview?.embedUrl}
				<!-- No sandbox: WebGPU requires full GPU access which sandbox blocks. Cross-origin iframe provides isolation. -->
				<iframe
					src={appPreview.embedUrl}
					class="w-full rounded-xl"
					style="aspect-ratio:9/16; max-height:80vh; border:none; background:#000"
					title={actor.name ?? 'Game'}
					allow="autoplay; gamepad; fullscreen; pointer-lock; xr-spatial-tracking"
					referrerpolicy="strict-origin-when-cross-origin"
				></iframe>
			{:else if heroKind === 'iframe' && appPreview?.embedUrl}
				<iframe
					src={appPreview.embedUrl}
					class="w-full rounded-xl"
					style="aspect-ratio:4/3; max-height:70vh; border:none; background:#000"
					title={actor.name ?? 'App'}
					sandbox="allow-scripts allow-forms allow-popups"
					allow="autoplay"
					referrerpolicy="strict-origin-when-cross-origin"
				></iframe>
			{:else if heroKind === 'baminiku'}
				<LiveStage {did} agentName={actor.name ?? 'Agent'} nanoid={actor.nanoid} />
			{:else if heroKind === 'org-banner'}
				<!-- Organization banner: gradient + name + member count -->
				<div class="w-full rounded-xl bg-gradient-to-br from-indigo-600 via-purple-600 to-blue-700 p-6" style="min-height:120px">
					<div class="flex items-end gap-4">
						{#if actor.avatar}
							<img src={actor.avatar} alt={actor.name ?? ''} class="h-16 w-16 rounded-2xl object-cover ring-2 ring-white/20" />
						{:else}
							<div class="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/10 text-2xl font-black text-white">
								{(actor.name ?? '?').slice(0, 2).toUpperCase()}
							</div>
						{/if}
						<div class="flex-1 min-w-0 pb-1">
							<h2 class="text-[20px] font-black text-white leading-tight truncate">{actor.name ?? 'Organization'}</h2>
							{#if actor.description}
								<p class="text-[13px] text-white/70 line-clamp-1 mt-0.5">{actor.description}</p>
							{/if}
						</div>
					</div>
				</div>
			{:else if heroKind === 'status'}
				<!-- System status hero: dark card with status indicator -->
				<div class="w-full rounded-xl bg-[#0d1117] border border-[#30363d] p-5" style="min-height:100px">
					<div class="flex items-center gap-3">
						<div class="h-3 w-3 rounded-full bg-emerald-400 animate-pulse"></div>
						<span class="text-[14px] font-bold text-emerald-400">Operational</span>
					</div>
					<h2 class="mt-2 text-[17px] font-black text-white truncate">{actor.name ?? 'System'}</h2>
					{#if actor.version}
						<span class="text-[12px] font-mono text-[#8b949e]">v{actor.version}</span>
					{/if}
				</div>
			{:else if heroKind === 'app-card'}
				<!-- Service app card: icon + name + description -->
				<div class="w-full rounded-xl bg-gradient-to-br from-[#1a1a2e] to-[#16213e] border border-[#30363d] p-5" style="min-height:100px">
					<div class="flex items-center gap-3">
						{#if actor.avatar}
							<img src={actor.avatar} alt="" class="h-12 w-12 rounded-xl object-cover" />
						{:else}
							<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-lg font-black text-white">
								{(actor.name ?? '?').slice(0, 2).toUpperCase()}
							</div>
						{/if}
						<div class="flex-1 min-w-0">
							<h2 class="text-[17px] font-black text-white truncate">{actor.name ?? 'Service'}</h2>
							{#if actor.description}
								<p class="text-[13px] text-white/60 line-clamp-2 mt-0.5">{actor.description}</p>
							{/if}
						</div>
					</div>
					{#if tools.length > 0}
						<div class="mt-3 flex flex-wrap gap-1.5">
							{#each tools.slice(0, 5) as tool}
								<span class="rounded-full bg-white/10 px-2.5 py-0.5 text-[11px] text-white/70">{tool}</span>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
		</div>
	{/if}

	{#if heroKind !== 'baminiku'}
		<ProjectorGuestChat {did} agentName={actor.name ?? 'Agent'} />
	{/if}

	<!-- Agent info bar (compact, below stage) -->
	<div class="px-4 pt-3">
		<div class="flex items-center gap-3">
			{#if actor.avatar}
				<img src={actor.avatar} alt={actor.name ?? 'Agent'} class="h-10 w-10 rounded-xl object-cover" />
			{:else}
				<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-sm font-black text-white">
					{(actor.name ?? '?').slice(0, 2).toUpperCase()}
				</div>
			{/if}
			<div class="flex-1 min-w-0">
				<div class="flex items-center gap-2">
					<h1 class="text-[17px] font-black text-gv2-text-primary leading-tight truncate">
						{actor.name ?? 'Agent'}
					</h1>
					<Badge value="Agent" variant="accent" />
					{#if performer.performerType}
						<Badge value={performer.performerType === 'person' ? '🧑 Person' : performer.performerType === 'organization' ? '🏛 Organization' : performer.performerType === 'system' ? '🔧 System' : '⚙ Service'} variant={performer.performerType === 'system' ? 'warning' : performer.performerType === 'organization' ? 'accent' : 'default'} />
					{/if}
				</div>
				<div class="text-[12px] font-mono text-gv2-text-muted truncate">
					{did}
				</div>
				<p class="mt-1 text-[13px] text-gv2-text-secondary line-clamp-2">{roleSubtitle}</p>
			</div>
			{#if $isSignedIn}
				<div class="flex items-center gap-2 flex-shrink-0">
					<button
						type="button"
						class="min-h-[36px] rounded-full px-4 py-1.5 text-[13px] font-bold tap-target-44 touch-manipulation active:opacity-80 {following ? 'border border-gv2-border text-gv2-text-primary' : 'border border-[#1185FE] text-[#1185FE]'}"
						onclick={handleFollow}
						disabled={followBusy}
					>
						{followBusy ? '...' : following ? 'フォロー中' : 'フォロー'}
					</button>
					<button
						type="button"
						class="min-h-[36px] rounded-full px-4 py-1.5 text-[13px] font-bold tap-target-44 touch-manipulation active:opacity-80 bg-[#1185FE] text-white"
						onclick={handleInstall}
						disabled={installBusy}
					>
						{installBusy ? '接続中...' : 'メッセージ'}
					</button>
					{#if isContractableUtility}
						<button
							type="button"
							class="min-h-[36px] rounded-full px-4 py-1.5 text-[13px] font-bold tap-target-44 touch-manipulation active:opacity-80 bg-emerald-600 text-white"
							onclick={handleContract}
							disabled={contractBusy}
						>
							{contractBusy ? '処理中...' : '契約'}
						</button>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Stats row -->
		<div class="mt-2 flex items-center gap-4 text-[13px]">
			<button type="button" class="hover:underline" onclick={() => { activeTab = 'posts'; }}>
				<span class="font-bold text-gv2-text-primary">{postsCountDisplay}</span>
				<span class="text-gv2-text-muted">投稿</span>
			</button>
			<button type="button" class="hover:underline" onclick={() => { activeTab = 'follows'; }}>
				<span class="font-bold text-gv2-text-primary">{followersCountDisplay}</span>
				<span class="text-gv2-text-muted">フォロワー</span>
			</button>
			<button type="button" class="hover:underline" onclick={() => { activeTab = 'follows'; }}>
				<span class="font-bold text-gv2-text-primary">{followsCountDisplay}</span>
				<span class="text-gv2-text-muted">フォロー</span>
			</button>
			<button type="button" class="hover:underline" onclick={() => { activeTab = 'graph'; }}>
				<span class="font-bold text-gv2-text-primary">{knowledgeCount}</span>
				<span class="text-gv2-text-muted">ナレッジ</span>
			</button>
		</div>

		{#if gccBalanceFormatted}
			<div class="mt-3 flex items-center gap-3 rounded-2xl border border-amber-500/20 bg-gradient-to-r from-amber-500/8 to-yellow-500/8 px-4 py-3" transition:fade={{ duration: 200 }}>
				<div class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-amber-400 text-[16px] font-bold select-none">G</div>
				<div class="min-w-0 flex-1">
					<p class="text-[13px] text-gv2-text-muted leading-tight">GCC トークン残高</p>
					<p class="text-[17px] font-bold text-amber-400 leading-tight">{gccBalanceFormatted}</p>
				</div>
				{#if gccSmartAccount}
					<a href="https://geth.etzhayyim.com" target="_blank" rel="noopener noreferrer"
						class="flex-shrink-0 rounded-full bg-amber-500/15 px-3 py-1 text-[12px] font-medium text-amber-400 touch-manipulation active:scale-95 transition-transform"
					>チェーン</a>
				{/if}
			</div>
		{/if}

		{#if isColdStart}
			<div class="mt-3 rounded-xl border border-gv2-border/40 bg-gv2-bg-hover/40 p-3">
				<p class="text-[13px] font-semibold text-gv2-text-primary">この App は初期状態です</p>
				<p class="mt-1 text-[12px] text-gv2-text-muted">まずはメッセージ送信、ツール公開、依存関係の登録から始めてください。</p>
				<div class="mt-2 flex flex-wrap gap-2">
					{#if $isSignedIn}
						<button
							type="button"
							class="rounded-full bg-[#1185FE] px-3 py-1.5 text-[12px] font-bold text-white touch-manipulation active:opacity-80"
							onclick={handleInstall}
							disabled={installBusy}
						>
							{installBusy ? '接続中...' : 'メッセージ'}
						</button>
					{/if}
					<button
						type="button"
						class="rounded-full border border-gv2-border px-3 py-1.5 text-[12px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
						onclick={() => { activeTab = 'tools'; }}
					>
						ツール設定へ
					</button>
					<button
						type="button"
						class="rounded-full border border-gv2-border px-3 py-1.5 text-[12px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
						onclick={() => { activeTab = 'graph'; }}
					>
						ナリッジグラフへ
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>

<!-- Tabs -->
<div class="mt-3 flex overflow-x-auto scrollbar-none border-b border-gv2-border/50">
	{#each agentTabs as tab}
		<button
			type="button"
			class="flex-shrink-0 px-4 py-3 text-[14px] font-semibold touch-manipulation whitespace-nowrap {activeTab === tab.id
				? 'text-gv2-text-primary border-b-2 border-[#1185FE]'
				: 'text-gv2-text-muted active:text-gv2-text-secondary'}"
			onclick={() => { activeTab = tab.id; }}
		>
			{tab.label}
		</button>
	{/each}
</div>

<!-- Tab content -->
<div>
	{#if activeTab === 'app'}
		<div class="p-4 space-y-4">
			{#if appLoading}
				<div class="space-y-3">
					<Skeleton variant="text" class="w-full h-48" />
					<Skeleton variant="text" class="w-2/3" />
				</div>
			{:else if showAppEmbed && appPreview && heroKind !== 'iframe' && heroKind !== 'game'}
				{#if (appPreview.uiType === 'iframe' || appPreview.uiType === 'game') && appPreview.embedUrl}
					<iframe
						src={appPreview.embedUrl}
						class="w-full rounded-xl border border-gv2-border/30"
						style="height:500px"
						title={actor.name ?? (appPreview.uiType === 'game' ? 'Game' : 'App')}
						sandbox="allow-scripts allow-forms allow-popups"
						loading="lazy"
						referrerpolicy="strict-origin-when-cross-origin"
					></iframe>
				{:else}
					<!-- appview: card-only, no interactive embed -->
					<div class="rounded-xl bg-gv2-bg-hover/50 p-4 text-center">
						<p class="text-[14px] text-gv2-text-muted">Protocol Canvas カード (タイムラインで表示)</p>
					</div>
				{/if}
				<button
					type="button"
					class="w-full rounded-xl border border-gv2-border/30 py-3 text-[14px] font-semibold text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
					onclick={() => { showAppEmbed = false; }}
				>
					閉じる
				</button>
			{:else}
				<!-- App preview card -->
				<div class="rounded-xl border border-gv2-border/30 overflow-hidden">
					{#if appPreview?.screenshotCid}
						<img src="https://cdn.etzhayyim.com/cas/{appPreview.screenshotCid}" alt="" class="w-full h-48 object-cover" loading="lazy" />
					{:else}
						<div class="w-full h-32 bg-gradient-to-br from-blue-500/20 to-purple-600/20 flex items-center justify-center">
							<span class="text-4xl">{actor.name?.slice(0, 2).toUpperCase() ?? '??'}</span>
						</div>
					{/if}
					<div class="p-4 space-y-3">
						<div>
							<div class="flex items-center gap-2">
								<h3 class="text-[17px] font-bold text-gv2-text-primary">{actor.name ?? 'Agent'}</h3>
								{#if appPreview?.uiType && appPreview.uiType !== 'appview'}
									<span class="rounded-full bg-blue-500/10 px-2 py-0.5 text-[11px] font-medium text-blue-600 dark:text-blue-400">{appPreview.uiType}</span>
								{/if}
							</div>
							<p class="mt-1 text-[14px] text-gv2-text-secondary leading-relaxed">{actor.description ?? ''}</p>
						</div>
						{#if appPreview?.capabilities?.length}
							<div class="flex flex-wrap gap-1.5">
								{#each appPreview.capabilities as cap}
									<span class="rounded-full bg-purple-500/10 px-2 py-0.5 text-[11px] font-medium text-purple-600 dark:text-purple-400">{cap}</span>
								{/each}
							</div>
						{/if}
						<div class="flex gap-2">
							{#if appPreview && appPreview.uiType !== 'appview'}
								<button
									type="button"
									class="flex-1 rounded-xl bg-[#1185FE] py-3 text-[14px] font-bold text-white touch-manipulation active:opacity-80"
									onclick={async () => {
									if (appPreview && !miniAppCtx) {
										miniAppCtx = await createActorContext({ nanoid: appPreview.nanoid, name: actor.name ?? 'App', ui: 'miniapp' as any });
									}
									showAppEmbed = true;
								}}
								>
									プレビュー
								</button>
							{/if}
							{#if $isSignedIn}
								<button
									type="button"
									class="flex-1 rounded-xl bg-[#1185FE] py-3 text-[14px] font-bold text-white touch-manipulation active:opacity-80"
									onclick={handleInstall}
									disabled={installBusy}
								>
									{installBusy ? '接続中...' : 'メッセージ'}
								</button>
							{/if}
						</div>
					</div>
				</div>
			{/if}
		</div>

	{:else if activeTab === 'overview'}
		<div class="p-4 space-y-4">
			<!-- Tools -->
			{#if tools.length > 0}
				<div>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">Agent ツール</h3>
					<div class="space-y-1.5">
						{#each tools as tool}
							<div class="flex items-center gap-2 rounded-xl bg-gv2-bg-hover/50 px-3 py-2">
								<svg class="h-4 w-4 flex-shrink-0 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
									<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
								</svg>
								<span class="text-[14px] font-medium text-gv2-text-primary">{tool}</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Performer info -->
			{#if performer.name}
				<div>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">DM2 パフォーマー</h3>
					<div class="rounded-xl bg-gv2-bg-hover/50 px-3 py-2.5">
						<div class="text-[15px] font-semibold text-gv2-text-primary">{performer.name}</div>
						{#if performer.description}
							<div class="mt-0.5 text-[13px] text-gv2-text-muted">{performer.description}</div>
						{/if}
						{#if performer.kind}
							<div class="mt-1">
								<span class="rounded-full bg-green-500/10 px-2 py-0.5 text-[11px] font-medium text-green-600 dark:text-green-400">{performer.kind}</span>
							</div>
						{/if}
					</div>
				</div>
			{/if}
		</div>

	{:else if activeTab === 'bpmn'}
		<div class="p-4 space-y-3">
			<div class="flex flex-col gap-1">
				<h3 class="text-sm font-semibold">プロセス (BPMN)</h3>
				{#if bpmnManifest}
					<p class="text-xs text-gray-500">
						{bpmnManifest.processes.length} 件表示{#if bpmnManifest.total > bpmnManifest.processes.length}
							/ 全 {bpmnManifest.total} 件{/if} ·
						<span class="text-amber-600">:synthesized 汎用テンプレート（実プロセスではありません）</span>
					</p>
					<select
						bind:value={selectedBpmnId}
						class="mt-1 w-full max-w-md rounded border border-gray-300 bg-white px-2 py-1 text-sm"
					>
						{#each bpmnManifest.processes as p (p.id)}
							<option value={p.id}>{p.name}{p.company ? ` — ${p.company.replace('org.corp.', '')}` : ''}</option>
						{/each}
					</select>
				{/if}
			</div>
			{#if selectedBpmnProcess}
				{#key selectedBpmnProcess.id}
					{#await import('./BpmnDiagram.svelte')}
						<p class="text-sm text-gray-500">読み込み中…</p>
					{:then { default: BpmnDiagram }}
						<BpmnDiagram xml={selectedBpmnProcess.xml} />
					{:catch}
						<p class="text-sm text-gray-500">BPMN ビューアを読み込めませんでした。</p>
					{/await}
				{/key}
			{:else if bpmnLoading}
				<p class="text-sm text-gray-500">読み込み中…</p>
			{:else}
				<p class="text-sm text-gray-500">表示できる BPMN がありません。</p>
			{/if}
		</div>

	{:else if activeTab === 'capabilities'}
		<div class="p-4 space-y-4">
			<!-- MCP Tools (from PDS gateway) -->
			{#if mcpLoading}
				<div class="space-y-2">
					<Skeleton variant="text" class="w-1/3 h-4" />
					<Skeleton variant="text" class="w-full h-16" />
					<Skeleton variant="text" class="w-full h-16" />
				</div>
			{:else if mcpTools.length > 0}
				<div>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">MCP Tools</h3>
					<div class="space-y-2">
						{#each mcpTools as tool}
							<div class="rounded-xl border border-gv2-border/30 p-3 flex items-start gap-3">
								<div class="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-purple-500/10">
									<svg class="h-4 w-4 text-purple-600 dark:text-purple-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
										<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
									</svg>
								</div>
								<div class="min-w-0 flex-1">
									<div class="text-[14px] font-semibold text-gv2-text-primary font-mono">{tool.name}</div>
									<div class="mt-0.5 text-[13px] text-gv2-text-muted leading-relaxed">{tool.description}</div>
								</div>
								<Badge value="MCP" variant="accent" class="!text-[10px] flex-shrink-0" />
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Graph Capabilities -->
			{#if capabilities.length === 0 && mcpTools.length === 0 && !mcpLoading}
				<div class="flex flex-col items-center gap-3 py-12 text-center">
					<p class="text-[15px] text-gv2-text-muted">ケイパビリティが登録されていません</p>
				</div>
			{:else if capabilities.length > 0}
				{#if mcpTools.length > 0}
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider">Capabilities</h3>
				{/if}
				<div class="space-y-2">
					{#each capabilities as cap}
						<div class="rounded-xl border border-gv2-border/30 p-3">
							<div class="text-[14px] font-semibold text-gv2-text-primary">{cap.id ?? 'capability'}</div>
							{#if cap.description}
								<div class="mt-0.5 text-[13px] text-gv2-text-muted">{cap.description}</div>
							{/if}
							{#if cap.tags}
								<div class="mt-2 flex flex-wrap gap-1">
									{#each parseTags(cap.tags) as tag}
										<span class="rounded-full bg-purple-500/10 px-2 py-0.5 text-[11px] font-medium text-purple-600 dark:text-purple-400">
											{tag}
										</span>
									{/each}
								</div>
							{/if}
							{#if cap.phase}
								<div class="mt-1">
									<span class="text-[11px] text-gv2-text-muted">Phase: {cap.phase}</span>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>

	{:else if activeTab === 'posts'}
		<div>
			{#if postsLoading}
				<div class="p-4 space-y-4">
					{#each { length: 3 } as _}
						<div class="flex gap-3 px-4 py-3">
							<Skeleton variant="circular" class="!h-11 !w-11 flex-shrink-0" />
							<div class="flex-1 space-y-2">
								<Skeleton variant="text" class="w-3/4" />
								<Skeleton variant="text" class="w-full" />
							</div>
						</div>
					{/each}
				</div>
			{:else if feedItems.length === 0}
				<div class="flex flex-col items-center gap-3 py-16 text-center">
					<p class="text-[15px] text-gv2-text-muted">まだ投稿がありません</p>
					<div class="flex flex-wrap justify-center gap-2">
						{#if $isSignedIn}
							<button
								type="button"
								class="rounded-full bg-[#1185FE] px-4 py-2 text-[13px] font-bold text-white touch-manipulation active:opacity-80"
								onclick={handleInstall}
								disabled={installBusy}
							>
								{installBusy ? '接続中...' : 'メッセージを開始'}
							</button>
						{/if}
						<button
							type="button"
							class="rounded-full border border-gv2-border px-4 py-2 text-[13px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
							onclick={() => { activeTab = 'tools'; }}
						>
							ツールを確認
						</button>
					</div>
				</div>
			{:else}
				<div class="divide-y divide-gv2-border/20">
					{#each feedItems as item (item.post.rkey ?? item.post.uri)}
						{@const routeActor = postRouteActor(item.post.author, did)}
						{@const routeRkey = postRkey(item.post)}
						{@const postEmbed = normalizedPostEmbed(item.post)}
						{@const record = item.post.record as Record<string, any> | undefined}
						{@const postText = String(item.post.text ?? record?.text ?? '')}
						{@const postFacets = item.post.facets ?? record?.facets ?? []}
						<button
							type="button"
							class="flex w-full gap-3 px-4 py-3 text-left touch-manipulation active:bg-[var(--gv2-accent)]/5 transition-colors duration-150"
							onclick={() => { if (routeActor && routeRkey) window.location.href = `/profile/${encodeURIComponent(routeActor)}/post/${encodeURIComponent(routeRkey)}`; }}
						>
							<Avatar
								src={item.post.author.avatar || undefined}
								fallback={(item.post.author.displayName || item.post.author.handle || '?').slice(0, 2).toUpperCase()}
								size="md"
								class="!h-11 !w-11 flex-shrink-0"
							/>
							<div class="min-w-0 flex-1">
								<div class="flex items-center gap-1.5">
									<span class="truncate text-[15px] font-bold text-gv2-text-primary">{item.post.author.displayName || item.post.author.handle}</span>
									<span class="flex-shrink-0 text-[14px] text-gv2-text-muted">· {timeAgo(item.post.indexedAt)}</span>
								</div>
								<ContentLabel labels={item.post.labels}>
								<div class="mt-0.5 text-[15px] leading-relaxed text-gv2-text-primary">
									<RichText text={postText} facets={postFacets} />
								</div>
								{#if postEmbed}
									<PostEmbed embed={postEmbed} />
								{/if}
							</ContentLabel>
								<div class="mt-2 flex items-center gap-6 text-gv2-text-muted">
									<div class="flex items-center gap-1">
										<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
										{#if item.post.replyCount}<span class="text-[13px]">{item.post.replyCount}</span>{/if}
									</div>
									<div class="flex items-center gap-1">
										<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 014-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 01-4 4H3" /></svg>
										{#if item.post.repostCount}<span class="text-[13px]">{item.post.repostCount}</span>{/if}
									</div>
									<div class="flex items-center gap-1">
										<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" /></svg>
										{#if item.post.likeCount}<span class="text-[13px]">{item.post.likeCount}</span>{/if}
									</div>
									<div class="flex items-center gap-1">
										<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/></svg>
										{#if item.post.viewCount > 0}<span class="text-[13px]">{item.post.viewCount}</span>{/if}
									</div>
								</div>
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</div>

	{:else if activeTab === 'contract'}
		<div class="p-4 space-y-4">
			{#if !$isSignedIn}
				<div class="flex flex-col items-center gap-3 py-12 text-center">
					<p class="text-[15px] text-gv2-text-muted">ログインして契約プランを確認</p>
				</div>
			{:else}
				<div>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-3">利用可能なプラン</h3>
					{#if did.includes('dk3n7k8p') || did.includes('denki.etzhayyim.com')}
						{@const plans = [
							{ id: 'dk-basic', name: '基本プラン', desc: '従量電灯B相当。一般家庭向け', price: '¥1,200/月' },
							{ id: 'dk-setsuyaku', name: '節約プラン', desc: '深夜割引 + 省エネアドバイス', price: '¥980/月' },
							{ id: 'dk-premium', name: 'プレミアムプラン', desc: '再エネ100% + EV充電割引', price: '¥2,400/月' },
						]}
						<div class="space-y-2">
							{#each plans as plan}
								<div class="rounded-xl border border-gv2-border/30 p-4 flex items-center gap-3">
									<div class="flex-1 min-w-0">
										<div class="text-[15px] font-bold text-gv2-text-primary">{plan.name}</div>
										<div class="text-[13px] text-gv2-text-muted mt-0.5">{plan.desc}</div>
									</div>
									<div class="text-[14px] font-bold text-emerald-500 flex-shrink-0">{plan.price}</div>
								</div>
							{/each}
						</div>
					{:else if did.includes('sd9w2t4r') || did.includes('suido.etzhayyim.com')}
						{@const plans = [
							{ id: 'sd-basic', name: '基本プラン', desc: '一般家庭向け上下水道', price: '¥800/月' },
							{ id: 'sd-setsuyaku', name: '節約プラン', desc: '節水アドバイス + 漏水検知', price: '¥650/月' },
							{ id: 'sd-premium', name: 'プレミアムプラン', desc: '浄水フィルター交換込み + 24h 対応', price: '¥1,600/月' },
						]}
						<div class="space-y-2">
							{#each plans as plan}
								<div class="rounded-xl border border-gv2-border/30 p-4 flex items-center gap-3">
									<div class="flex-1 min-w-0">
										<div class="text-[15px] font-bold text-gv2-text-primary">{plan.name}</div>
										<div class="text-[13px] text-gv2-text-muted mt-0.5">{plan.desc}</div>
									</div>
									<div class="text-[14px] font-bold text-emerald-500 flex-shrink-0">{plan.price}</div>
								</div>
							{/each}
						</div>
					{:else if did.includes('gs5a6s1m') || did.includes('gas.etzhayyim.com')}
						{@const plans = [
							{ id: 'gs-basic', name: '基本プラン', desc: '一般家庭向け都市ガス', price: '¥900/月' },
							{ id: 'gs-setsuyaku', name: '節約プラン', desc: 'ガスファンヒーター割引 + 省エネ診断', price: '¥750/月' },
							{ id: 'gs-premium', name: 'プレミアムプラン', desc: '床暖房割引 + ガス機器保証 + 24h 駆けつけ', price: '¥1,800/月' },
						]}
						<div class="space-y-2">
							{#each plans as plan}
								<div class="rounded-xl border border-gv2-border/30 p-4 flex items-center gap-3">
									<div class="flex-1 min-w-0">
										<div class="text-[15px] font-bold text-gv2-text-primary">{plan.name}</div>
										<div class="text-[13px] text-gv2-text-muted mt-0.5">{plan.desc}</div>
									</div>
									<div class="text-[14px] font-bold text-emerald-500 flex-shrink-0">{plan.price}</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>

				<!-- Provider list (Japan default) -->
				<div>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-3">提携プロバイダー (日本)</h3>
					{#if did.includes('dk3n7k8p') || did.includes('denki.etzhayyim.com')}
						{@const jpProviders = [
							{ name: '東京電力 (TEPCO)', region: '関東' },
							{ name: '関西電力', region: '関西' },
							{ name: '中部電力', region: '中部' },
							{ name: '東北電力', region: '東北' },
							{ name: '九州電力', region: '九州' },
							{ name: '中国電力', region: '中国' },
							{ name: '北海道電力', region: '北海道' },
							{ name: '四国電力', region: '四国' },
							{ name: '北陸電力', region: '北陸' },
							{ name: '沖縄電力', region: '沖縄' },
						]}
						<div class="grid grid-cols-2 gap-2">
							{#each jpProviders as p}
								<div class="rounded-lg bg-gv2-bg-hover/50 px-3 py-2">
									<div class="text-[13px] font-semibold text-gv2-text-primary truncate">{p.name}</div>
									<div class="text-[11px] text-gv2-text-muted">{p.region}</div>
								</div>
							{/each}
						</div>
					{:else if did.includes('sd9w2t4r') || did.includes('suido.etzhayyim.com')}
						{@const jpProviders = [
							{ name: '東京都水道局', region: '東京' },
							{ name: '大阪市水道局', region: '大阪' },
							{ name: '横浜市水道局', region: '横浜' },
							{ name: '名古屋市上下水道局', region: '名古屋' },
							{ name: '札幌市水道局', region: '札幌' },
							{ name: '福岡市水道局', region: '福岡' },
							{ name: '神戸市水道局', region: '神戸' },
							{ name: '京都市上下水道局', region: '京都' },
							{ name: '仙台市水道局', region: '仙台' },
							{ name: '広島市水道局', region: '広島' },
						]}
						<div class="grid grid-cols-2 gap-2">
							{#each jpProviders as p}
								<div class="rounded-lg bg-gv2-bg-hover/50 px-3 py-2">
									<div class="text-[13px] font-semibold text-gv2-text-primary truncate">{p.name}</div>
									<div class="text-[11px] text-gv2-text-muted">{p.region}</div>
								</div>
							{/each}
						</div>
					{:else if did.includes('gs5a6s1m') || did.includes('gas.etzhayyim.com')}
						{@const jpProviders = [
							{ name: '東京ガス', region: '関東' },
							{ name: '大阪ガス (Daigas)', region: '関西' },
							{ name: '東邦ガス', region: '中部' },
							{ name: '西部ガス', region: '九州' },
							{ name: '静岡ガス', region: '静岡' },
							{ name: '北海道ガス', region: '北海道' },
							{ name: '北陸ガス', region: '北陸' },
							{ name: '広島ガス', region: '中国' },
							{ name: '京葉ガス', region: '千葉' },
							{ name: 'INPEX', region: '全国' },
						]}
						<div class="grid grid-cols-2 gap-2">
							{#each jpProviders as p}
								<div class="rounded-lg bg-gv2-bg-hover/50 px-3 py-2">
									<div class="text-[13px] font-semibold text-gv2-text-primary truncate">{p.name}</div>
									<div class="text-[11px] text-gv2-text-muted">{p.region}</div>
								</div>
							{/each}
						</div>
					{/if}
					<p class="mt-2 text-[11px] text-gv2-text-muted">他 30+ 国のプロバイダーにも対応。DM で国名を伝えてください。</p>
				</div>

				<button
					type="button"
					class="w-full rounded-xl bg-emerald-600 py-3 text-[14px] font-bold text-white touch-manipulation active:opacity-80"
					onclick={handleContract}
					disabled={contractBusy}
				>
					{contractBusy ? '処理中...' : 'この Agent と契約する'}
				</button>
			{/if}
		</div>

	{:else if activeTab === 'graph'}
		<div class="p-4">
			{#if neighborsLoading}
				<div class="space-y-3">
					{#each { length: 5 } as _}
						<Skeleton variant="text" class="w-full" />
					{/each}
				</div>

			<!-- Domain DID: Web Pages section -->
			{:else if domainPages.length > 0}
				<div class="mb-4">
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-1">Web Pages</h3>
					<p class="mb-3 text-[12px] text-gv2-text-muted">
						{domainPageCount} pages from Common Crawl
					</p>
				</div>

				<!-- Page list with screenshot + WET detail -->
				<div class="space-y-2 mb-6">
					{#each domainPages as pg (pg.url)}
						<div class="rounded-xl bg-gv2-bg-hover/50 overflow-hidden">
							<button type="button" onclick={() => togglePageDetail(pg.url)} class="flex items-start gap-3 w-full px-3 py-2.5 text-left touch-manipulation active:bg-gv2-bg-hover">
								{#if pg.screenshotBlobRef}
									<img src="/cdn/blob/{pg.screenshotBlobRef}" alt="" class="w-10 h-14 shrink-0 rounded-md object-cover object-top bg-gv2-bg-hover" loading="lazy" />
								{:else}
									<div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400">
										{#if pg.contentType?.includes('pdf')}
											<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
										{:else}
											<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
										{/if}
									</div>
								{/if}
								<div class="min-w-0 flex-1">
									<div class="truncate text-[14px] font-medium text-gv2-text-primary">{pg.title || new URL(pg.url).pathname}</div>
									<div class="truncate text-[12px] text-gv2-text-muted font-mono">{pg.url}</div>
									<div class="flex gap-2 mt-0.5 text-[11px] text-gv2-text-muted">
										{#if pg.contentType?.includes('pdf')}<span class="text-red-400">PDF</span>{/if}
										{#if pg.outlink_count > 0}<span>{pg.outlink_count} outlinks</span>{/if}
										{#if pg.screenshotBlobRef}<span class="text-emerald-400">WebP</span>{/if}
									</div>
								</div>
								<svg class="h-4 w-4 shrink-0 text-gv2-text-muted transition-transform {expandedPageUrl === pg.url ? 'rotate-180' : ''}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
							</button>
							{#if expandedPageUrl === pg.url}
								<div class="px-3 pb-3 space-y-3 border-t border-gv2-border/20">
									{#if pg.screenshotBlobRef}
										<img src="/cdn/blob/{pg.screenshotBlobRef}" alt="Screenshot of {pg.title}" class="w-full rounded-lg mt-3" loading="lazy" />
									{/if}
									{#if expandedWetLoading}
										<div class="text-[12px] text-gv2-text-muted animate-pulse mt-2">Loading text...</div>
									{:else if expandedWetText}
										<div class="text-[13px] text-gv2-text-secondary leading-relaxed mt-2 max-h-[300px] overflow-y-auto whitespace-pre-wrap">{expandedWetText}</div>
									{/if}
									<a href={pg.url} target="_blank" rel="noopener noreferrer" class="inline-block text-[12px] text-blue-400 mt-1">Open original</a>
								</div>
							{/if}
						</div>
					{/each}
				</div>

				<!-- Graph visualization -->
				{#if knowledgeGraph.nodes.length > 1}
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">Link Graph</h3>
					<div class="rounded-xl border border-gv2-border/30 bg-gv2-bg-hover/30 p-2 mb-4">
						<div class="h-[280px] w-full overflow-hidden rounded-lg">
							{@html knowledgeGraphSvg}
						</div>
					</div>
				{/if}

			{:else if !neighborsLoaded}
				<!-- loadGraph() not yet invoked — show skeleton to avoid false empty state -->
				<div class="space-y-3">
					{#each { length: 5 } as _}
						<Skeleton variant="text" class="w-full" />
					{/each}
				</div>
			{:else if neighbors.length === 0}
				<div class="flex flex-col items-center gap-3 py-12 text-center">
					<p class="text-[15px] text-gv2-text-muted">公開可能なナリッジグラフがありません</p>
					<p class="text-[12px] text-gv2-text-muted">閲覧権限は RACI / RBAC に基づいて評価されます</p>
					<button
						type="button"
						class="rounded-full border border-gv2-border px-4 py-2 text-[13px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
						onclick={() => { activeTab = 'governance'; }}
					>
						ガバナンスを確認
					</button>
				</div>
			{:else}
				<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">ナリッジグラフ</h3>
				<p class="mb-3 text-[12px] text-gv2-text-muted">
					表示: {knowledgeAccessSummary.visibleCount} / {knowledgeAccessSummary.totalCount}
					{#if knowledgeAccessSummary.viewerRoles.length > 0}
						· role: {knowledgeAccessSummary.viewerRoles.join(', ')}
					{/if}
				</p>
				<div class="rounded-xl border border-gv2-border/30 bg-gv2-bg-hover/30 p-2">
					<div class="h-[280px] w-full overflow-hidden rounded-lg">
						{@html knowledgeGraphSvg}
					</div>
				</div>
				<h4 class="mt-4 mb-2 text-[12px] font-semibold text-gv2-text-muted uppercase tracking-wider">Graph Data: Nodes ({knowledgeGraph.nodes.length})</h4>
				<div class="space-y-2">
					{#each knowledgeGraph.nodes as node (node.id)}
						<a
							href="/profile/{encodeURIComponent(node.id)}"
							class="flex items-center gap-3 rounded-xl bg-gv2-bg-hover/50 px-3 py-2.5 no-underline touch-manipulation active:bg-gv2-bg-hover"
						>
							<div class="flex h-9 w-9 items-center justify-center rounded-lg bg-gv2-bg-hover text-[12px] font-bold text-gv2-text-muted">
								{(node.nsPrefix ?? '?').slice(0, 3).toUpperCase()}
							</div>
							<div class="min-w-0 flex-1">
								<div class="truncate text-[14px] font-medium text-gv2-text-primary">{node.label || node.id}</div>
								<div class="text-[12px] font-mono text-gv2-text-muted truncate">{node.id}</div>
								{#if node.description}
									<div class="text-[12px] text-gv2-text-muted truncate">{node.description}</div>
								{/if}
							</div>
						</a>
					{/each}
				</div>
				<h4 class="mt-4 mb-2 text-[12px] font-semibold text-gv2-text-muted uppercase tracking-wider">Graph Data: Edges ({knowledgeGraph.edges.length})</h4>
				<div class="space-y-1.5">
					{#each knowledgeGraph.edges as edge, i (`${edge.source}-${edge.target}-${edge.rel}-${i}`)}
						<div class="rounded-lg bg-gv2-bg-hover/50 px-3 py-2 text-[12px] text-gv2-text-secondary">
							<span class="font-mono text-gv2-text-primary">{edge.rel}</span>
							<span class="mx-1 text-gv2-text-muted">:</span>
							<span class="font-mono">{edge.source.replace('did:web:', '')}</span>
							<span class="mx-1 text-gv2-text-muted">→</span>
							<span class="font-mono">{edge.target.replace('did:web:', '')}</span>
						</div>
					{/each}
				</div>
			{/if}
		</div>

	{:else if activeTab === 'tools'}
		<div class="p-4 space-y-4">
			{#if mcpLoading}
				<div class="space-y-2">
					<Skeleton variant="text" class="w-1/3 h-4" />
					<Skeleton variant="text" class="w-full h-16" />
					<Skeleton variant="text" class="w-full h-16" />
				</div>
			{:else if mcpTools.length === 0 && tools.length === 0}
				<div class="flex flex-col items-center gap-3 py-12 text-center">
					<svg class="h-12 w-12 text-gv2-text-muted/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" /></svg>
					<p class="text-[15px] text-gv2-text-muted">ツールが登録されていません</p>
					<button
						type="button"
						class="rounded-full border border-gv2-border px-4 py-2 text-[13px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
						onclick={() => { activeTab = 'graph'; }}
					>
						ナリッジグラフを確認
					</button>
				</div>
			{:else}
				<!-- MCP Tools -->
				{#if mcpTools.length > 0}
					<div>
						<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">MCP Tools</h3>
						<div class="space-y-2">
							{#each mcpTools as tool}
								<div class="rounded-xl border border-gv2-border/30 p-3 flex items-start gap-3">
									<div class="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-purple-500/10">
										<svg class="h-4 w-4 text-purple-600 dark:text-purple-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
											<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
										</svg>
									</div>
									<div class="min-w-0 flex-1">
										<div class="text-[14px] font-semibold text-gv2-text-primary font-mono">{tool.name}</div>
										<div class="mt-0.5 text-[13px] text-gv2-text-muted leading-relaxed">{tool.description}</div>
									</div>
									<Badge value="MCP" variant="accent" class="!text-[10px] flex-shrink-0" />
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Agent Tools -->
				{#if tools.length > 0}
					<div>
						<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">Agent ツール</h3>
						<div class="space-y-1.5">
							{#each tools as tool}
								<div class="flex items-center gap-2 rounded-xl bg-gv2-bg-hover/50 px-3 py-2">
									<svg class="h-4 w-4 flex-shrink-0 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
										<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
									</svg>
									<span class="text-[14px] font-medium text-gv2-text-primary">{tool}</span>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Graph Capabilities -->
				{#if capabilities.length > 0}
					<div>
						<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">ケイパビリティ</h3>
						<div class="space-y-2">
							{#each capabilities as cap}
								<div class="rounded-xl border border-gv2-border/30 p-3">
									<div class="text-[14px] font-semibold text-gv2-text-primary">{cap.id ?? 'capability'}</div>
									{#if cap.description}
										<div class="mt-0.5 text-[13px] text-gv2-text-muted">{cap.description}</div>
									{/if}
									{#if cap.tags}
										<div class="mt-2 flex flex-wrap gap-1">
											{#each parseTags(cap.tags) as tag}
												<Chip label={tag} />
											{/each}
										</div>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}
			{/if}
		</div>

	{:else if activeTab === 'governance'}
		<div class="p-4 space-y-4">
			{#if governanceLoading}
				<div class="space-y-3">
					{#each { length: 4 } as _}
						<Skeleton variant="text" class="w-full" />
					{/each}
				</div>
			{:else}
				<!-- RACI/RBAC Governance Rules -->
				{@const raciRules = governanceData.governance.filter((r: any) => r.label === 'GovernanceRule' && r.command)}
				{@const policyRules = governanceData.governance.filter((r: any) => r.label !== 'GovernanceRule')}
				{#if raciRules.length > 0}
					<div>
						<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">RACI / RBAC ガバナンス</h3>
						<div class="space-y-2">
							{#each raciRules as rule}
								{@const raci = (() => { try { return JSON.parse(rule.raci_json || '[]'); } catch { return []; } })()}
								{@const approval = (() => { try { return rule.approval_json ? JSON.parse(rule.approval_json) : null; } catch { return null; } })()}
								<div class="rounded-xl border border-gv2-border/30 p-3">
									<div class="flex items-center gap-2">
										<svg class="h-4 w-4 flex-shrink-0 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
										<span class="text-[14px] font-semibold text-gv2-text-primary font-mono">{rule.command}</span>
									</div>
									{#if raci.length > 0}
										<div class="mt-2 space-y-1">
											{#each raci as a}
												{@const boundDids = roleBindings.filter((rb: any) => rb.role === a.value)}
												<div class="flex flex-wrap items-center gap-1.5">
													<span class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold
														{a.role === 'responsible' ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400' :
														 a.role === 'accountable' ? 'bg-red-500/10 text-red-600 dark:text-red-400' :
														 a.role === 'consulted' ? 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400' :
														 'bg-gray-500/10 text-gray-600 dark:text-gray-400'}">
														<span class="uppercase">{(a.role ?? '')[0]}</span>
														<span>{a.value}</span>
													</span>
													{#if boundDids.length > 0}
														<span class="text-[11px] text-gv2-text-muted">→</span>
														{#each boundDids as bd}
															<a href="/profile/{encodeURIComponent(bd.did)}" class="inline-flex items-center gap-1 rounded-md bg-emerald-500/10 px-2 py-0.5 text-[11px] font-mono text-emerald-600 dark:text-emerald-400 no-underline hover:bg-emerald-500/20">
																{bd.did.replace('did:web:', '').replace('.etzhayyim.com', '')}
															</a>
														{/each}
													{:else}
														<span class="text-[10px] text-gv2-text-muted/50 italic">未割当</span>
													{/if}
												</div>
											{/each}
										</div>
									{/if}
									{#if approval}
										<div class="mt-2 flex items-center gap-1.5 text-[12px] text-gv2-text-muted">
											<svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
											<span>承認必要: Class {['A','B','C','D'][approval.decisionClass] ?? '?'}, {approval.minApprovers}名, リスク: {approval.riskTier}</span>
										</div>
									{/if}
									<div class="mt-1.5 flex flex-wrap gap-1">
										{#if rule.bpmn_task_id}<Chip label="BPMN: {rule.bpmn_task_id}" />{/if}
										{#if rule.ocel_event_type}<Chip label="OCEL: {rule.ocel_event_type}" />{/if}
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Role → DID Bindings -->
				{#if roleBindings.length > 0}
					<div>
						<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">ロール割当 (RBAC)</h3>
						<div class="space-y-1.5">
							{#each roleBindings as rb}
								<div class="flex items-center gap-2 rounded-xl bg-gv2-bg-hover/50 px-3 py-2">
									<span class="inline-flex items-center rounded-md bg-purple-500/10 px-2 py-0.5 text-[11px] font-semibold text-purple-600 dark:text-purple-400">{rb.role}</span>
									<span class="text-[12px] text-gv2-text-muted">→</span>
									<a href="/profile/{encodeURIComponent(rb.did)}" class="text-[13px] font-mono text-emerald-600 dark:text-emerald-400 no-underline hover:underline truncate">{rb.did.replace('did:web:', '')}</a>
									{#if rb.description}
										<span class="text-[11px] text-gv2-text-muted truncate hidden sm:inline">({rb.description})</span>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Tool Governance Policies -->
				{#if policyRules.length > 0}
					<div>
						<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">ガバナンスポリシー</h3>
						<div class="space-y-2">
							{#each policyRules as rule}
								<div class="rounded-xl border border-gv2-border/30 p-3">
									<div class="flex items-center gap-2">
										<svg class="h-4 w-4 flex-shrink-0 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
										<span class="text-[14px] font-semibold text-gv2-text-primary">{rule.name ?? rule.type ?? 'Rule'}</span>
									</div>
									{#if rule.standard}
										<p class="mt-1 text-[12px] font-mono text-gv2-text-muted">{rule.standard}</p>
									{/if}
									{#if rule.kind}
										<div class="mt-1.5"><Chip label={rule.kind} /></div>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Compliance -->
				{#if governanceData.compliance.length > 0}
					<div>
						<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">コンプライアンス</h3>
						<div class="space-y-2">
							{#each governanceData.compliance as item}
								<div class="rounded-xl border border-gv2-border/30 p-3">
									<div class="flex items-center gap-2">
										<svg class="h-4 w-4 flex-shrink-0 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
										<span class="text-[14px] font-semibold text-gv2-text-primary">{item.name ?? item.standard ?? 'Compliance'}</span>
									</div>
									{#if item.status}
										<div class="mt-1.5"><Badge value={item.status} variant={item.status === 'compliant' ? 'accent' : 'warning'} /></div>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Dependencies -->
				{#if governanceData.deps.length > 0}
					<div>
						<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">依存関係 (Deps)</h3>
						<div class="space-y-2">
							{#each governanceData.deps as dep}
								<a
									href="/profile/{encodeURIComponent(dep.did ?? dep.nodeId ?? '')}"
									class="flex items-center gap-3 rounded-xl bg-gv2-bg-hover/50 px-3 py-2.5 no-underline touch-manipulation active:bg-gv2-bg-hover"
								>
									<div class="flex h-9 w-9 items-center justify-center rounded-lg bg-gv2-bg-hover text-[12px] font-bold text-gv2-text-muted">
										{(dep.label ?? dep.type ?? '?').slice(0, 3).toUpperCase()}
									</div>
									<div class="min-w-0 flex-1">
										<div class="truncate text-[14px] font-medium text-gv2-text-primary">{dep.name ?? dep.label ?? dep.nodeId ?? 'Dependency'}</div>
										{#if dep.relationship}
											<div class="text-[12px] text-gv2-text-muted">{dep.relationship}</div>
										{/if}
									</div>
								</a>
							{/each}
						</div>
					</div>
				{/if}

				{#if governanceData.governance.length === 0 && governanceData.compliance.length === 0 && governanceData.deps.length === 0}
					<div class="flex flex-col items-center gap-3 py-12 text-center">
						<svg class="h-12 w-12 text-gv2-text-muted/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
						<p class="text-[15px] text-gv2-text-muted">ガバナンス情報がありません</p>
						<button
							type="button"
							class="rounded-full border border-gv2-border px-4 py-2 text-[13px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
							onclick={() => { activeTab = 'tools'; }}
						>
							ツールを確認
						</button>
					</div>
				{/if}
			{/if}
		</div>

	{:else if activeTab === 'gov'}
		<div class="p-4 space-y-6">
			{#if (actor.complianceFrameworks?.length ?? 0) > 0}
				<section>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">法的枠組み / Constitutional & Statutory Framework</h3>
					<div class="space-y-1.5">
						{#each actor.complianceFrameworks ?? [] as f}
							<div class="rounded-xl border border-gv2-border/30 p-2.5 bg-amber-500/5">
								<div class="flex items-start gap-2">
									<svg class="h-4 w-4 flex-shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
									<div class="text-[13px] text-gv2-text-primary">{f}</div>
								</div>
							</div>
						{/each}
					</div>
				</section>
			{/if}
			{#if actor.dataSourceRef || (actor.ministryCount ?? 0) > 0 || (actor.bpmnCount ?? 0) > 0}
				<div class="rounded-xl border border-gv2-border/30 p-3 bg-gv2-bg-secondary/30 text-[12px] text-gv2-text-muted">
					{#if actor.ministryCount}省庁 {actor.ministryCount} 件 · {/if}
					{#if actor.bpmnCount}BPMN {actor.bpmnCount} 件 · {/if}
					{#if actor.contractCount}法令 {actor.contractCount} 件{/if}
					{#if actor.dataSourceRef}
						<div class="mt-1 font-mono text-[11px] text-gv2-text-muted/70 truncate">{actor.dataSourceRef}</div>
					{/if}
				</div>
			{/if}
			{#if (actor.addresses?.length ?? 0) > 0}
				<section>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">住所 / Addresses</h3>
					<div class="space-y-2">
						{#each actor.addresses ?? [] as a}
							<div class="rounded-xl border border-gv2-border/30 p-3">
								<div class="text-[13px] font-semibold text-gv2-text-primary">{a.label ?? a.kind ?? ''}</div>
								{#if a.streetAddress || a.addressLocality || a.addressRegion || a.postalCode || a.country}
									<div class="text-[12px] text-gv2-text-muted mt-1">
										{[a.streetAddress, a.addressLocality, a.addressRegion, a.postalCode, a.country].filter(Boolean).join(', ')}
									</div>
								{/if}
								{#if a.latlng}
									<a href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(a.latlng)}`} target="_blank" rel="noopener noreferrer" class="text-[11px] text-blue-500 hover:underline font-mono mt-1 inline-block">📍 {a.latlng}</a>
								{/if}
							</div>
						{/each}
					</div>
				</section>
			{/if}
			{#if (actor.contacts?.length ?? 0) > 0}
				<section>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">連絡先 / Contacts</h3>
					<div class="space-y-1.5">
						{#each actor.contacts ?? [] as c}
							<a href={c.uri} target="_blank" rel="noopener noreferrer" class="flex items-start gap-2 rounded-xl border border-gv2-border/30 p-2 hover:bg-gv2-bg-secondary/50 transition-colors">
								<span class="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400">{c.kind ?? ''}</span>
								<div class="flex-1 min-w-0">
									<div class="text-[13px] text-gv2-text-primary truncate">{c.label ?? c.uri ?? ''}</div>
									<div class="text-[11px] text-gv2-text-muted font-mono truncate">{c.uri ?? ''}</div>
								</div>
							</a>
						{/each}
					</div>
				</section>
			{/if}
			{#if (actor.desks?.length ?? 0) > 0}
				<section>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">窓口 / Desks</h3>
					<div class="space-y-2">
						{#each actor.desks ?? [] as d}
							<div class="rounded-xl border border-gv2-border/30 p-3">
								<div class="flex items-start gap-2">
									<span class="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">{d.kind ?? ''}</span>
									<div class="flex-1 min-w-0">
										<div class="text-[13px] font-semibold text-gv2-text-primary">{d.label ?? ''}</div>
										{#if d.basis}<div class="text-[11px] text-gv2-text-muted mt-0.5">根拠: {d.basis}</div>{/if}
										{#if d.uri}<a href={d.uri} target="_blank" rel="noopener noreferrer" class="text-[11px] text-blue-500 hover:underline font-mono block truncate mt-0.5">{d.uri}</a>{/if}
										{#if d.tel}<a href={`tel:${d.tel}`} class="text-[11px] text-blue-500 hover:underline font-mono block mt-0.5">📞 {d.tel}</a>{/if}
									</div>
								</div>
							</div>
						{/each}
					</div>
				</section>
			{/if}
			{#if (actor.procedures?.length ?? 0) > 0}
				<section>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">行政手続き / Procedures</h3>
					<div class="space-y-2">
						{#each actor.procedures ?? [] as p}
							<div class="rounded-xl border border-gv2-border/30 p-3">
								<div class="text-[13px] font-semibold text-gv2-text-primary">{p.title ?? p.id ?? ''}</div>
								{#if p.titleLocal && p.titleLocal !== p.title}<div class="text-[12px] text-gv2-text-muted mt-0.5">{p.titleLocal}</div>{/if}
								<div class="flex flex-wrap items-center gap-1.5 mt-1.5">
									{#if p.authority}<span class="inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] bg-gv2-bg-secondary text-gv2-text-muted">{p.authority}</span>{/if}
									{#if p.basis}<span class="inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] bg-amber-500/10 text-amber-600 dark:text-amber-400">{p.basis}</span>{/if}
									{#if p.bpmnRef || p.bpmn}<a href={`/bpmn-viewer?path=${encodeURIComponent(p.bpmnRef || p.bpmn || '')}`} class="inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] bg-purple-500/10 text-purple-600 dark:text-purple-400 hover:bg-purple-500/20">BPMN</a>{/if}
									{#if p.dmnRef || p.dmn}<a href={`/bpmn-viewer?path=${encodeURIComponent(p.dmnRef || p.dmn || '')}&kind=dmn`} class="inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] bg-teal-500/10 text-teal-600 dark:text-teal-400 hover:bg-teal-500/20">DMN</a>{/if}
									{#if p.formRef || p.form}<a href={(p.formRef || p.form || '').startsWith('http') ? (p.formRef || p.form || '') : `/form-preview?path=${encodeURIComponent(p.formRef || p.form || '')}`} target={(p.formRef || p.form || '').startsWith('http') ? '_blank' : undefined} rel="noopener noreferrer" class="inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] bg-pink-500/10 text-pink-600 dark:text-pink-400 hover:bg-pink-500/20">Form</a>{/if}
									{#if p.xrpcRef}<span class="inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] bg-blue-500/10 text-blue-600 dark:text-blue-400 font-mono">{p.xrpcRef}</span>{/if}
								</div>
								{#if p.portalUri}<a href={p.portalUri} target="_blank" rel="noopener noreferrer" class="text-[11px] text-blue-500 hover:underline font-mono block truncate mt-1">{p.portalUri}</a>{/if}
							</div>
						{/each}
					</div>
				</section>
			{/if}
			{#if (actor.documentTemplates?.length ?? 0) > 0}
				<section>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">書類雛形 / Document Templates</h3>
					<div class="space-y-2">
						{#each actor.documentTemplates ?? [] as d}
							<a href={d.uri ?? '#'} target={d.uri ? '_blank' : undefined} rel="noopener noreferrer" class="block rounded-xl border border-gv2-border/30 p-3 hover:bg-gv2-bg-secondary/50 transition-colors">
								<div class="flex items-start gap-2">
									<svg class="h-4 w-4 flex-shrink-0 text-gv2-text-muted mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6M8 13h8M8 17h8M8 9h2" /></svg>
									<div class="flex-1 min-w-0">
										<div class="text-[13px] font-semibold text-gv2-text-primary">{d.title ?? d.id ?? ''}</div>
										{#if d.titleLocal && d.titleLocal !== d.title}<div class="text-[12px] text-gv2-text-muted mt-0.5">{d.titleLocal}</div>{/if}
										<div class="flex flex-wrap items-center gap-1.5 mt-1">
											{#if d.authority}<span class="inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] bg-gv2-bg-secondary text-gv2-text-muted">{d.authority}</span>{/if}
											{#if d.basis}<span class="inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] bg-amber-500/10 text-amber-600 dark:text-amber-400">{d.basis}</span>{/if}
										</div>
									</div>
								</div>
							</a>
						{/each}
					</div>
				</section>
			{/if}
		</div>

	{:else if activeTab === 'follows'}
		<div class="p-4 space-y-4">
			{#if followsLoading}
				<div class="space-y-3">
					{#each { length: 5 } as _}
						<div class="flex gap-3">
							<Skeleton variant="circular" class="!h-10 !w-10 flex-shrink-0" />
							<div class="flex-1 space-y-2">
								<Skeleton variant="text" class="w-2/3" />
								<Skeleton variant="text" class="w-1/2" />
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<!-- Following -->
				<div>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">フォロー中 ({follows.length})</h3>
					{#if follows.length === 0}
						<p class="text-[13px] text-gv2-text-muted py-4">フォロー中のアカウントはありません</p>
						{#if $isSignedIn && !following}
							<button
								type="button"
								class="rounded-full border border-gv2-border px-4 py-2 text-[13px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
								onclick={handleFollow}
								disabled={followBusy}
							>
								{followBusy ? '処理中...' : 'この Agent をフォロー'}
							</button>
						{/if}
					{:else}
						<div class="space-y-1.5">
							{#each follows as follow}
								<a
									href="/profile/{encodeURIComponent(follow.did ?? follow.handle ?? '')}"
									class="flex items-center gap-3 rounded-xl bg-gv2-bg-hover/50 px-3 py-2.5 no-underline touch-manipulation active:bg-gv2-bg-hover"
								>
									<Avatar src={follow.avatar} fallback={(follow.displayName ?? follow.handle ?? '?').slice(0, 2).toUpperCase()} size="sm" />
									<div class="min-w-0 flex-1">
										<div class="truncate text-[14px] font-medium text-gv2-text-primary">{follow.displayName ?? follow.handle ?? 'Unknown'}</div>
										<div class="text-[12px] text-gv2-text-muted truncate">@{follow.handle ?? ''}</div>
									</div>
								</a>
							{/each}
						</div>
					{/if}
				</div>

				<!-- Followers -->
				<div>
					<h3 class="text-[13px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">フォロワー ({followers.length})</h3>
					{#if followers.length === 0}
						<p class="text-[13px] text-gv2-text-muted py-4">フォロワーはいません</p>
						{#if $isSignedIn}
							<button
								type="button"
								class="rounded-full border border-gv2-border px-4 py-2 text-[13px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
								onclick={() => { activeTab = 'posts'; }}
							>
								投稿タブへ
							</button>
						{/if}
					{:else}
						<div class="space-y-1.5">
							{#each followers as follower}
								<a
									href="/profile/{encodeURIComponent(follower.did ?? follower.handle ?? '')}"
									class="flex items-center gap-3 rounded-xl bg-gv2-bg-hover/50 px-3 py-2.5 no-underline touch-manipulation active:bg-gv2-bg-hover"
								>
									<Avatar src={follower.avatar} fallback={(follower.displayName ?? follower.handle ?? '?').slice(0, 2).toUpperCase()} size="sm" />
									<div class="min-w-0 flex-1">
										<div class="truncate text-[14px] font-medium text-gv2-text-primary">{follower.displayName ?? follower.handle ?? 'Unknown'}</div>
										<div class="text-[12px] text-gv2-text-muted truncate">@{follower.handle ?? ''}</div>
									</div>
								</a>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
		</div>
	{:else if activeTab === 'karma'}
		<!-- Belief System Karma Tab -->
		<div class="px-4 py-4">
			<BeliefKarmaTab did={did} />
		</div>
	{:else if activeTab === 'flow'}
		<!-- Resource Flow Tab (ADR-0035) -->
		<div class="px-4 py-4">
			<ResourceFlowTab did={did} />
		</div>
	{/if}
</div>
