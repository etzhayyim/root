<script lang="ts">
	import type { Snippet } from 'svelte';
	import { Avatar, Badge, Button, Card, TabBar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { fade, fly } from 'svelte/transition';
	import { playTap, haptic } from '@etzhayyim/design-system/audio';
	import {
		isSignedIn,
		clerkUser,
		displayName,
		currentOrg,
		trustSummary,
	} from '../auth/stores.js';
	import { getSessionToken } from '$lib/auth';
	import { initClerk, signIn } from '../auth/passkey.js';
	import { trustVariantFromScore } from '../auth/trust.js';
	import { getCurrentDID, getAuthorProfile, getAuthorFeed, getActorLikes, getFollowers, getFollows, likePost, unlikePost, repost, unrepost, setProfile, atProcedure } from '$lib/atproto-agent';
	import { graphSql, sqlString } from '$lib/graph-sql';
	import { RichText } from '../w/index.js';
	import type { AuthorProfile, FeedItem, PostView } from '$lib/atproto-agent';

	interface Props {
		/** Extra content after feed tabs (e.g. agent toolbar). */
		extraContent?: Snippet;
		/** Override guest CTA entirely. */
		guestCta?: Snippet;
		/** Settings URL. Default: /settings */
		settingsHref?: string;
		/** Edit profile label. */
		editLabel?: string;
		/** Called when a post is tapped. */
		onPostClick?: (handle: string, rkey: string) => void;
		/** Called when compose is requested. */
		onCompose?: () => void;
	}

	let {
		extraContent,
		guestCta,
		settingsHref = '/settings',
		editLabel = 'Edit Profile',
		onPostClick,
		onCompose,
	}: Props = $props();

	let myProfile = $state<AuthorProfile | null>(null);
	let profileFeedItems = $state<FeedItem[]>([]);
	let profileFeedLoading = $state(false);
	let profileActiveTab = $state('posts');
	let likedItems = $state<Set<string>>(new Set());
	let repostedItems = $state<Set<string>>(new Set());
	let countsHydrating = $state(false);

	// Card state (Stripe Issuing)
	interface IssuedCard {
		id: string;
		cardType: string;
		status: string;
		lastFour: string;
		currency: string;
		spendingLimitAmount: number;
		spendingLimitInterval: string;
		createdAt: string;
	}
	let cardsList = $state<IssuedCard[]>([]);
	let cardsLoading = $state(false);
	let cardsError = $state('');
	let showCardsOnboarding = $state(false);
	let cardIssuing = $state(false);
	let cardChargingId = $state('');
	let chargeAmountByCard = $state<Record<string, string>>({});

	// eSIM state
	interface ESimProfile {
		iccid: string;
		provider: string;
		coverage: string;
		dataRemainingMb: number;
		dataUsedMb: number;
		status: string;
		qrCodeUrl?: string;
		activationCode?: string;
	}
	let esimProfile = $state<ESimProfile | null>(null);
	let esimLoading = $state(false);
	let esimProvisioning = $state(false);
	let esimError = $state('');
	let showEsimOnboarding = $state(false);

	/** Dojo drill results for current user */
	let dojoLoading = $state(false);
	let dojoDrills: Array<{ id: string; title: string; score: number; completedAt: string }> = $state([]);
	let dojoStats: { avgScore: number; totalDrills: number } = $state({ avgScore: 0, totalDrills: 0 });

	const profileTabDefs = [
		{ value: 'posts', label: '投稿' },
		{ value: 'replies', label: '返信' },
		{ value: 'media', label: 'メディア' },
		{ value: 'video', label: 'ビデオ' },
		{ value: 'likes', label: 'いいね' },
		{ value: 'dojo', label: 'Dojo' },
		{ value: 'sim', label: 'SIM' },
		{ value: 'cards', label: 'カード' },
		{ value: 'feeds', label: 'フィード' },
		{ value: 'starter', label: 'スターターパック' },
	];

	async function resolveViewerDid(): Promise<string> {
		const did = await getCurrentDID().catch((error) => {
			console.warn('[silent-fail] ProfilePanel.svelte: getCurrentDID failed', error);
			return '';
		});
		if (did) return did;
		const fallbackDid = $clerkUser?.id ?? '';
		return fallbackDid.startsWith('did:') ? fallbackDid : '';
	}

	// Load AT Protocol profile when signed in
	$effect(() => {
		if (!$isSignedIn) { myProfile = null; profileFeedItems = []; return; }
		resolveViewerDid().then((did) => {
			if (!did) return;
			getAuthorProfile(did).then((p) => {
				myProfile = p;
				// Some migrated profiles intermittently return 0/0/0 despite existing graph/feed data.
				if ((p.followersCount ?? 0) === 0 && (p.followsCount ?? 0) === 0 && (p.postsCount ?? 0) === 0) {
					void hydrateProfileCounts(did);
				}
			}).catch((e) => console.warn('getAuthorProfile failed', e));
			loadProfileFeed('posts_with_replies');
			fetchEsimProfile(did);
		}).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/superapp/ProfilePanel.svelte: suppressed async error", error); });
	});

	async function countPaginated<T>(
		fetchPage: (cursor?: string) => Promise<{ items: T[]; cursor?: string }>,
		maxPages = 20,
	): Promise<number> {
		let cursor: string | undefined;
		let total = 0;
		let pages = 0;
		while (pages < maxPages) {
			const { items, cursor: nextCursor } = await fetchPage(cursor);
			total += items.length;
			pages += 1;
			if (!nextCursor) break;
			cursor = nextCursor;
		}
		return total;
	}

	async function hydrateProfileCounts(did: string) {
		if (!myProfile || countsHydrating) return;
		countsHydrating = true;
		try {
			const [postsCount, followersCount, followsCount] = await Promise.all([
				countPaginated(async (cursor?: string) => {
					const res = await getAuthorFeed(did, { limit: 100, cursor } as any);
					const feed = Array.isArray(res) ? res : (res as any)?.feed ?? [];
					const nextCursor = Array.isArray(res) ? undefined : (res as any)?.cursor;
					return { items: feed, cursor: nextCursor };
				}),
				countPaginated(async (cursor?: string) => {
					const res = await getFollowers(did, { limit: 100, cursor });
					return { items: res.followers ?? [], cursor: res.cursor };
				}),
				countPaginated(async (cursor?: string) => {
					const res = await getFollows(did, { limit: 100, cursor });
					return { items: res.follows ?? [], cursor: res.cursor };
				}),
			]);
			if (!myProfile) return;
			myProfile = {
				...myProfile,
				postsCount: Math.max(myProfile.postsCount ?? 0, postsCount),
				followersCount: Math.max(myProfile.followersCount ?? 0, followersCount),
				followsCount: Math.max(myProfile.followsCount ?? 0, followsCount),
			};
		} catch (e) {
			console.warn('hydrateProfileCounts failed', e);
		} finally {
			countsHydrating = false;
		}
	}

	async function loadProfileFeed(filter: string) {
		const did = await resolveViewerDid();
		if (!did) return;
		profileFeedLoading = true;
		try {
			const result = await getAuthorFeed(did, { limit: 50, filter } as any);
			profileFeedItems = Array.isArray(result) ? result : (result as any).feed ?? [];
			for (const fi of profileFeedItems) {
				if (fi.post.viewerLike) likedItems.add(fi.post.uri);
				if (fi.post.viewerRepost) repostedItems.add(fi.post.uri);
			}
		} catch {
			profileFeedItems = [];
		} finally {
			profileFeedLoading = false;
		}
	}

	async function handleProfileTabChange(tabId: string) {
		profileActiveTab = tabId;
		if (tabId === 'cards') {
			const did = await resolveViewerDid();
			if (did) void fetchCards(did);
			return;
		} else if (tabId === 'sim') {
			const did = await resolveViewerDid();
			if (did) void fetchEsimProfile(did);
			return;
		} else if (tabId === 'dojo') {
			const did = await resolveViewerDid();
			if (did) void fetchDojoDrills(did);
			return;
		} else if (tabId === 'likes') {
			const did = await resolveViewerDid();
			if (!did) return;
			profileFeedLoading = true;
			try {
				const result = await getActorLikes(did, { limit: 50 });
				profileFeedItems = Array.isArray(result) ? result : (result as any).feed ?? [];
			} catch { profileFeedItems = []; }
			finally { profileFeedLoading = false; }
		} else {
			const filterMap: Record<string, string> = { posts: 'posts_with_replies', replies: 'posts_with_replies', media: 'posts_with_media' };
			await loadProfileFeed(filterMap[tabId] ?? 'posts_with_replies');
		}
	}

	/** Fetch dojo drill completions for the given DID */
	async function fetchDojoDrills(userDid: string) {
		dojoLoading = true;
		try {
			const token = await getSessionToken().catch((_err) => null);
			if (!token) {
				dojoDrills = [];
				dojoStats = { avgScore: 0, totalDrills: 0 };
				return;
			}
			const rows = await graphSql<Record<string, unknown>>(`
				SELECT value_json, created_at
				FROM vertex_dojo_step_completed_event
				WHERE actor_did = ${sqlString(userDid)}
				ORDER BY created_at DESC
				LIMIT 50
			`);
			dojoDrills = rows.map((r) => {
				let rec: Record<string, unknown> = {};
				try { rec = JSON.parse(String(r.value_json ?? '{}')); } catch { rec = {}; }
				return {
					id: String(rec.id ?? rec.stepId ?? ''),
					title: String(rec.title ?? rec.stepTitle ?? 'Drill'),
					score: Number(rec.score ?? rec.finalScore ?? 0),
					completedAt: String(rec.completedAt ?? r.created_at ?? ''),
				};
			});
			if (dojoDrills.length > 0) {
				const total = dojoDrills.reduce((sum, d) => sum + d.score, 0);
				dojoStats = { avgScore: Math.round(total / dojoDrills.length), totalDrills: dojoDrills.length };
			} else {
				dojoStats = { avgScore: 0, totalDrills: 0 };
			}
		} catch (err) {
			console.warn('fetchDojoDrills failed', err);
			dojoDrills = [];
			dojoStats = { avgScore: 0, totalDrills: 0 };
		} finally {
			dojoLoading = false;
		}
	}

	function timeAgo(ts: string): string {
		const date = new Date(ts);
		if (Number.isNaN(date.getTime())) return '';
		const diff = Date.now() - date.getTime();
		const mins = Math.max(0, Math.floor(diff / 60000));
		if (mins < 60) return `${mins}m`;
		const hrs = Math.floor(mins / 60);
		if (hrs < 24) return `${hrs}h`;
		return `${Math.floor(hrs / 24)}d`;
	}

	function isLiked(post: PostView): boolean {
		return likedItems.has(post.uri) || !!post.viewerLike;
	}

	function isReposted(post: PostView): boolean {
		return repostedItems.has(post.uri) || !!post.viewerRepost;
	}

	async function handleLike(e: Event, post: PostView) {
		e.stopPropagation();
		const uri = post.uri;
		if (isLiked(post)) {
			const next = new Set(likedItems); next.delete(uri); likedItems = next;
			try { await unlikePost(post.viewerLike || uri); } catch (err) { console.warn('unlikePost failed', err); }
		} else {
			likedItems = new Set([...likedItems, uri]);
			try { await likePost(uri, post.cid); } catch (err) { console.warn('likePost failed', err); }
		}
	}

	async function handleRepost(e: Event, post: PostView) {
		e.stopPropagation();
		const uri = post.uri;
		if (isReposted(post)) {
			const next = new Set(repostedItems); next.delete(uri); repostedItems = next;
			try { await unrepost(post.viewerRepost || uri); } catch (err) { console.warn('unrepost failed', err); }
		} else {
			repostedItems = new Set([...repostedItems, uri]);
			try { await repost(uri, post.cid); } catch (err) { console.warn('repost failed', err); }
		}
	}

	async function handleSignIn() {
		await initClerk({ publishableKey: '', accountsBaseUrl: 'https://auth.etzhayyim.com' }).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/superapp/ProfilePanel.svelte: suppressed async error", error); });
		await signIn();
	}

	// Edit profile modal
	let showEditProfile = $state(false);
	let editDisplayName = $state('');
	let editBio = $state('');
	let editSaving = $state(false);

	function openEditProfile() {
		editDisplayName = myProfile?.displayName ?? $displayName ?? '';
		editBio = myProfile?.description ?? '';
		showEditProfile = true;
	}

	async function fetchEsimProfile(_userDid: string) {
		esimLoading = true;
		esimError = '';
		try {
			const result = await atProcedure<{ rows?: Record<string, unknown>[] }>('com.etzhayyim.apps.celler.getEsimProfile', {});
			if (result?.rows?.[0]) {
				const row = result.rows[0];
				esimProfile = {
					iccid: String(row.iccid ?? ''),
					provider: String(row.provider ?? 'telnyx'),
					coverage: String(row.coverage ?? 'global'),
					dataRemainingMb: Number(row.dataRemainingMb ?? 0),
					dataUsedMb: Number(row.dataUsedMb ?? 0),
					status: String(row.status ?? 'unknown'),
					qrCodeUrl: row.qrCodeUrl ? String(row.qrCodeUrl) : undefined,
					activationCode: row.activationCode ? String(row.activationCode) : undefined,
				};
			} else {
				esimProfile = null;
				showEsimOnboarding = true;
			}
		} catch (e) {
			console.warn('fetchEsimProfile failed', e);
			esimProfile = null;
		} finally {
			esimLoading = false;
		}
	}

	async function provisionEsim() {
		esimProvisioning = true;
		esimError = '';
		try {
			const userDid = await resolveViewerDid();
			const result = await atProcedure<Record<string, unknown>>('com.etzhayyim.apps.celler.provisionEsim', {
				did: userDid,
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

	// Card functions (Stripe Issuing)
	async function fetchCards(_userDid: string) {
		cardsLoading = true;
		cardsError = '';
		try {
			const userDid = await resolveViewerDid();
			const result = await atProcedure<{ items?: IssuedCard[] }>('com.etzhayyim.apps.stripe.listCards', { userId: userDid });
			if (result?.items && result.items.length > 0) {
				cardsList = result.items.map((raw: any) => ({
					id: String(raw.id ?? ''),
					cardType: String(raw.cardType ?? raw.card_type ?? 'virtual'),
					status: String(raw.status ?? 'unknown'),
					lastFour: String(raw.lastFour ?? raw.last_four ?? ''),
					currency: String(raw.currency ?? 'jpy'),
					spendingLimitAmount: Number(raw.spendingLimitAmount ?? raw.spending_limit_amount ?? 0),
					spendingLimitInterval: String(raw.spendingLimitInterval ?? raw.spending_limit_interval ?? ''),
					createdAt: String(raw.createdAt ?? raw.created_at ?? ''),
				}));
				showCardsOnboarding = false;
			} else {
				cardsList = [];
				showCardsOnboarding = true;
			}
		} catch (e) {
			console.warn('fetchCards failed', e);
			cardsList = [];
			showCardsOnboarding = true;
		} finally {
			cardsLoading = false;
		}
	}

	function toStripeErrorCode(value: unknown): string {
		return String(value ?? '').replaceAll('_', '').toLowerCase();
	}

	function prettyStripeError(code: unknown): string {
		const normalized = toStripeErrorCode(code);
		if (normalized === 'nocardholder') return 'カードホルダー登録が必要です';
		if (normalized === 'authtierinsufficient') return '本人確認が必要です (Verified 以上)';
		return String(code ?? 'カードの発行に失敗しました');
	}

	async function ensureStripeCardholder(userDid: string): Promise<boolean> {
		const name = String(myProfile?.displayName ?? $displayName ?? 'User');
		const email = String(
			($clerkUser as any)?.primaryEmailAddress?.emailAddress
			?? ($clerkUser as any)?.emailAddresses?.[0]?.emailAddress
			?? '',
		);
		if (!email) {
			cardsError = 'カードホルダー作成に必要なメールアドレスが見つかりません';
			return false;
		}
		const created = await atProcedure<Record<string, unknown>>('com.etzhayyim.apps.stripe.createCardholder', {
			userId: userDid,
			name,
			email,
		});
		if (created?.error) {
			cardsError = prettyStripeError(created.error);
			return false;
		}
		return true;
	}

	async function issueVirtualCard() {
		cardIssuing = true;
		cardsError = '';
		try {
			const userDid = await resolveViewerDid();
			let result = await atProcedure<Record<string, unknown>>('com.etzhayyim.apps.stripe.issueCard', {
				userId: userDid,
				cardType: 'virtual',
				currency: 'jpy',
			});
			if (toStripeErrorCode(result?.error) === 'nocardholder') {
				const ready = await ensureStripeCardholder(userDid);
				if (ready) {
					result = await atProcedure<Record<string, unknown>>('com.etzhayyim.apps.stripe.issueCard', {
						userId: userDid,
						cardType: 'virtual',
						currency: 'jpy',
					});
				}
			}
			if (result?.error) {
				cardsError = prettyStripeError(result.error);
			} else if (result?.card) {
				const raw = result.card as any;
				const card: IssuedCard = {
					id: String(raw.id ?? ''),
					cardType: String(raw.cardType ?? raw.card_type ?? 'virtual'),
					status: String(raw.status ?? 'unknown'),
					lastFour: String(raw.lastFour ?? raw.last_four ?? ''),
					currency: String(raw.currency ?? 'jpy'),
					spendingLimitAmount: Number(raw.spendingLimitAmount ?? raw.spending_limit_amount ?? 0),
					spendingLimitInterval: String(raw.spendingLimitInterval ?? raw.spending_limit_interval ?? ''),
					createdAt: String(raw.createdAt ?? raw.created_at ?? ''),
				};
				cardsList = [card, ...cardsList];
				showCardsOnboarding = false;
			}
		} catch (e) {
			cardsError = e instanceof Error ? e.message : 'カードの発行に失敗しました';
			console.warn('issueVirtualCard failed', e);
		} finally {
			cardIssuing = false;
		}
	}

	async function toggleCardFreeze(card: IssuedCard) {
		try {
				const userDid = await resolveViewerDid();
				if (card.status === 'active') {
					await atProcedure('com.etzhayyim.apps.stripe.freezeCard', { userId: userDid, cardId: card.id });
					cardsList = cardsList.map(c => c.id === card.id ? { ...c, status: 'inactive' } : c);
				} else if (card.status === 'inactive') {
					await atProcedure('com.etzhayyim.apps.stripe.unfreezeCard', { userId: userDid, cardId: card.id });
					cardsList = cardsList.map(c => c.id === card.id ? { ...c, status: 'active' } : c);
				}
		} catch (e) {
			console.warn('toggleCardFreeze failed', e);
		}
	}

	function setChargeAmount(cardId: string, value: string): void {
		chargeAmountByCard = { ...chargeAmountByCard, [cardId]: value };
	}

	async function chargeCard(card: IssuedCard): Promise<void> {
		const userDid = await resolveViewerDid();
		if (!userDid) {
			cardsError = 'ユーザー識別子の取得に失敗しました';
			return;
		}
		const amount = Math.round(Number(chargeAmountByCard[card.id] ?? 0));
		if (!Number.isFinite(amount) || amount <= 0) {
			cardsError = 'チャージ金額は 1 以上で入力してください';
			return;
		}

		cardChargingId = card.id;
		cardsError = '';
		try {
			const result = await atProcedure<Record<string, unknown>>('com.etzhayyim.apps.stripe.assignCardCredits', {
				userId: userDid,
				cardId: card.id,
				amount,
			});
			if (result?.error) {
				cardsError = prettyStripeError(result.error);
				return;
			}
			setChargeAmount(card.id, '');
		} catch (e) {
			cardsError = e instanceof Error ? e.message : 'チャージに失敗しました';
			console.warn('chargeCard failed', e);
		} finally {
			cardChargingId = '';
		}
	}

	async function saveProfile() {
		editSaving = true;
		try {
			await setProfile({ displayName: editDisplayName, description: editBio });
			const did = await resolveViewerDid();
			if (did) myProfile = await getAuthorProfile(did);
			showEditProfile = false;
		} catch (e) {
			console.warn('profile: saveProfile failed', e);
		} finally {
			editSaving = false;
		}
	}
</script>

<div class="flex flex-col gap-0">
	{#if $isSignedIn && $clerkUser}
		<!-- AT Protocol profile header -->
		<div class="px-4 pt-4" in:fade={staggerFade(0, { duration: 200 })}>
			<div class="flex items-start justify-between">
				<Avatar
					src={$clerkUser?.imageUrl || undefined}
					fallback={($displayName || 'U').slice(0, 2).toUpperCase()}
					size="lg"
					class="!h-16 !w-16 !text-xl !bg-[var(--gv2-accent,#58CC02)] !text-white ring-4 ring-gv2-bg-primary"
				/>
				<div class="flex gap-2">
					<button
						type="button"
						class="min-h-[36px] rounded-full border border-gv2-border px-4 py-1.5 text-[14px] font-semibold text-gv2-text-primary tap-target-44 touch-manipulation active:bg-gv2-bg-hover active:scale-[0.97] transition-transform"
						onclick={() => openEditProfile()}
					>
						{editLabel}
					</button>
				</div>
			</div>
			<h1 class="mt-3 text-[22px] font-black text-gv2-text-primary leading-tight">{myProfile?.displayName || $displayName || 'User'}</h1>
			<div class="mt-0.5 text-[14px] text-gv2-text-muted">@{myProfile?.handle || $clerkUser?.username || 'user'}</div>
			{#if myProfile?.description}
				<p class="mt-1 text-[14px] text-gv2-text-secondary leading-snug">{myProfile.description}</p>
			{/if}
			<div class="mt-2 flex items-center gap-1 text-[14px]">
				<span class="font-bold text-gv2-text-primary">{myProfile?.followersCount ?? 0}</span>
				<span class="text-gv2-text-muted">followers</span>
				<span class="mx-1 font-bold text-gv2-text-primary">{myProfile?.followsCount ?? 0}</span>
				<span class="text-gv2-text-muted">following</span>
				<span class="mx-1 font-bold text-gv2-text-primary">{myProfile?.postsCount ?? 0}</span>
				<span class="text-gv2-text-muted">posts</span>
			</div>
			<!-- Trust & org -->
			<div class="mt-2 flex items-center gap-2">
				<Badge value={`T${$trustSummary.score}`} variant={trustVariantFromScore($trustSummary.score)} />
				{#if $currentOrg?.name}
					<span class="text-[12px] text-gv2-text-muted">{$currentOrg.name}</span>
				{/if}
			</div>
		</div>

		<!-- eSIM Onboarding Banner -->
		{#if showEsimOnboarding && !esimProfile && profileActiveTab !== 'sim'}
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
					onclick={() => { playTap(); haptic('light'); profileActiveTab = 'sim'; void handleProfileTabChange('sim'); }}
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

		<!-- Feed tabs -->
		<TabBar
			tabs={profileTabDefs}
			bind:activeValue={profileActiveTab}
			onchange={(v) => void handleProfileTabChange(v)}
			class="mt-3"
		/>

		<!-- Tab content -->
		<div>
			{#if profileActiveTab === 'cards'}
				<!-- Card Management Tab (Stripe Issuing) -->
				<div class="px-4 py-6">
					{#if cardsLoading}
						<div class="flex flex-col items-center gap-4 py-12">
							<div class="h-12 w-12 animate-pulse rounded-full bg-violet-500/20"></div>
							<Skeleton variant="text" class="w-48" />
							<Skeleton variant="text" class="w-32" />
						</div>
					{:else if cardsList.length > 0}
						<!-- Card List -->
						<div class="space-y-4">
							{#each cardsList as card (card.id)}
								<div class="rounded-2xl border border-gv2-border/30 bg-gradient-to-br from-gv2-bg-hover/50 to-gv2-bg-hover/20 p-5">
									<div class="flex items-center justify-between mb-3">
										<div class="flex items-center gap-3">
											<div class="flex h-12 w-12 items-center justify-center rounded-xl {card.cardType === 'physical' ? 'bg-amber-500/20 text-amber-400' : 'bg-violet-500/20 text-violet-400'}">
												<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="1" y="4" width="22" height="16" rx="2" /><path d="M1 10h22" /></svg>
											</div>
											<div>
													<p class="text-[15px] font-bold text-gv2-text-primary">{card.cardType === 'physical' ? 'Physical Card' : 'Virtual Card'}</p>
													<p class="text-[13px] text-gv2-text-muted font-mono">**** {card.lastFour}</p>
											</div>
										</div>
										<span class="rounded-full px-3 py-1 text-[12px] font-bold {card.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' : card.status === 'inactive' ? 'bg-amber-500/20 text-amber-400' : 'bg-gray-500/20 text-gray-400'}">
											{card.status === 'active' ? '有効' : card.status === 'inactive' ? '凍結中' : card.status === 'canceled' ? '取消済み' : card.status}
										</span>
									</div>

										{#if card.spendingLimitAmount > 0}
											<div class="mb-3 text-[13px] text-gv2-text-muted">
												<span>利用限度: {card.currency.toUpperCase()} {card.spendingLimitAmount.toLocaleString()} / {card.spendingLimitInterval === 'monthly' ? '月' : card.spendingLimitInterval}</span>
											</div>
										{/if}

										{#if card.status !== 'canceled'}
											<div class="space-y-3">
												<div class="rounded-xl border border-gv2-border/25 bg-gv2-bg-hover/40 p-3">
													<p class="mb-2 text-[12px] font-semibold text-gv2-text-muted">クレジットをチャージ</p>
													<div class="flex items-center gap-2">
														<input
															type="number"
															min="1"
															step="1"
															inputmode="numeric"
															placeholder="1000"
															class="h-11 flex-1 rounded-xl border border-gv2-border/40 bg-gv2-bg-primary px-3 text-[14px] text-gv2-text-primary outline-none focus:border-violet-500/70"
															value={chargeAmountByCard[card.id] ?? ''}
															oninput={(e) => setChargeAmount(card.id, (e.currentTarget as HTMLInputElement).value)}
														/>
														<button
															type="button"
															class="h-11 rounded-xl bg-violet-500 px-4 text-[13px] font-bold text-white touch-manipulation active:scale-[0.98] transition-transform disabled:opacity-50"
															onclick={() => { playTap(); haptic('light'); void chargeCard(card); }}
															disabled={cardChargingId === card.id}
														>
															{cardChargingId === card.id ? '処理中...' : 'チャージ'}
														</button>
													</div>
												</div>
											<div class="flex gap-3">
												<button
													type="button"
													class="flex-1 rounded-xl {card.status === 'active' ? 'bg-gv2-bg-hover' : 'bg-violet-500'} py-3 text-center text-[14px] font-bold {card.status === 'active' ? 'text-gv2-text-muted' : 'text-white'} touch-manipulation active:scale-[0.98] transition-transform"
													onclick={() => { playTap(); haptic('medium'); void toggleCardFreeze(card); }}
												>
													{card.status === 'active' ? '凍結する' : '解除する'}
												</button>
											</div>
											</div>
										{/if}
								</div>
							{/each}
						</div>

						<!-- Issue another card CTA -->
						<button
							type="button"
							class="mt-4 w-full rounded-xl border-2 border-dashed border-gv2-border/40 py-4 text-center text-[14px] font-semibold text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover transition-colors"
							onclick={() => { playTap(); haptic('medium'); void issueVirtualCard(); }}
							disabled={cardIssuing}
						>
							{cardIssuing ? '発行中...' : '+ バーチャルカードを追加'}
						</button>
					{:else}
						<!-- No Cards — Issue CTA -->
						<div class="flex flex-col items-center gap-5 py-8">
							<div class="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-violet-500/20 to-indigo-500/20">
								<svg class="h-10 w-10 text-violet-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="1" y="4" width="22" height="16" rx="2" /><path d="M1 10h22" /></svg>
							</div>
							<div class="text-center">
								<h3 class="text-[17px] font-bold text-gv2-text-primary">カードを発行しよう</h3>
								<p class="mt-1 max-w-[280px] text-[14px] text-gv2-text-muted">Murakumo クレジットで使えるバーチャルカード。オンライン決済に即利用可能。</p>
							</div>

							<div class="w-full max-w-[320px] space-y-2">
								<div class="flex items-center justify-between rounded-xl border border-gv2-border/20 bg-gv2-bg-hover/30 p-4">
									<div class="flex items-center gap-3">
										<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/20 text-violet-400">
											<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" /></svg>
										</div>
										<span class="text-[14px] text-gv2-text-primary font-medium">Virtual Card</span>
									</div>
									<span class="text-violet-400 font-bold text-[14px]">無料</span>
								</div>
								<div class="flex items-center justify-between rounded-xl border border-gv2-border/20 bg-gv2-bg-hover/30 p-4">
									<div class="flex items-center gap-3">
										<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400">
											<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" /><path d="M1 10h22" /></svg>
										</div>
										<span class="text-[14px] text-gv2-text-primary font-medium">Physical Card</span>
									</div>
									<span class="text-amber-400 font-bold text-[14px]">500 credits</span>
								</div>
							</div>

							{#if cardsError}
								<p class="text-[13px] text-red-400">{cardsError}</p>
							{/if}

							<button
								type="button"
								class="min-h-[48px] w-full max-w-[320px] rounded-full bg-violet-500 px-8 py-3 text-[15px] font-bold text-white tap-target-44 touch-manipulation active:scale-95 transition-transform disabled:opacity-40"
								style="box-shadow: 0 4px 20px rgba(139, 92, 246, 0.3)"
								disabled={cardIssuing}
								onclick={() => { playTap(); haptic('medium'); void issueVirtualCard(); }}
							>
								{cardIssuing ? '発行中...' : 'バーチャルカードを発行する'}
							</button>

							<p class="text-[11px] text-gv2-text-muted/60">Stripe Issuing / Murakumo Credits</p>
						</div>
					{/if}
				</div>
			{:else if profileActiveTab === 'dojo'}
				<!-- Dojo Drills Tab -->
				<div class="px-4 py-6">
					{#if dojoLoading}
						<div class="flex flex-col items-center gap-4 py-12">
							<div class="h-12 w-12 animate-pulse rounded-full bg-emerald-500/20"></div>
							<Skeleton variant="text" class="w-48" />
							<Skeleton variant="text" class="w-32" />
						</div>
					{:else if dojoDrills.length > 0}
						<!-- Stats Summary -->
						<div class="mb-4 flex items-center gap-4 rounded-2xl border border-gv2-border/30 bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 p-4">
							<div class="flex h-14 w-14 items-center justify-center rounded-xl bg-emerald-500/20">
								<svg class="h-7 w-7 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2L2 7l10 5 10-5-10-5z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" /></svg>
							</div>
							<div>
								<p class="text-[17px] font-bold text-gv2-text-primary">Avg {dojoStats.avgScore}%</p>
								<p class="text-[13px] text-gv2-text-muted">{dojoStats.totalDrills} drills completed</p>
							</div>
						</div>
						<!-- Drill List -->
						<div class="space-y-3">
							{#each dojoDrills as drill (drill.id)}
								<div class="rounded-xl border border-gv2-border/20 bg-gv2-bg-hover/30 p-4">
									<div class="flex items-center justify-between">
										<p class="text-[14px] font-medium text-gv2-text-primary">{drill.title}</p>
										<span class="rounded-full px-2.5 py-0.5 text-[12px] font-bold {drill.score >= 80 ? 'bg-emerald-500/20 text-emerald-400' : drill.score >= 60 ? 'bg-amber-500/20 text-amber-400' : 'bg-red-500/20 text-red-400'}">
											{drill.score}%
										</span>
									</div>
									{#if drill.completedAt}
										<p class="mt-1 text-[12px] text-gv2-text-muted">{timeAgo(drill.completedAt)}</p>
									{/if}
								</div>
							{/each}
						</div>
					{:else}
						<!-- No Drills -->
						<div class="flex flex-col items-center gap-5 py-8">
							<div class="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500/20 to-cyan-500/20">
								<svg class="h-10 w-10 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M12 2L2 7l10 5 10-5-10-5z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" /></svg>
							</div>
							<div class="text-center">
								<h3 class="text-[17px] font-bold text-gv2-text-primary">Dojo</h3>
								<p class="mt-1 max-w-[280px] text-[14px] text-gv2-text-muted">Readiness kata ドリルを完了して、スコアを上げよう。</p>
							</div>
						</div>
					{/if}
				</div>
			{:else if profileActiveTab === 'sim'}
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
			{:else if profileFeedLoading}
				<div class="p-4 space-y-4">
					{#each { length: 3 } as _}
						<div class="flex gap-3">
							<Skeleton variant="circular" class="h-11 w-11 flex-shrink-0" />
							<div class="flex-1 space-y-2">
								<Skeleton variant="text" class="h-4 w-3/4" />
								<Skeleton variant="text" class="h-4 w-full" />
							</div>
						</div>
					{/each}
				</div>
			{:else if profileFeedItems.length === 0}
				<div class="flex flex-col items-center gap-3 py-20 text-center" in:fade={staggerFade(2, { duration: 200 })}>
					<p class="text-[15px] text-gv2-text-muted">No posts yet</p>
					{#if onCompose}
						<button
							type="button"
							class="mt-1 min-h-[40px] rounded-full bg-[var(--gv2-accent,#1185FE)] px-5 py-2 text-[14px] font-bold text-white tap-target-44 touch-manipulation active:opacity-80"
							onclick={onCompose}
						>
							Create post
						</button>
					{/if}
				</div>
			{:else}
				<div class="divide-y divide-gv2-border/20">
					{#each profileFeedItems as item (item.post.rkey ?? item.post.uri)}
						{@const post = item.post}
						<div class="flex w-full gap-3 px-4 py-3 text-left touch-manipulation active:bg-[var(--gv2-accent)]/5 transition-colors duration-150">
							<button
								type="button"
								class="flex-shrink-0"
								onclick={() => { playTap(); haptic('light'); onPostClick?.(post.author.handle || '', post.rkey); }}
							>
								<Avatar
									src={post.author.avatar || undefined}
									fallback={(post.author.displayName || post.author.handle || '?').slice(0, 2).toUpperCase()}
									size="md"
									class="!h-11 !w-11"
								/>
							</button>
							<div class="min-w-0 flex-1">
								<button
									type="button"
									class="w-full text-left"
									onclick={() => { playTap(); haptic('light'); onPostClick?.(post.author.handle || '', post.rkey); }}
								>
									<div class="flex items-center gap-1.5">
										<span class="truncate text-[15px] font-bold text-gv2-text-primary">{post.author.displayName || post.author.handle}</span>
										<span class="flex-shrink-0 text-[14px] text-gv2-text-muted">@{post.author.handle}</span>
										<span class="flex-shrink-0 text-[14px] text-gv2-text-muted">· {timeAgo(post.indexedAt)}</span>
									</div>
									<div class="mt-0.5 text-[15px] leading-relaxed text-gv2-text-primary">
										<RichText text={post.text ?? ''} facets={post.facets ?? []} />
									</div>
								</button>
								<!-- Action bar: Reply / Repost / Like -->
								<div class="mt-2 flex items-center text-gv2-text-muted">
									<div class="flex flex-1 items-center">
										<button type="button" class="group -ml-2 flex items-center gap-1 rounded-full px-2 py-1.5 touch-manipulation transition-colors active:bg-[#1185FE]/10" aria-label="Reply" onclick={() => { playTap(); onPostClick?.(post.author.handle || '', post.rkey); }}>
											<svg class="h-[18px] w-[18px] transition-colors group-active:text-[#1185FE]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
											{#if post.replyCount}<span class="text-[13px]">{post.replyCount}</span>{/if}
										</button>
										<button
											type="button"
											class="group flex items-center gap-1 rounded-full px-2 py-1.5 touch-manipulation transition-colors active:bg-[#00BA7C]/10 {isReposted(post) ? 'text-[#00BA7C]' : ''}"
											onclick={(e) => { playTap(); handleRepost(e, post); }}
											aria-label="Repost"
										>
											<svg class="h-[18px] w-[18px] transition-colors {isReposted(post) ? 'text-[#00BA7C]' : 'group-active:text-[#00BA7C]'}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 014-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 01-4 4H3" /></svg>
											{#if post.repostCount}<span class="text-[13px]">{post.repostCount}</span>{/if}
										</button>
										<button
											type="button"
											class="group flex items-center gap-1 rounded-full px-2 py-1.5 touch-manipulation transition-colors active:bg-[#F91880]/10 {isLiked(post) ? 'text-[#F91880]' : ''}"
											onclick={(e) => { playTap(); handleLike(e, post); }}
											aria-label="Like"
										>
											<svg class="h-[18px] w-[18px] transition-colors {isLiked(post) ? 'text-[#F91880]' : 'group-active:text-[#F91880]'}" viewBox="0 0 24 24" fill={isLiked(post) ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" /></svg>
											{#if post.likeCount}<span class="text-[13px]">{post.likeCount}</span>{/if}
										</button>
										<div class="flex items-center gap-1 px-2 py-1.5">
											<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/></svg>
											{#if post.viewCount > 0}<span class="text-[13px]">{post.viewCount}</span>{/if}
										</div>
									</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		{#if extraContent}
			{@render extraContent()}
		{/if}

		<!-- Credits link -->
		<div class="p-3">
			<a
				href="/credits"
				class="flex w-full items-center gap-3 rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-4 no-underline touch-manipulation active:bg-gv2-bg-hover"
			>
				<div class="flex h-10 w-10 items-center justify-center rounded-full bg-[#58CC02]/20">
					<svg class="h-5 w-5 text-[#58CC02]" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10" opacity="0.3" /><circle cx="12" cy="12" r="6" /></svg>
				</div>
				<div class="flex-1">
					<span class="text-[15px] font-semibold text-gv2-text-primary">Credits & Wallet</span>
					<p class="text-[12px] text-gv2-text-muted">Earn credits, manage wallet, join inference</p>
				</div>
				<svg class="h-4 w-4 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M9 18l6-6-6-6" /></svg>
			</a>
		</div>
	{:else}
		{#if guestCta}
			<div class="p-5">
				{@render guestCta()}
			</div>
		{:else}
			<!-- Default guest sign-in CTA -->
			<div class="flex flex-col items-center gap-4 px-6 py-12">
				<div class="flex h-16 w-16 items-center justify-center rounded-full bg-etzhayyim-hover">
					<svg class="h-8 w-8 text-etzhayyim-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<circle cx="12" cy="8" r="4" />
						<path d="M20 21a8 8 0 1 0-16 0" />
					</svg>
				</div>
				<div class="flex flex-col items-center gap-2">
					<h2 class="text-[18px] font-bold text-etzhayyim-text">Sign in</h2>
					<p class="text-center text-[13px] text-etzhayyim-secondary">Sign in to access your profile and feed.</p>
				</div>
				<Button
					variant="solid-fill"
					size="sm"
					class="!bg-[#58CC02] !text-white !rounded-xl !shadow-[0_4px_0_#3D8A00] active:!shadow-none active:!translate-y-[4px] !transition-all"
					onclick={handleSignIn}
				>
					Sign in
				</Button>
			</div>
		{/if}
	{/if}
</div>

{#if showEditProfile}
<div class="fixed inset-0 z-[999] flex items-end sm:items-center justify-center">
	<button type="button" class="absolute inset-0 bg-black/60" onclick={() => { showEditProfile = false; }} aria-label="Close"></button>
	<div class="relative z-10 w-full max-w-[500px] rounded-t-2xl sm:rounded-2xl bg-gv2-bg-primary border border-gv2-border p-5 shadow-2xl">
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-[18px] font-bold text-gv2-text-primary">プロフィールを編集</h2>
			<button type="button" class="text-gv2-text-muted" onclick={() => { showEditProfile = false; }}>
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
			</button>
		</div>
		<label class="block mb-3">
			<span class="text-[13px] font-semibold text-gv2-text-muted mb-1 block">表示名</span>
			<input type="text" bind:value={editDisplayName} maxlength="64"
				class="w-full rounded-xl border border-gv2-border bg-gv2-bg-hover px-3 py-2.5 text-[15px] text-gv2-text-primary outline-none focus:border-[var(--gv2-accent,#58CC02)]" />
		</label>
		<label class="block mb-4">
			<span class="text-[13px] font-semibold text-gv2-text-muted mb-1 block">自己紹介</span>
			<textarea bind:value={editBio} maxlength="256" rows="3"
				class="w-full rounded-xl border border-gv2-border bg-gv2-bg-hover px-3 py-2.5 text-[15px] text-gv2-text-primary outline-none focus:border-[var(--gv2-accent,#58CC02)] resize-none"></textarea>
		</label>
		<div class="flex gap-2 justify-end">
			<button type="button" class="min-h-[40px] rounded-full border border-gv2-border px-5 py-2 text-[14px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={() => { showEditProfile = false; }}>キャンセル</button>
			<button type="button" class="min-h-[40px] rounded-full bg-[var(--gv2-accent,#58CC02)] px-5 py-2 text-[14px] font-bold text-white touch-manipulation active:opacity-80 disabled:opacity-50" disabled={editSaving} onclick={saveProfile}>
				{editSaving ? '保存中...' : '保存'}
			</button>
		</div>
	</div>
</div>
{/if}
