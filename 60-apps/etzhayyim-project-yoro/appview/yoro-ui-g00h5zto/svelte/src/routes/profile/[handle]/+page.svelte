<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	// Server data for SSR OG tags (crawlers)
	const { data } = $props();
	import { Avatar, Skeleton, ActionSheet, TabBar } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { playTap, playTabSwitch, haptic } from '@etzhayyim/design-system/audio';
	import { spring } from 'svelte/motion';
	import { RichText, didFromRouteActor, postRkey, postRouteActor, type ESimProfile, fetchEsimProfile as _fetchEsim, type IssuingCard, type IssuingBalance, fetchCards as _fetchCards, freezeCard as _freezeCard, unfreezeCard as _unfreezeCard, fetchActorScores as _fetchActorScores, timeAgo } from '$lib/w';
		import { getAuthorProfile, getAuthorFeed, getFollowers, getFollows, followUser, unfollowUser, resolveHandle, getCurrentDID, isDid, setProfile, muteActor, unmuteActor, blockActor, unblockActor, reportContent, atProcedure, atQuery } from '$lib/atproto-agent';
	import type { FeedItem, AuthorProfile } from '$lib/atproto-agent';
	import { isSignedIn } from '$lib/auth';
	import { fade, fly } from 'svelte/transition';
	import { ActorHero } from '$lib/actor';
	import type { ActorProfileView, ActorScores } from '$lib/actor';
	import AgentProfile from './AgentProfile.svelte';
	import { XPBar, AchievementsGrid, BeliefKarmaTab } from '$lib/gamification';
	import { ResourceFlowTab } from '$lib/fiscal';
	import { recordVisit } from '$lib/history.svelte';

	let loading = $state(true);
	let error = $state('');
	let did = $state('');
	let handle = $state('');
	let isSelf = $state(false);
	let profile = $state<AuthorProfile | null>(null);
	let feedItems = $state<FeedItem[]>([]);
	let postsLoading = $state(false);
	let followBusy = $state(false);
	let activeTab = $state('posts');

	// Agent/Entity DID profile
	let isAgent = $state(false);
	let actorData = $state<Record<string, any>>({});
	let capabilitiesData = $state<Array<Record<string, any>>>([]);
	let performerData = $state<Record<string, any>>({});
	let publicConvos = $state<any[]>([]);

	// Cross-app scores (dojo, joucho)
	let actorScores = $state<ActorScores | undefined>(undefined);

	// eSIM state (types from $lib/w/profile-utils)
	let esimProfile = $state<ESimProfile | null>(null);
	let esimLoading = $state(false);
	let esimProvisioning = $state(false);
	let esimError = $state('');

	// AI call handling state
	interface AIResponsePolicy {
		mode: 'always_ai' | 'absent_only' | 'unknown_only' | 'off';
		greeting: string;
		systemPrompt: string;
		blockThreshold: number;
	}
	interface AICall {
		callId: string;
		callerE164: string;
		callerDid?: string;
		state: string;
		trustScore?: number;
		summary?: string;
		durationMs?: number;
		createdAt: string;
	}
	let aiPolicy = $state<AIResponsePolicy>({ mode: 'always_ai', greeting: '', systemPrompt: '', blockThreshold: 20 });
	let aiPolicyLoading = $state(false);
	let aiPolicySaving = $state(false);
	let aiCalls = $state<AICall[]>([]);
	let aiCallsLoading = $state(false);

	// Cards (Stripe Issuing) state (types from $lib/w/profile-utils)
	let cardsItems = $state<IssuingCard[]>([]);
	let cardsLoading = $state(false);
	let cardsBalance = $state<IssuingBalance | null>(null);
	let showEsimOnboarding = $state(false);

	// GCC token balance on the private chain (ADR-0074)
	let gccBalance = $state<string | null>(null);      // wei as decimal string, null = not loaded
	let gccSmartAccount = $state<string | null>(null); // activated smart account address

	// Edit profile modal
	let showEditProfile = $state(false);
	let editDisplayName = $state('');
	let editBio = $state('');
	let editSaving = $state(false);

	// More menu
	let showMoreMenu = $state(false);

	// Moderation state
	let viewerMuted = $state(false);
	let viewerBlocked = $state(false);

	const rawHandle = $derived(decodeURIComponent(($page.params as Record<string, string>).handle ?? ''));
	let lastLoadedHandle = '';

	let displayName = $derived(profile?.displayName ?? '');
	let avatarUrl = $derived(profile?.avatar ?? '');
	let bio = $derived(profile?.description ?? '');
	let followerCount = $derived(profile?.followersCount ?? 0);
	let followingCount = $derived(profile?.followsCount ?? 0);
	let postCount = $derived(profile?.postsCount ?? 0);
	let viewerFollowing = $derived(profile?.viewerFollowing ?? false);

	$effect(() => {
		const h = rawHandle;
		if (h && h !== lastLoadedHandle) {
			lastLoadedHandle = h;
			void loadProfile(h);
		}
	});

	async function loadProfile(inputHandle: string) {
		error = '';
		loading = true;
		try {
			handle = inputHandle.replace(/^@/, '');
			// Use SSR-resolved DID if available (skip resolveHandle round-trip)
			if (data?.og?.did && !did) {
				did = data.og.did;
			} else if (isDid(handle)) {
				did = handle;
			} else {
				did = didFromRouteActor(handle) || await resolveHandle(handle);
			}

			// did:web: DIDs are App agents — show AgentProfile directly
			// Sub-path DIDs (did:web:gamers.etzhayyim.com:elden-ring) are per-entity
			// profiles within an app — resolved via PDS, not app manifest.
			// Exception: atproto.etzhayyim.com:user: DIDs are human users, not agents.
			// Normalize bare nanoid DIDs: did:web:abc123 → did:web:abc123.etzhayyim.com
			if (did.startsWith('did:web:')) {
				const rest = did.slice(8);
				const colonIdx = rest.indexOf(':');
				const host = colonIdx >= 0 ? rest.slice(0, colonIdx) : rest;
				if (!host.includes('.')) {
					did = colonIdx >= 0
						? `did:web:${host}.etzhayyim.com:${rest.slice(colonIdx + 1)}`
						: `did:web:${host}.etzhayyim.com`;
				}
			}
			const isPdsUserDid = did.startsWith('did:web:atproto.etzhayyim.com:user:');
			if (did.startsWith('did:web:') && !isPdsUserDid) {
				isAgent = true;
				// Parse DID:web — colons after host are sub-path segments
				const didParts = did.replace('did:web:', '').split(':');
				const appHost = didParts[0];
				const subPath = didParts.slice(1).join('/');
				const appSlug = appHost.replace('.etzhayyim.com', '');
				const displaySlug = subPath || appSlug;
				actorData = { name: displaySlug, did, nanoid: appSlug, subPath, description: `${appHost} — App` };
				capabilitiesData = [];
				performerData = {};
				publicConvos = [];
				// Single path: PDS XRPC getAuthorProfile → graph SQL path → RisingWave
				const actorLookup = !isDid(handle) && handle.includes(':') ? handle : did;
				const [actorResult, currentDid] = await Promise.all([
					getAuthorProfile(actorLookup),
					getCurrentDID(),
				]);
				// SSR tools (server-side, no extra fetch)
				const ssrTools = data?.appTools;
				if (Array.isArray(ssrTools) && ssrTools.length > 0) {
					actorData.tools = JSON.stringify(ssrTools);
				}
				// Apply PDS actor data
				profile = actorResult;
				if (actorResult.displayName && actorResult.displayName !== actorResult.handle) actorData.name = actorResult.displayName;
				if (actorResult.description) actorData.description = actorResult.description;
				if (actorResult.avatar) actorData.avatar = actorResult.avatar;
				if (actorResult.performerType) actorData.performerType = actorResult.performerType;
				if (actorResult.nanoid) actorData.nanoid = actorResult.nanoid;
				if (actorResult.uiType) actorData.uiType = actorResult.uiType;
				if (actorResult.embedUrl) actorData.embedUrl = actorResult.embedUrl;
				// Server-authoritative social stats from app.bsky.actor.getProfile
				// (mv_actor_social_stats). Used as primary source for the profile
				// stats badges; client-side feed/follow loaders are the fallback.
				if (typeof actorResult.postsCount === 'number') actorData.postsCount = actorResult.postsCount;
				if (typeof actorResult.followersCount === 'number') actorData.followersCount = actorResult.followersCount;
				if (typeof actorResult.followsCount === 'number') actorData.followsCount = actorResult.followsCount;
				// Gov / civic profile extensions (if present in PDS response)
				if (actorResult.category) actorData.category = actorResult.category;
				if (actorResult.country) actorData.country = actorResult.country;
				if (Array.isArray(actorResult.addresses)) actorData.addresses = actorResult.addresses;
				if (Array.isArray(actorResult.contacts)) actorData.contacts = actorResult.contacts;
				if (Array.isArray(actorResult.desks)) actorData.desks = actorResult.desks;
				if (Array.isArray(actorResult.procedures)) actorData.procedures = actorResult.procedures;
				if (Array.isArray(actorResult.documentTemplates)) actorData.documentTemplates = actorResult.documentTemplates;
				if (Array.isArray(actorResult.complianceFrameworks)) actorData.complianceFrameworks = actorResult.complianceFrameworks;
				if (typeof actorResult.ministryCount === 'number') actorData.ministryCount = actorResult.ministryCount;
				if (typeof actorResult.contractCount === 'number') actorData.contractCount = actorResult.contractCount;
				if (typeof actorResult.bpmnCount === 'number') actorData.bpmnCount = actorResult.bpmnCount;
				if (actorResult.dataSourceRef) actorData.dataSourceRef = actorResult.dataSourceRef;
				// Fallback: if getProfile did not surface gov fields, query
				// com.etzhayyim.apps.states.stateProfile records directly from graph.
				if (!actorData.addresses && !actorData.procedures) {
					try {
						// Derive ISO-3 code from did path. 2 supported shapes:
						//   did:web:states.etzhayyim.com:state:jpn  → repo=states.etzhayyim.com, rkey=jpn
						//   did:web:jpn-state.etzhayyim.com         → repo=states.etzhayyim.com, rkey=jpn
						let iso = '';
						const subLast = subPath.split('/').filter(Boolean).pop() || '';
						const hostFirst = appHost.split('.')[0] || '';
						if (/^[a-z]{3}$/i.test(subLast)) iso = subLast.toLowerCase();
						else if (/^[a-z]{3}$/i.test(hostFirst)) iso = hostFirst.toLowerCase();
						if (iso) {
							// Use public /api/kagami/query proxy (read-only, no auth needed)
							const sql = `SELECT value_json FROM vertex_state_profile WHERE repo = 'states.etzhayyim.com' AND rkey = '${iso.replace(/[^a-z0-9]/g, '')}'`;
							const kRes = await fetch('https://atproto.etzhayyim.com/api/kagami/query', {
								method: 'POST', headers: { 'Content-Type': 'application/json' },
								body: JSON.stringify({ sql }),
							}).then(r => r.ok ? r.json() : null).catch(() => null);
							const rows = (kRes as any)?.rows?.rows;
							let rec: any = null;
							if (Array.isArray(rows) && rows[0]?.value_json) {
								try { rec = JSON.parse(rows[0].value_json); } catch {}
							}
							if (rec && typeof rec === 'object') {
								if (Array.isArray(rec.addresses)) actorData.addresses = rec.addresses;
								if (Array.isArray(rec.contacts)) actorData.contacts = rec.contacts;
								if (Array.isArray(rec.desks)) actorData.desks = rec.desks;
								if (Array.isArray(rec.procedures)) actorData.procedures = rec.procedures;
								if (Array.isArray(rec.documentTemplates)) actorData.documentTemplates = rec.documentTemplates;
								if (Array.isArray(rec.complianceFrameworks)) actorData.complianceFrameworks = rec.complianceFrameworks;
								if (typeof rec.ministryCount === 'number') actorData.ministryCount = rec.ministryCount;
								if (typeof rec.contractCount === 'number') actorData.contractCount = rec.contractCount;
								if (typeof rec.bpmnCount === 'number') actorData.bpmnCount = rec.bpmnCount;
								if (rec.dataSourceRef) actorData.dataSourceRef = rec.dataSourceRef;
								actorData.category = actorData.category || 'government';
							}
						}
					} catch (e) { console.warn('stateProfile fallback failed', e); }
				}
				capabilitiesData = actorResult?.capabilities ?? [];
				performerData = actorResult?.performer ?? {};
				if (!performerData.performerType && actorData.performerType) {
					performerData = { ...performerData, performerType: actorData.performerType };
				}
				publicConvos = actorResult?.convos ?? [];
				isSelf = currentDid === did;
			} else {
				// Human profile: PDS getProfile + agent check + getCurrentDID in parallel
				const [profileResult, currentDidResult] = await Promise.allSettled([
					atQuery('app.bsky.actor.getProfile', { actor: did }).catch((_err) => null),
					getCurrentDID(),
				]);

				// Use PDS response for both profile and agent check (single fetch)
				const actorResult = profileResult.status === 'fulfilled' ? profileResult.value : null;
				if (actorResult) {
					// Set profile from PDS response
					profile = await getAuthorProfile(did);
					// Check agent flag from same response
					isAgent = actorResult.isAgent === true;
					if (isAgent) {
						actorData = actorResult.actor ?? {};
						capabilitiesData = actorResult.capabilities ?? [];
						performerData = actorResult.performer ?? {};
						publicConvos = actorResult.convos ?? [];
					}
				} else {
					profile = await getAuthorProfile(did);
				}

				// isSelf from parallel getCurrentDID
				isSelf = currentDidResult.status === 'fulfilled' && currentDidResult.value === did;
			}

			viewerMuted = profile?.viewerMuted ?? false;
			viewerBlocked = !!profile?.viewerBlocked;

			// Record browsing history
			recordVisit({
				path: `/profile/${encodeURIComponent(inputHandle)}`,
				title: profile?.displayName || actorData.name || inputHandle,
				type: 'profile',
				avatar: profile?.avatar || actorData.avatar,
				handle: profile?.handle || actorData.did?.replace(/^did:web:/, ''),
			});

			// Non-blocking score fetch for all profiles
			_fetchActorScores(did).then((s) => { actorScores = s; });
			// Non-blocking GCC balance fetch (public endpoint, no auth required)
			void fetchGccTokenBalance(did);

			if (!isAgent) {
				// Non-blocking feed load — show profile immediately, feed loads in background
				loadFeed('posts_with_replies');
				// Non-blocking eSIM + AI policy check for self profile
				if (isSelf) {
					fetchEsimProfile(did).then(() => {
						if (!esimProfile) showEsimOnboarding = true;
					});
					fetchAiPolicy();
					fetchAiCalls();
				}
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'プロフィールの読み込みに失敗しました';
		} finally {
			loading = false;
		}
	}

	async function loadFeed(filter: string) {
		postsLoading = true;
		try {
			const result = await getAuthorFeed(did, { limit: 50 } as any);
			const items: FeedItem[] = (Array.isArray(result) ? result : (result as any).feed ?? []) as FeedItem[];
			const seen = new Set<string>();
			feedItems = items.filter((item: FeedItem) => {
				const key = item?.post?.uri || `${item?.post?.author?.did || ''}/${item?.post?.rkey || ''}`;
				if (!key || seen.has(key)) return false;
				seen.add(key);
				return true;
			});
		} catch (e) {
			console.warn('profile: loadFeed failed', e);
			feedItems = [];
		} finally {
			postsLoading = false;
		}
	}

	async function handleTabChange(tabId: string) {
		activeTab = tabId;
		if (isAgent) return;

		switch (tabId) {
			case 'posts':
				await loadFeed('posts_with_replies');
				break;
			case 'replies':
				await loadFeed('posts_with_replies');
				break;
			case 'media':
				await loadFeed('posts_with_media');
				break;
			case 'sim':
				await fetchEsimProfile(did);
				break;
			case 'cards':
				await fetchCards();
				break;
			default:
				feedItems = [];
				break;
		}
	}

	let filteredPosts = $derived.by(() => {
		if (activeTab === 'replies') {
			return feedItems.filter((item) => item.post.reply != null);
		}
		return feedItems;
	});

	async function toggleFollow() {
		if (!did || followBusy) return;
		followBusy = true;
		try {
			if (viewerFollowing) {
				await unfollowUser(did);
			} else {
				await followUser(did);
			}
			// Refresh profile to get updated follow state
			profile = await getAuthorProfile(did);
		} catch (e) {
			console.warn('profile: toggleFollow failed', e);
		} finally {
			followBusy = false;
		}
	}

	async function toggleMute() {
		try {
			if (viewerMuted) {
				await unmuteActor(did);
				viewerMuted = false;
			} else {
				await muteActor(did);
				viewerMuted = true;
			}
		} catch (e) { console.warn('profile: toggleMute failed', e); }
		showMoreMenu = false;
	}

	async function toggleBlock() {
		try {
			if (viewerBlocked) {
				await unblockActor(did);
				viewerBlocked = false;
			} else {
				await blockActor(did);
				viewerBlocked = true;
			}
		} catch (e) { console.warn('profile: toggleBlock failed', e); }
		showMoreMenu = false;
	}

	async function handleReport() {
		try {
			await reportContent({
				reasonType: 'other',
				reason: '',
				subject: { did },
			});
		} catch (e) { console.warn('profile: handleReport failed', e); }
		showMoreMenu = false;
	}

	function goBack() {
		if (history.length > 1) history.back();
		else goto('/');
	}

	async function fetchEsimProfile(_userDid: string) {
		esimLoading = true;
		esimError = '';
		try {
			const res = await _fetchEsim();
			esimProfile = res;
		} catch (e) {
			console.warn('fetchEsimProfile failed', e);
			esimProfile = null;
		} finally {
			esimLoading = false;
		}
	}

	async function fetchGccTokenBalance(actorDid: string) {
		gccBalance = null;
		gccSmartAccount = null;
		try {
			const res = await fetch(
				`https://authz.etzhayyim.com/xrpc/com.etzhayyim.authz.getActorTokenBalance?did=${encodeURIComponent(actorDid)}`,
				{ signal: AbortSignal.timeout(5000) },
			);
			if (!res.ok) return;
			const data = await res.json() as { gccBalance?: string; smartAccount?: string | null; activated?: boolean };
			gccBalance = data.gccBalance ?? "0";
			gccSmartAccount = data.smartAccount ?? null;
		} catch {
			// non-critical — silently suppress
		}
	}

	async function provisionEsim() {
		esimProvisioning = true;
		esimError = '';
		try {
			const result = await atProcedure<Record<string, unknown>>('com.etzhayyim.apps.celler.provisionEsim', {
				did,
				dataPlan: 'starter',
			});
			const qrCodeUrl = result?.qrCodeUrl ? String(result.qrCodeUrl) : '';
			const activationCode = result?.activationCode ? String(result.activationCode) : '';
			if (result?.iccid || qrCodeUrl || result?.status) {
				esimProfile = {
					iccid: String(result.iccid ?? ''),
					provider: 'telnyx',
					coverage: 'global',
					dataRemainingMb: Number(result.dataRemainingMb ?? 1024),
					dataUsedMb: Number(result.dataUsedMb ?? 0),
					status: String(result.status ?? 'provisioned'),
					qrCodeUrl: qrCodeUrl || undefined,
					activationCode: activationCode || undefined,
				};
				showEsimOnboarding = false;
			} else if (result?.error) {
				esimError = String(result.error);
			}
		} catch (e) {
			esimError = e instanceof Error ? e.message : 'eSIM の発行に失敗しました';
			console.warn('provisionEsim failed', e);
		} finally {
			esimProvisioning = false;
		}
	}

	async function activateEsim() {
		if (!esimProfile?.iccid) return;
		try {
			await atProcedure('com.etzhayyim.apps.celler.activateEsim', { iccid: esimProfile.iccid });
			esimProfile = { ...esimProfile, status: 'enabled' };
		} catch (e) {
			console.warn('activateEsim failed', e);
		}
	}

	async function suspendEsim() {
		if (!esimProfile?.iccid) return;
		try {
			await atProcedure('com.etzhayyim.apps.celler.suspendEsim', { iccid: esimProfile.iccid });
			esimProfile = { ...esimProfile, status: 'disabled' };
		} catch (e) {
			console.warn('suspendEsim failed', e);
		}
	}

	async function fetchAiPolicy() {
		aiPolicyLoading = true;
		try {
			const result = await atProcedure<Record<string, unknown>>('com.etzhayyim.apps.celler.getAiResponsePolicy', {});
				if (result) {
					aiPolicy = {
						mode: (String(result.mode ?? 'always_ai')) as AIResponsePolicy['mode'],
						greeting: String(result.greeting ?? ''),
						systemPrompt: String(result.systemPrompt ?? ''),
						blockThreshold: Number(result.blockThreshold ?? 20),
					};
				}
		} catch (e) {
			console.warn('fetchAiPolicy failed', e);
		} finally {
			aiPolicyLoading = false;
		}
	}

	async function saveAiPolicy() {
		aiPolicySaving = true;
		try {
			await atProcedure('com.etzhayyim.apps.celler.setAiResponsePolicy', aiPolicy);
		} catch (e) {
			console.warn('saveAiPolicy failed', e);
		} finally {
			aiPolicySaving = false;
		}
	}

	async function fetchAiCalls() {
		aiCallsLoading = true;
		try {
			const result = await atProcedure<{ calls?: Record<string, unknown>[] }>('com.etzhayyim.apps.celler.listAiCalls', { limit: 10 });
			aiCalls = (result?.calls ?? []).map((c: Record<string, unknown>) => ({
				callId: String(c.callId ?? ''),
				callerE164: String(c.callerE164 ?? ''),
				callerDid: c.callerDid ? String(c.callerDid) : undefined,
				state: String(c.state ?? ''),
				trustScore: c.trustScore != null ? Number(c.trustScore) : undefined,
				summary: c.summary ? String(c.summary) : undefined,
				durationMs: c.durationMs != null ? Number(c.durationMs) : undefined,
				createdAt: String(c.createdAt ?? ''),
			}));
		} catch (e) {
			console.warn('fetchAiCalls failed', e);
		} finally {
			aiCallsLoading = false;
		}
	}

	async function fetchCards() {
		cardsLoading = true;
		try {
			const result = await _fetchCards();
			cardsItems = result.cards;
			cardsBalance = result.balance;
		} catch {
			cardsItems = [];
		} finally {
			cardsLoading = false;
		}
	}

	async function freezeCard(cardId: string) {
		if (await _freezeCard(cardId)) cardsItems = cardsItems.map((c) => c.id === cardId ? { ...c, status: 'inactive' } : c);
	}

	async function unfreezeCard(cardId: string) {
		if (await _unfreezeCard(cardId)) cardsItems = cardsItems.map((c) => c.id === cardId ? { ...c, status: 'active' } : c);
	}

	function openEditProfile() {
		editDisplayName = displayName;
		editBio = bio;
		showEditProfile = true;
	}

	async function saveProfile() {
		editSaving = true;
		try {
			await setProfile({ displayName: editDisplayName } as any);
			profile = await getAuthorProfile(did);
			showEditProfile = false;
		} catch (e) {
			console.warn('profile: saveProfile failed', e);
		} finally {
			editSaving = false;
		}
	}

	function copyProfileLink() {
		navigator.clipboard?.writeText(`https://yoro.etzhayyim.com/profile/${handle}`);
		showMoreMenu = false;
	}

	const profileTabs = $derived([
		{ value: 'posts', label: '投稿' },
		{ value: 'replies', label: '返信' },
		{ value: 'media', label: 'メディア' },
		{ value: 'video', label: 'ビデオ' },
		{ value: 'likes', label: 'いいね' },
		{ value: 'dojo', label: 'Dojo' },
		{ value: 'karma', label: 'カルマ' },
		{ value: 'flow', label: 'Resource Flow' },
		...(isSelf ? [{ value: 'sim', label: 'SIM' }] : []),
		...(isSelf ? [{ value: 'cards', label: 'カード' }] : []),
		{ value: 'feeds', label: 'フィード' },
		{ value: 'starter', label: 'スターターパック' },
	]);

	// Build ActorProfileView for ActorHero from available data
	const actorProfileView = $derived.by((): ActorProfileView => {
		const base = {
			did,
			handle: handle || '',
			displayName: isAgent ? (actorData.name ?? actorData.displayName ?? handle) : (profile?.displayName ?? handle),
			avatar: isAgent ? (actorData.avatar ?? '') : (profile?.avatar ?? ''),
			description: isAgent ? (actorData.description ?? '') : (profile?.description ?? ''),
			followersCount: profile?.followersCount ?? 0,
			followsCount: profile?.followsCount ?? 0,
			postsCount: profile?.postsCount ?? 0,
			viewerFollowing: profile?.viewerFollowing,
			viewerMuted: profile?.viewerMuted,
			viewerBlocked: profile?.viewerBlocked as string | undefined,
		};
		// AT Protocol extensions (from PDS getProfile response)
		const ext = profile as any;
		return {
			...base,
			performerType: ext?.performerType ?? (isAgent ? 'service' : 'person'),
			contentMode: ext?.contentMode ?? 'timeline',
			nanoid: actorData.nanoid ?? '',
			service: ext?.service,
			system: ext?.system,
			person: ext?.person,
			organization: ext?.organization,
			scores: actorScores,
		};
	});

	const ogTitle = $derived(data?.og?.title || `${displayName || handle || 'Profile'} — YORO`);

	/** GCC balance formatted as "1,234.56 GCC". null if not loaded or zero. */
	const gccBalanceFormatted = $derived.by(() => {
		if (gccBalance === null || gccBalance === "0") return null;
		try {
			const wei = BigInt(gccBalance);
			const gcc = Number(wei) / 1e18;
			return gcc.toLocaleString('ja-JP', { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + ' GCC';
		} catch {
			return null;
		}
	});
	const ogDesc = $derived(data?.og?.description || (isAgent ? (actorData.description ?? `@${handle} on YORO`) : `@${handle} on YORO`));
	const ogType = $derived(data?.og?.type || (isAgent ? 'website' : 'profile'));
	const ogImage = $derived(data?.og?.image || avatarUrl || 'https://yoro.etzhayyim.com/logo-v3.png');
	const ogImageAlt = $derived(data?.og?.imageAlt || `${displayName || handle || 'YORO'} profile image`);
	const ogUrl = $derived(data?.og?.url || `https://yoro.etzhayyim.com/profile/${handle}`);
</script>

<svelte:head>
	<title>{ogTitle}</title>
	<meta name="description" content={ogDesc} />
	<meta property="og:title" content={ogTitle} />
	<meta property="og:description" content={ogDesc} />
	<meta property="og:type" content={ogType} />
	<meta property="og:url" content={ogUrl} />
	<meta property="og:image" content={ogImage} />
	<meta property="og:image:alt" content={ogImageAlt} />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={ogTitle} />
	<meta name="twitter:description" content={ogDesc} />
	<meta name="twitter:image" content={ogImage} />
	<meta name="twitter:image:alt" content={ogImageAlt} />
	<link rel="canonical" href={ogUrl} />
	<link rel="alternate" type="application/json+oembed"
		href="https://yoro.etzhayyim.com/oembed?url={encodeURIComponent(ogUrl)}&format=json"
		title={ogTitle} />
	{#if data?.og?.did}
		<meta name="at:did" content={data.og.did} />
	{/if}
	{#if data?.jsonLd}
		{@html `<script type="application/ld+json">${JSON.stringify(data.jsonLd)}</script>`}
	{/if}
</svelte:head>

<div class="flex h-full flex-col bg-gv2-bg-primary">
	<!-- Header: back arrow only -->
	<div class="flex min-h-[48px] items-center px-2">
		<button
			type="button"
			class="flex h-11 w-11 items-center justify-center rounded-full text-gv2-text-primary tap-target-44 touch-manipulation active:bg-gv2-bg-hover active:scale-90 focus-glow transition-transform"
			onclick={() => { playTap(); haptic('light'); goBack(); }}
			aria-label="戻る"
		>
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
				<path d="M15 19l-7-7 7-7" />
			</svg>
		</button>
	</div>

	<div class="flex-1 overflow-y-auto scrollbar-none pb-20 safe-area-bottom">
		{#if loading}
			<div class="px-4 py-8">
				<div class="flex flex-col gap-4" in:fade={staggerFade(0, { duration: 300 })}>
					<div class="h-16 w-16 animate-pulse rounded-full bg-gv2-bg-hover"></div>
					<div class="space-y-2">
						<Skeleton variant="text" class="w-48" />
						<Skeleton variant="text" class="w-40" />
						<Skeleton variant="text" class="w-32" />
					</div>
				</div>
			</div>
		{:else if error}
			<div class="flex flex-col items-center gap-4 px-4 py-16" in:fade={{ duration: 300 }}>
				<div class="flex h-20 w-20 items-center justify-center rounded-full bg-red-500/10 text-[36px]">?</div>
				<h2 class="text-[17px] font-bold text-gv2-text-primary">プロフィールが見つかりません</h2>
				<p class="max-w-[280px] text-center text-[14px] text-gv2-text-muted">{error}</p>
				<button type="button" class="mt-4 min-h-[44px] rounded-full bg-[#1185FE] px-6 py-2.5 text-[15px] font-semibold text-white tap-target-44 touch-manipulation active:opacity-80" onclick={goBack}>戻る</button>
			</div>
		{:else if isAgent}
			<!-- Agent/Entity DID Profile — performerType-aware tabs -->
			<AgentProfile
				{did}
				actor={actorData}
				capabilities={capabilitiesData}
				performer={performerData}
				{publicConvos}
				initialFollowing={viewerFollowing}
				{gccBalance}
				{gccSmartAccount}
			/>
		{:else}
			<!-- Human Profile — ActorHero + tabs -->
			<ActorHero profile={actorProfileView} />

			<!-- GCC Token Balance (shown when smart account is activated and balance > 0) -->
			{#if gccBalanceFormatted}
				<div class="mx-4 mt-3 flex items-center gap-3 rounded-2xl border border-amber-500/20 bg-gradient-to-r from-amber-500/8 to-yellow-500/8 px-4 py-3" transition:fade={{ duration: 200 }}>
					<div class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-amber-400 text-[16px] font-bold select-none">G</div>
					<div class="min-w-0 flex-1">
						<p class="text-[13px] text-gv2-text-muted leading-tight">GCC トークン残高</p>
						<p class="text-[17px] font-bold text-amber-400 leading-tight">{gccBalanceFormatted}</p>
					</div>
					{#if gccSmartAccount}
						<a
							href="https://geth.etzhayyim.com"
							target="_blank"
							rel="noopener noreferrer"
							class="flex-shrink-0 rounded-full bg-amber-500/15 px-3 py-1 text-[12px] font-medium text-amber-400 touch-manipulation active:scale-95 transition-transform"
						>チェーン</a>
					{/if}
				</div>
			{/if}

			<!-- Tabs -->
			<TabBar
				tabs={profileTabs}
				bind:activeValue={activeTab}
				onchange={(v) => void handleTabChange(v)}
				class="mt-3"
			/>

			<!-- eSIM Onboarding Banner (self, no eSIM) -->
			{#if isSelf && showEsimOnboarding && !esimProfile && activeTab !== 'sim'}
				<div class="mx-4 mt-3 flex items-center gap-3 rounded-2xl bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20 px-4 py-3" transition:fly={{ y: -10, duration: 200 }}>
					<div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
						<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M6 10h4v4H6z" /><path d="M14 10h1" /><path d="M18 10h1" /><path d="M14 14h5" /></svg>
					</div>
					<div class="min-w-0 flex-1">
						<p class="text-[14px] font-bold text-gv2-text-primary">eSIM を取得しよう</p>
						<p class="text-[12px] text-gv2-text-muted">180+ 国で使えるデータ通信。今すぐ契約</p>
					</div>
					<button
						type="button"
						class="flex-shrink-0 rounded-full bg-emerald-500 px-4 py-1.5 text-[13px] font-bold text-white touch-manipulation active:scale-95 transition-transform"
						onclick={() => { playTap(); haptic('light'); activeTab = 'sim'; void fetchEsimProfile(did); }}
					>
						契約
					</button>
					<button
						type="button"
						class="flex-shrink-0 text-gv2-text-muted touch-manipulation active:opacity-70"
						onclick={() => { showEsimOnboarding = false; }}
						aria-label="閉じる"
					>
						<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
					</button>
				</div>
			{/if}

			<!-- Tab content -->
			<div>
				{#if activeTab === 'dojo'}
					<!-- Dojo Gamification Tab -->
					<div class="px-4 py-4 flex flex-col gap-4">
						<XPBar />
						<AchievementsGrid />
					</div>
				{:else if activeTab === 'karma'}
					<!-- Belief System Karma Tab -->
					<div class="px-4 py-4">
						<BeliefKarmaTab did={did || undefined} />
					</div>
				{:else if activeTab === 'flow'}
					<!-- Resource Flow Tab (ADR-0035) -->
					<div class="px-4 py-4">
						<ResourceFlowTab did={did || undefined} />
					</div>
				{:else if activeTab === 'sim' && isSelf}
					<!-- eSIM Management Tab -->
					<div class="px-4 py-6">
						{#if esimLoading}
							<div class="flex flex-col items-center gap-4 py-12">
								<div class="h-12 w-12 animate-pulse rounded-full bg-emerald-500/20"></div>
								<Skeleton variant="text" class="w-48" />
								<Skeleton variant="text" class="w-32" />
							</div>
						{:else if esimProfile}
							<!-- eSIM Status Card -->
							<div class="rounded-2xl border border-gv2-border/30 bg-gradient-to-br from-gv2-bg-hover/50 to-gv2-bg-hover/20 p-5">
								<div class="flex items-center justify-between mb-4">
									<div class="flex items-center gap-3">
										<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
											<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M6 10h4v4H6z" /><path d="M14 10h1" /><path d="M18 10h1" /><path d="M14 14h5" /></svg>
										</div>
										<div>
											<p class="text-[15px] font-bold text-gv2-text-primary">Celler eSIM</p>
											<p class="text-[12px] text-gv2-text-muted">Telnyx Wireless / {esimProfile.coverage}</p>
										</div>
									</div>
									<span class="rounded-full px-3 py-1 text-[12px] font-bold {(esimProfile.status === 'active' || esimProfile.status === 'enabled') ? 'bg-emerald-500/20 text-emerald-400' : esimProfile.status === 'provisioned' ? 'bg-amber-500/20 text-amber-400' : 'bg-gray-500/20 text-gray-400'}">
										{(esimProfile.status === 'active' || esimProfile.status === 'enabled') ? '有効' : esimProfile.status === 'provisioned' ? 'アクティベーション待ち' : (esimProfile.status === 'suspended' || esimProfile.status === 'disabled') ? '停止中' : esimProfile.status}
									</span>
								</div>

								<!-- Data Usage -->
								<div class="mb-4">
									<div class="flex items-center justify-between text-[13px] text-gv2-text-muted mb-1.5">
										<span>データ使用量</span>
										<span>{esimProfile.dataUsedMb.toFixed(0)} / {(esimProfile.dataUsedMb + esimProfile.dataRemainingMb).toFixed(0)} MB</span>
									</div>
									{#if true}
										{@const total = esimProfile.dataUsedMb + esimProfile.dataRemainingMb}
										{@const pct = total > 0 ? Math.min((esimProfile.dataUsedMb / total) * 100, 100) : 0}
										<div class="h-2 rounded-full bg-gv2-bg-hover overflow-hidden">
											<div class="h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-500" style="width: {pct}%"></div>
										</div>
									{/if}
								</div>

								<!-- ICCID -->
								<div class="mb-4 text-[12px] text-gv2-text-muted">
									<span>ICCID: {esimProfile.iccid}</span>
								</div>

								<!-- QR Code for activation -->
								{#if esimProfile.qrCodeUrl && esimProfile.status === 'provisioned'}
									<div class="mb-4 flex flex-col items-center gap-3 rounded-xl bg-white p-4">
										<img src={esimProfile.qrCodeUrl} alt="eSIM QR Code" class="h-48 w-48" />
										<p class="text-[13px] text-gray-600">スマホでスキャンして eSIM を有効化</p>
									</div>
								{/if}

								<!-- Actions -->
								<div class="flex gap-3">
									{#if esimProfile.status === 'provisioned'}
										<button
											type="button"
											class="flex-1 rounded-xl bg-emerald-500 py-3 text-center text-[14px] font-bold text-white touch-manipulation active:scale-[0.98] transition-transform"
											onclick={() => { playTap(); haptic('medium'); void activateEsim(); }}
										>
											アクティベート
										</button>
									{:else if esimProfile.status === 'active' || esimProfile.status === 'enabled'}
										<button
											type="button"
											class="flex-1 rounded-xl bg-gv2-bg-hover py-3 text-center text-[14px] font-bold text-gv2-text-muted touch-manipulation active:scale-[0.98] transition-transform"
											onclick={() => { playTap(); haptic('medium'); void suspendEsim(); }}
										>
											一時停止
										</button>
									{:else if esimProfile.status === 'suspended' || esimProfile.status === 'disabled'}
										<button
											type="button"
											class="flex-1 rounded-xl bg-emerald-500 py-3 text-center text-[14px] font-bold text-white touch-manipulation active:scale-[0.98] transition-transform"
											onclick={() => { playTap(); haptic('medium'); void activateEsim(); }}
										>
											再開
										</button>
									{/if}
								</div>
							</div>

							<!-- Info -->
							<div class="mt-4 rounded-xl bg-gv2-bg-hover/30 p-4">
								<p class="text-[13px] text-gv2-text-muted">Celler eSIM は Telnyx Wireless 経由で 180+ 国の LTE/5G データ通信を提供します。DID-addressed encrypted telephony。</p>
							</div>

							<!-- AI Call Response Settings -->
							<div class="mt-6 rounded-2xl border border-gv2-border/30 bg-gradient-to-br from-violet-500/5 to-blue-500/5 p-5">
								<div class="flex items-center gap-3 mb-4">
									<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/20 text-violet-400">
										<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>
									</div>
									<div>
										<p class="text-[15px] font-bold text-gv2-text-primary">AI 着信応答</p>
										<p class="text-[12px] text-gv2-text-muted">AI Agent が電話に応答・録音・文字起こし</p>
									</div>
								</div>

								{#if aiPolicyLoading}
									<div class="flex justify-center py-4"><Skeleton variant="text" class="w-48" /></div>
								{:else}
									<!-- Mode selector -->
									<div class="mb-4">
										<label class="block text-[12px] text-gv2-text-muted mb-1.5">応答モード</label>
										<div class="grid grid-cols-2 gap-2">
											{#each [
												{ value: 'always_ai', label: '常時 AI' },
												{ value: 'absent_only', label: '不在時のみ' },
												{ value: 'unknown_only', label: '未知番号のみ' },
												{ value: 'off', label: 'OFF' },
											] as opt}
												<button
													type="button"
													class="rounded-lg px-3 py-2.5 text-[13px] font-medium transition-all touch-manipulation active:scale-[0.97] {aiPolicy.mode === opt.value ? 'bg-violet-500/20 text-violet-300 border border-violet-500/40' : 'bg-gv2-bg-hover/50 text-gv2-text-muted border border-transparent'}"
													onclick={() => { playTap(); aiPolicy = { ...aiPolicy, mode: opt.value as AIResponsePolicy['mode'] }; void saveAiPolicy(); }}
												>
													{opt.label}
												</button>
											{/each}
										</div>
									</div>

									<!-- Greeting -->
									{#if aiPolicy.mode !== 'off'}
										<div class="mb-4">
											<label class="block text-[12px] text-gv2-text-muted mb-1.5">応答メッセージ</label>
											<textarea
												class="w-full rounded-lg bg-gv2-bg-hover/50 border border-gv2-border/20 px-3 py-2 text-[13px] text-gv2-text-primary resize-none focus:outline-none focus:border-violet-500/40"
												rows="2"
												placeholder="はい、お電話ありがとうございます。ただいま不在にしております。"
												bind:value={aiPolicy.greeting}
												onblur={() => void saveAiPolicy()}
											></textarea>
										</div>

										<!-- Spam threshold -->
										<div class="flex items-center justify-between">
											<div>
												<p class="text-[13px] text-gv2-text-primary">スパムブロック</p>
													<p class="text-[11px] text-gv2-text-muted">Trust Score {aiPolicy.blockThreshold} 未満を自動拒否</p>
											</div>
											<select
												class="rounded-lg bg-gv2-bg-hover/50 border border-gv2-border/20 px-2 py-1.5 text-[13px] text-gv2-text-primary focus:outline-none"
													bind:value={aiPolicy.blockThreshold}
												onchange={() => void saveAiPolicy()}
											>
												<option value={10}>10</option>
												<option value={20}>20</option>
												<option value={30}>30</option>
												<option value={50}>50</option>
											</select>
										</div>
									{/if}
								{/if}

								{#if aiPolicySaving}
									<p class="mt-2 text-[11px] text-violet-400">保存中...</p>
								{/if}
							</div>

							<!-- Recent AI Calls -->
							{#if aiCalls.length > 0}
								<div class="mt-6">
									<h3 class="text-[13px] font-bold text-gv2-text-muted mb-3">最近の AI 対応</h3>
									<div class="space-y-2">
										{#each aiCalls as call}
											<div class="rounded-xl bg-gv2-bg-hover/30 border border-gv2-border/10 p-3">
												<div class="flex items-center justify-between mb-1">
													<div class="flex items-center gap-2">
															<span class="text-[13px] font-medium text-gv2-text-primary">{call.callerE164 || '不明'}</span>
														{#if call.state === 'blocked'}
															<span class="rounded-full bg-red-500/20 px-2 py-0.5 text-[10px] font-bold text-red-400">BLOCKED</span>
														{:else if call.state === 'completed'}
															<span class="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400">完了</span>
														{:else}
															<span class="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-bold text-amber-400">{call.state}</span>
														{/if}
													</div>
													<span class="text-[11px] text-gv2-text-muted">
															{#if call.durationMs}
																{Math.round(call.durationMs / 1000)}秒
															{/if}
													</span>
												</div>
												{#if call.summary}
													<p class="text-[12px] text-gv2-text-muted line-clamp-2">{call.summary}</p>
												{/if}
													{#if call.createdAt}
														<p class="mt-1 text-[10px] text-gv2-text-muted/60">{new Date(call.createdAt).toLocaleString('ja-JP')}</p>
													{/if}
											</div>
										{/each}
									</div>
								</div>
							{:else if !aiCallsLoading}
								<div class="mt-6 text-center py-4">
									<p class="text-[13px] text-gv2-text-muted/60">AI 対応の通話履歴はまだありません</p>
								</div>
							{/if}
						{:else}
							<!-- No eSIM — Provisioning CTA -->
							<div class="flex flex-col items-center gap-5 py-8">
								<div class="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500/20 to-cyan-500/20">
									<svg class="h-10 w-10 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M6 10h4v4H6z" /><path d="M14 10h1" /><path d="M18 10h1" /><path d="M14 14h5" /></svg>
								</div>
								<div class="text-center">
									<h3 class="text-[17px] font-bold text-gv2-text-primary">eSIM を契約する</h3>
									<p class="mt-1 max-w-[280px] text-[14px] text-gv2-text-muted">180+ 国対応のデータ通信 eSIM。QR スキャンで即時開通。DID に紐付いた暗号化通信。</p>
								</div>

								<div class="w-full max-w-[320px] rounded-xl border border-gv2-border/20 bg-gv2-bg-hover/30 p-4">
									<div class="flex items-center justify-between text-[14px]">
										<span class="text-gv2-text-primary font-medium">1GB / 月</span>
										<span class="text-emerald-400 font-bold">~$2/月</span>
									</div>
									<p class="mt-1 text-[12px] text-gv2-text-muted">Telnyx Wireless LTE/5G</p>
								</div>

								{#if esimError}
									<p class="text-[13px] text-red-400">{esimError}</p>
								{/if}

								<button
									type="button"
									class="min-h-[48px] w-full max-w-[320px] rounded-full bg-emerald-500 px-8 py-3 text-[15px] font-bold text-white tap-target-44 touch-manipulation active:scale-95 transition-transform disabled:opacity-40"
									style="box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3)"
									disabled={esimProvisioning}
									onclick={() => { playTap(); haptic('medium'); void provisionEsim(); }}
								>
									{esimProvisioning ? '発行中...' : 'eSIM を発行する'}
								</button>

								<p class="text-[11px] text-gv2-text-muted/60">Celler by etzhayyim / Telnyx Wireless</p>
							</div>
						{/if}
					</div>
				{:else if activeTab === 'cards' && isSelf}
					<!-- Stripe Issuing Cards Tab -->
					<div class="px-4 py-6">
						{#if cardsLoading}
							<div class="flex flex-col items-center gap-4 py-12">
								<div class="h-12 w-12 animate-pulse rounded-full bg-[#635BFF]/20"></div>
								<Skeleton variant="text" class="w-48" />
								<Skeleton variant="text" class="w-32" />
							</div>
						{:else if cardsItems.length > 0}
							<!-- Issuing Balance -->
							{#if cardsBalance}
								<div class="mb-4 rounded-xl bg-gradient-to-r from-[#635BFF]/10 to-[#635BFF]/5 border border-[#635BFF]/20 p-4">
									<p class="text-[12px] text-gv2-text-muted mb-1">Issuing 残高</p>
									<p class="text-[22px] font-bold text-gv2-text-primary">
										{cardsBalance.currency === 'jpy' ? '¥' : cardsBalance.currency.toUpperCase() + ' '}{(cardsBalance.amount / (cardsBalance.currency === 'jpy' ? 1 : 100)).toLocaleString()}
									</p>
								</div>
							{/if}

							<!-- Card List -->
							<div class="space-y-3">
								{#each cardsItems as card (card.id)}
									<div class="rounded-2xl border border-gv2-border/30 bg-gradient-to-br from-gv2-bg-hover/50 to-gv2-bg-hover/20 p-4">
										<div class="flex items-center justify-between mb-3">
											<div class="flex items-center gap-3">
												<div class="flex h-10 w-10 items-center justify-center rounded-xl {card.status === 'active' ? 'bg-[#635BFF]/20 text-[#635BFF]' : card.status === 'inactive' ? 'bg-amber-500/20 text-amber-400' : 'bg-gray-500/20 text-gray-400'}">
													<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="1" y="4" width="22" height="16" rx="2" /><line x1="1" y1="10" x2="23" y2="10" /></svg>
												</div>
												<div>
													<p class="text-[15px] font-bold text-gv2-text-primary">•••• {card.last4}</p>
													<p class="text-[12px] text-gv2-text-muted">{card.cardType === 'physical' ? 'Physical' : 'Virtual'} · {card.currency.toUpperCase()}</p>
												</div>
											</div>
											<span class="rounded-full px-2.5 py-0.5 text-[11px] font-bold {card.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' : card.status === 'inactive' ? 'bg-amber-500/20 text-amber-400' : 'bg-gray-500/20 text-gray-400'}">
												{card.status === 'active' ? '有効' : card.status === 'inactive' ? '停止中' : '解約済み'}
											</span>
										</div>

										{#if card.cardholderName}
											<p class="text-[13px] text-gv2-text-muted mb-2">{card.cardholderName}</p>
										{/if}

										{#if card.spendingLimit}
											<div class="text-[12px] text-gv2-text-muted mb-3">
												利用上限: {card.currency === 'jpy' ? '¥' : ''}{card.spendingLimit.amount.toLocaleString()} / {card.spendingLimit.interval === 'monthly' ? '月' : card.spendingLimit.interval === 'daily' ? '日' : card.spendingLimit.interval}
											</div>
										{/if}

										{#if card.status !== 'canceled'}
											<div class="flex gap-2">
												{#if card.status === 'active'}
													<button
														type="button"
														class="flex-1 rounded-xl bg-gv2-bg-hover py-2.5 text-center text-[13px] font-bold text-gv2-text-muted touch-manipulation active:scale-[0.98] transition-transform"
														onclick={() => { playTap(); haptic('medium'); void freezeCard(card.id); }}
													>
														一時停止
													</button>
												{:else if card.status === 'inactive'}
													<button
														type="button"
														class="flex-1 rounded-xl bg-[#635BFF] py-2.5 text-center text-[13px] font-bold text-white touch-manipulation active:scale-[0.98] transition-transform"
														onclick={() => { playTap(); haptic('medium'); void unfreezeCard(card.id); }}
													>
														再開
													</button>
												{/if}
											</div>
										{/if}
									</div>
								{/each}
							</div>

							<!-- Info -->
							<div class="mt-4 rounded-xl bg-gv2-bg-hover/30 p-4">
								<p class="text-[13px] text-gv2-text-muted">Stripe Issuing によるカード管理。DM で Cards agent に話しかけると、カード発行・利用上限変更・取引照会などが可能です。</p>
							</div>
						{:else}
							<!-- No Cards — CTA -->
							<div class="flex flex-col items-center gap-5 py-8">
								<div class="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-[#635BFF]/20 to-[#635BFF]/10">
									<svg class="h-10 w-10 text-[#635BFF]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="1" y="4" width="22" height="16" rx="2" /><line x1="1" y1="10" x2="23" y2="10" /></svg>
								</div>
								<div class="text-center">
									<h3 class="text-[17px] font-bold text-gv2-text-primary">カードを発行する</h3>
									<p class="mt-1 max-w-[280px] text-[14px] text-gv2-text-muted">Stripe Issuing で virtual/physical カードを即時発行。利用制限・取引監視をリアルタイムで管理。</p>
								</div>

								<button
									type="button"
									class="min-h-[48px] w-full max-w-[320px] rounded-full bg-[#635BFF] px-8 py-3 text-[15px] font-bold text-white tap-target-44 touch-manipulation active:scale-95 transition-transform"
									style="box-shadow: 0 4px 20px rgba(99, 91, 255, 0.3)"
									onclick={() => { playTap(); haptic('medium'); goto('/profile/did:web:cards.etzhayyim.com'); }}
								>
									Cards agent に相談
								</button>
								<p class="text-[11px] text-gv2-text-muted/60">Stripe Issuing by etzhayyim</p>
							</div>
						{/if}
					</div>
				{:else if activeTab === 'posts' || activeTab === 'replies' || activeTab === 'media'}
					{#if postsLoading}
						<div class="p-4 space-y-4">
							{#each { length: 3 } as _}
								<div class="flex gap-3">
									<Skeleton variant="circular" class="h-11 w-11 flex-shrink-0" />
									<div class="flex-1 space-y-2">
										<Skeleton variant="text" class="w-3/4" />
										<Skeleton variant="text" class="w-full" />
									</div>
								</div>
							{/each}
						</div>
					{:else if filteredPosts.length === 0}
						<!-- Empty state (Nintendo style) -->
						<div class="flex flex-col items-center gap-4 py-20 text-center">
							<div class="text-5xl empty-bob">✏️</div>
							<p class="text-[15px] text-white/50">まだ投稿がありません</p>
							{#if isSelf}
								<button
									type="button"
									class="mt-1 min-h-[40px] rounded-full bg-[var(--gv2-accent,#1185FE)] px-6 py-2.5 text-[14px] font-bold text-white tap-target-44 touch-manipulation active:scale-95 focus-glow transition-transform"
									onclick={() => { playTap(); haptic('light'); }}
									style="box-shadow: 0 4px 16px var(--gv2-accent, #1185FE)44"
								>
									投稿を書く
								</button>
							{/if}
						</div>
					{:else}
						<div class="divide-y divide-gv2-border/20">
							{#each filteredPosts as item, idx (item.post.rkey ?? item.post.uri)}
								{@const record = item.post.record as Record<string, any> | undefined}
								{@const postText = String(item.post.text ?? record?.text ?? '')}
								{@const postFacets = item.post.facets ?? record?.facets ?? []}
								{@const routeActor = postRouteActor(item.post.author, handle)}
								{@const routeRkey = postRkey(item.post)}
								<button
									type="button"
									class="flex w-full gap-3 px-4 py-3 text-left touch-manipulation active:bg-[var(--gv2-accent)]/5 transition-colors duration-150 post-item-enter"
									style="animation-delay: {Math.min(idx * 40, 400)}ms"
									onclick={() => { if (routeActor && routeRkey) { playTap(); haptic('light'); goto(`/profile/${encodeURIComponent(routeActor)}/post/${encodeURIComponent(routeRkey)}`); } }}
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
											<span class="flex-shrink-0 text-[14px] text-gv2-text-muted">@{item.post.author.handle}</span>
											<span class="flex-shrink-0 text-[14px] text-gv2-text-muted">· {timeAgo(item.post.indexedAt)}</span>
										</div>
										{#if item.post.reply}
											<div class="mt-0.5 text-[13px] text-gv2-text-muted">
												返信先: @{item.post.reply.parent?.uri?.split('/').at(-3)?.slice(0, 12) ?? '...'}
											</div>
										{/if}
										<div class="mt-0.5 text-[15px] leading-relaxed text-gv2-text-primary">
											<RichText text={postText} facets={postFacets} />
										</div>
										<!-- Action icons -->
										<div class="mt-2 flex items-center justify-between text-gv2-text-muted">
											<div class="flex items-center gap-6">
												<!-- Reply -->
												<div class="flex items-center gap-1">
													<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
													{#if item.post.replyCount}<span class="text-[13px]">{item.post.replyCount}</span>{/if}
												</div>
												<!-- Repost -->
												<div class="flex items-center gap-1">
													<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 014-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 01-4 4H3" /></svg>
													{#if item.post.repostCount}<span class="text-[13px]">{item.post.repostCount}</span>{/if}
												</div>
												<!-- Like -->
												<div class="flex items-center gap-1">
													<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" /></svg>
													{#if item.post.likeCount}<span class="text-[13px]">{item.post.likeCount}</span>{/if}
												</div>
												<!-- View count -->
												<div class="flex items-center gap-1">
													<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/></svg>
													{#if item.post.viewCount > 0}<span class="text-[13px]">{item.post.viewCount}</span>{/if}
												</div>
											</div>
											<div class="flex items-center gap-4">
												<!-- Bookmark -->
												<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" /></svg>
												<!-- Share -->
												<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8" /><polyline points="16 6 12 2 8 6" /><line x1="12" y1="2" x2="12" y2="15" /></svg>
												<!-- More -->
												<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="19" cy="12" r="1.5" /></svg>
											</div>
										</div>
									</div>
								</button>
							{/each}
						</div>
					{/if}
				{:else}
					<!-- Other tabs empty state -->
					<div class="flex flex-col items-center gap-3 py-20 text-center">
						<svg class="h-16 w-16 text-gv2-text-muted/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
							<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
							<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
						</svg>
						<p class="text-[15px] text-gv2-text-muted">まだ投稿がありません</p>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

<!-- Edit Profile Modal (Bluesky style) -->
{#if showEditProfile}
	<div class="fixed inset-0 z-[70] flex items-start justify-center bg-black/60 pt-16" transition:fade={{ duration: 200 }}>
		<div
			class="mx-4 w-full max-w-[420px] rounded-2xl bg-gv2-bg-primary shadow-2xl"
			transition:fly={{ y: 40, duration: 250 }}
		>
			<!-- Header -->
			<div class="flex items-center justify-between border-b border-gv2-border/30 px-4 py-3">
				<button
					type="button"
					class="text-[15px] font-medium text-[#1185FE] touch-manipulation active:opacity-70"
					onclick={() => { showEditProfile = false; }}
				>
					キャンセル
				</button>
				<span class="text-[17px] font-bold text-gv2-text-primary">プロフィールを編集</span>
				<button
					type="button"
					class="text-[15px] font-semibold text-gv2-text-muted touch-manipulation active:opacity-70 disabled:opacity-30"
					disabled={editSaving}
					onclick={() => void saveProfile()}
				>
					{editSaving ? '...' : '保存'}
				</button>
			</div>

			<div class="p-4">
				<!-- Banner area (placeholder) -->
				<div class="relative mb-4 h-24 rounded-xl bg-gv2-bg-hover/50">
					<button type="button" class="absolute right-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-gv2-bg-primary/80 text-gv2-text-muted" aria-label="バナー変更">
						<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" /></svg>
					</button>
				</div>

				<!-- Avatar with camera badge -->
				<div class="relative -mt-14 ml-2 mb-4 inline-block">
					<Avatar
						src={avatarUrl || undefined}
						fallback={(editDisplayName || handle || '?').slice(0, 2).toUpperCase()}
						size="lg"
						class="!h-16 !w-16 !text-xl ring-4 ring-gv2-bg-primary"
					/>
					<div class="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-gv2-bg-hover text-gv2-text-muted">
						<svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" /><circle cx="12" cy="13" r="4" /></svg>
					</div>
				</div>

				<!-- Display name -->
				<div class="mb-4">
					<label class="mb-1 block text-[13px] font-medium text-gv2-text-muted" for="edit-name">表示名</label>
					<input
						id="edit-name"
						type="text"
						class="w-full rounded-xl border border-gv2-border bg-gv2-bg-hover/30 px-4 py-3 text-[15px] text-gv2-text-primary outline-none placeholder:text-gv2-text-muted/50 focus:border-[#1185FE]"
						placeholder="例：山田 太郎"
						bind:value={editDisplayName}
					/>
				</div>

				<!-- Bio -->
				<div>
					<label class="mb-1 block text-[13px] font-medium text-gv2-text-muted" for="edit-bio">説明</label>
					<textarea
						id="edit-bio"
						class="w-full resize-none rounded-xl border border-gv2-border bg-gv2-bg-hover/30 px-4 py-3 text-[15px] text-gv2-text-primary outline-none placeholder:text-gv2-text-muted/50 focus:border-[#1185FE]"
						placeholder="あなた自身について少し教えて"
						rows="3"
						bind:value={editBio}
					></textarea>
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- More menu -->
<ActionSheet
	bind:open={showMoreMenu}
	actions={[
		{ label: 'プロフィールへのリンクをコピー', onclick: copyProfileLink },
		{ label: '投稿を検索', onclick: () => { showMoreMenu = false; } },
		...(isSelf ? [] : [
			{ label: viewerMuted ? 'ミュート解除' : 'ミュートする', onclick: toggleMute },
			{ label: viewerBlocked ? 'ブロック解除' : 'ブロックする', onclick: toggleBlock, destructive: !viewerBlocked },
			{ label: 'アカウントを報告', onclick: handleReport, destructive: true },
		]),
	]}
	cancelLabel="キャンセル"
/>

<style>
	.post-item-enter {
		animation: post-slide-in 0.3s ease-out both;
	}
	@keyframes post-slide-in {
		from { opacity: 0; transform: translateY(8px); }
		to { opacity: 1; transform: translateY(0); }
	}
	.empty-bob {
		animation: empty-bob-anim 3s ease-in-out infinite;
	}
	@keyframes empty-bob-anim {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-8px); }
	}
	@media (prefers-reduced-motion: reduce) {
		.post-item-enter, .empty-bob { animation: none; }
	}
</style>
