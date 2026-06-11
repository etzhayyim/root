<!--
  /profile/{handle}/post/{rkey} — Bluesky-compatible post/thread view.
  AT URI: at://{did}/app.bsky.feed.post/{rkey}
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { ActionSheet } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { playTap, playSuccess, haptic } from '@etzhayyim/design-system/audio';
	import { RichText, PostEmbed, ContentLabel, didFromRouteActor, normalizedPostEmbed, postRkey, postRouteActor } from '$lib/w';
		import { getPostThread, getCurrentDID, likePost, unlikePost, repost, unrepost, createPost, createBookmark, deleteBookmark, muteThread, unmuteThread, muteActor, blockActor, reportContent, sendInteractions, resolveHandle } from '$lib/atproto-agent';
	import type { FeedItem, PostView } from '$lib/atproto-agent';
	import { isSignedIn } from '$lib/auth';
	import { recordVisit } from '$lib/history.svelte';

	const routeParams = $derived.by(() => {
		const params = ($page.params as Record<string, string>) ?? {};
		const fromParamsHandle = params.handle ?? '';
		const fromParamsRkey = params.rkey ?? '';
		if (fromParamsHandle && fromParamsRkey) {
			return {
				handle: decodeURIComponent(fromParamsHandle),
				rkey: decodeURIComponent(fromParamsRkey),
			};
		}
		const pathname = ($page.url as URL | undefined)?.pathname ?? '';
		const match = pathname.match(/^\/profile\/([^/]+)\/post\/([^/?#]+)/);
		if (!match) return { handle: '', rkey: '' };
		return {
			handle: decodeURIComponent(match[1] ?? ''),
			rkey: decodeURIComponent(match[2] ?? ''),
		};
	});
	const handle = $derived(routeParams.handle);
	const rkey = $derived(routeParams.rkey);

	// Server data for OG tags
	const { data } = $props();

	let rootPost = $state<PostView | null>(null);
	let replies = $state<PostView[]>([]);
	let loading = $state(true);
	let selfDid = $state('');
	let replyText = $state('');
	let sending = $state(false);
	let liked = $state(false);
	let reposted = $state(false);
	let bookmarked = $state(false);
	let showMoreMenu = $state(false);
	let loadError = $state('');
	let replyError = $state('');
	let showLoginPrompt = $state(false);
	let actionError = $state('');
	let actionBusy = $state(false);
	let actionErrorTimer: ReturnType<typeof setTimeout> | null = null;
	function showActionError(msg: string) {
		actionError = msg;
		if (actionErrorTimer) clearTimeout(actionErrorTimer);
		actionErrorTimer = setTimeout(() => { actionError = ''; }, 5000);
	}
	const RESOLVE_HANDLE_TIMEOUT_MS = 8_000;
	const POST_THREAD_TIMEOUT_MS = 15_000;

	function timeAgo(ts: string): string {
		const date = new Date(ts);
		if (Number.isNaN(date.getTime())) return 'now';
		const diff = Date.now() - date.getTime();
		const mins = Math.max(0, Math.floor(diff / 60000));
		if (mins < 60) return `${mins}m`;
		const hrs = Math.floor(mins / 60);
		if (hrs < 24) return `${hrs}h`;
		return `${Math.floor(hrs / 24)}d`;
	}

	function fullTimestamp(ts: string): string {
		const date = new Date(ts);
		if (Number.isNaN(date.getTime())) return '';
		return date.toLocaleString('ja-JP', {
			year: 'numeric', month: '2-digit', day: '2-digit',
			hour: '2-digit', minute: '2-digit',
		});
	}

	function formatCount(n: number): string {
		if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
		if (n >= 10_000) return `${(n / 1000).toFixed(1)}K`;
		if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
		return String(n);
	}

	function withTimeout<T>(promise: Promise<T>, timeoutMs: number, label: string): Promise<T> {
		return Promise.race([
			promise,
			new Promise<T>((_, reject) => {
				setTimeout(() => reject(new Error(`${label}: timeout (${timeoutMs}ms)`)), timeoutMs);
			}),
		]);
	}

	function extractErrorCode(err: unknown): string {
		const raw = String((err as { message?: string })?.message ?? err ?? '');
		const m = raw.match(/\b([A-Za-z][A-Za-z0-9]+(?:[A-Z][a-z0-9]+)+)\b/);
		return m?.[1] ?? '';
	}

	async function loadThread() {
		loading = true;
		loadError = '';
		try {
			let did = data?.og?.authorDid || '';
			if (!did) {
				did = didFromRouteActor(handle);
				if (!did) {
					did = await withTimeout(resolveHandle(handle), RESOLVE_HANDLE_TIMEOUT_MS, 'resolveHandle');
				}
			}
			const uri = `at://${did}/app.bsky.feed.post/${rkey}`;
			const res = await withTimeout(getPostThread(uri), POST_THREAD_TIMEOUT_MS, 'getPostThread');
			if (res?.thread) {
				rootPost = res.thread.post ?? null;
				replies = (res.thread.replies ?? []).map((r: any) => r.post ?? r);
				if (!rootPost) {
					loadError = '投稿データを取得できませんでした';
				}
				liked = !!(rootPost as any)?.viewerLike;
				reposted = !!(rootPost as any)?.viewerRepost;
				bookmarked = !!(rootPost as any)?.viewerBookmarked;
				if (rootPost?.uri) {
					void sendInteractions([{ uri: rootPost.uri, event: 'view' }]).catch((error) => { console.warn("[silent-fail] sendInteractions:", error); });
				}
				if (rootPost) {
					const snippet = (rootPost.text || '').slice(0, 80) || '投稿';
					recordVisit({
						path: `/profile/${encodeURIComponent(handle)}/post/${encodeURIComponent(rkey)}`,
						title: snippet,
						type: 'post',
						avatar: rootPost.author?.avatar,
						handle: rootPost.author?.handle || rootPost.author?.displayName,
					});
				}
			}
		} catch (e: any) {
			const msg = e?.message || 'Failed to load thread';
			const code = extractErrorCode(e);
			loadError = code ? `${code}: ${msg}` : msg;
			console.error('post thread: load failed', e);
		} finally {
			loading = false;
		}
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/');
	}

	function openPost(post: PostView, fallbackActor = handle) {
		const rkey = postRkey(post);
		const actor = postRouteActor(post.author, fallbackActor);
		if (!rkey || !actor) return;
		void goto(`/profile/${encodeURIComponent(actor)}/post/${encodeURIComponent(rkey)}`);
	}

	onMount(async () => {
		try { selfDid = await getCurrentDID(); } catch (e) {
			console.warn('getCurrentDID: not authenticated', e);
		}
	});

	$effect(() => {
		if (handle && rkey) void loadThread();
	});

	// ── Like toggle ──
	async function toggleLike() {
		if (!rootPost || actionBusy) return;
		actionBusy = true;
		if (!$isSignedIn) { actionBusy = false; showLoginPrompt = true; return; }
		liked = !liked;
		playTap();
		haptic('light');
		try {
			if (liked) {
				await likePost(rootPost.uri, rootPost.cid);
			} else {
				await unlikePost(rootPost.uri);
			}
		} catch (e: any) {
			liked = !liked;
			const msg = e?.message || e?.error || String(e);
			showActionError(`Like failed: ${msg}`);
			console.warn('like toggle failed', e);
		} finally { actionBusy = false; }
	}

	// ── Repost toggle ──
	async function toggleRepost() {
		if (!rootPost || actionBusy) return;
		actionBusy = true;
		if (!$isSignedIn) { actionBusy = false; showLoginPrompt = true; return; }
		reposted = !reposted;
		playTap();
		haptic('light');
		try {
			if (reposted) {
				await repost(rootPost.uri, rootPost.cid);
			} else {
				await unrepost(rootPost.uri);
			}
		} catch (e: any) {
			reposted = !reposted;
			const msg = e?.message || e?.error || String(e);
			showActionError(`Repost failed: ${msg}`);
			console.warn('repost toggle failed', e);
		} finally { actionBusy = false; }
	}

	// ── Bookmark toggle ──
	async function toggleBookmark() {
		if (!rootPost || actionBusy) return;
		actionBusy = true;
		if (!$isSignedIn) { actionBusy = false; showLoginPrompt = true; return; }
		bookmarked = !bookmarked;
		playTap();
		try {
			if (bookmarked) {
				await createBookmark(rootPost.uri);
			} else {
				await deleteBookmark(rootPost.uri);
			}
		} catch (e: any) {
			bookmarked = !bookmarked;
			const msg = e?.message || e?.error || String(e);
			showActionError(`Bookmark failed: ${msg}`);
			console.warn('bookmark toggle failed', e);
		} finally { actionBusy = false; }
	}

	// ── Share ──
	async function sharePost() {
		if (!rootPost) return;
		const url = `https://yoro.etzhayyim.com/profile/${encodeURIComponent(handle)}/post/${encodeURIComponent(rkey)}`;
		try {
			if (navigator.share) {
				await navigator.share({ title: `${rootPost.author?.displayName || handle} on YORO`, url });
			} else {
				await navigator.clipboard.writeText(url);
			}
		} catch (e) {
			console.warn('share failed', e);
		}
	}

	// ── Reply submit ──
	async function submitReply() {
		if (!replyText.trim() || !rootPost || sending) return;
		sending = true;
		replyError = '';
		try {
			await createPost(replyText.trim(), {
				replyTo: {
					root: { uri: rootPost.uri, cid: rootPost.cid },
					parent: { uri: rootPost.uri, cid: rootPost.cid },
				},
			});
			playSuccess();
			replyText = '';
			await loadThread();
		} catch (e) {
			const msg = e instanceof Error ? e.message : String(e);
			replyError = msg.includes('Auth') ? 'ログインが必要です' : `返信に失敗しました: ${msg}`;
			console.warn('reply failed', e);
		} finally {
			sending = false;
		}
	}

	// ── More menu actions ──
	const moreMenuActions = $derived([
		{ label: '投稿のテキストをコピー', onclick: () => {
			if (rootPost?.text) navigator.clipboard.writeText(rootPost.text).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/routes/profile/[handle]/post/[rkey]/+page.svelte: suppressed async error", error); });
		}},
		{ label: 'スレッドをミュート', onclick: () => {
			if (rootPost) muteThread(rootPost.uri).catch((e) => console.warn('mute thread failed', e));
		}},
		{ label: 'アカウントをミュート', onclick: () => {
			if (rootPost?.author?.did) muteActor(rootPost.author.did).catch((e) => console.warn('mute failed', e));
		}},
		{ label: 'アカウントをブロック', onclick: () => {
			if (rootPost?.author?.did) blockActor(rootPost.author.did).catch((e) => console.warn('block failed', e));
		}, destructive: true },
		{ label: '投稿を報告', onclick: () => {
			if (rootPost) reportContent({ reasonType: 'spam', subject: { uri: rootPost.uri, cid: rootPost.cid } }).catch((e) => console.warn('report failed', e));
		}, destructive: true },
	]);

	const likeCount = $derived((rootPost as any)?.likeCount ?? 0);
	const repostCount = $derived((rootPost as any)?.repostCount ?? 0);
	const replyCount = $derived((rootPost as any)?.replyCount ?? replies.length);
	const quoteCount = $derived((rootPost as any)?.quoteCount ?? 0);
	const viewCount = $derived((rootPost as any)?.viewCount ?? 0);

	const ogTitle = $derived(data?.og?.title ?? `Post — YORO`);
	const ogDescription = $derived(data?.og?.description ?? `@${handle} on YORO`);
	const ogImage = $derived(data?.og?.image ?? null);
	const ogUrl = $derived(data?.og?.url ?? `https://yoro.etzhayyim.com/profile/${handle}/post/${rkey}`);
</script>

<svelte:head>
	<title>{ogTitle} — YORO</title>
	<meta name="description" content={ogDescription} />
	<meta property="og:title" content={ogTitle} />
	<meta property="og:description" content={ogDescription} />
	<meta property="og:type" content="article" />
	<meta property="og:url" content={ogUrl} />
	{#if ogImage}
		<meta property="og:image" content={ogImage} />
		<meta property="og:image:alt" content={ogDescription} />
	{/if}
	{#if data?.og?.createdAt}
		<meta property="article:published_time" content={data.og.createdAt} />
	{/if}
	{#if data?.og?.authorName}
		<meta property="article:author" content={data.og.authorName} />
	{/if}
	<meta name="twitter:card" content={ogImage ? 'summary_large_image' : 'summary'} />
	<meta name="twitter:title" content={ogTitle} />
	<meta name="twitter:description" content={ogDescription} />
	{#if ogImage}<meta name="twitter:image" content={ogImage} />{/if}
	<link rel="canonical" href={ogUrl} />
	<link rel="alternate" type="application/json+oembed"
		href="https://yoro.etzhayyim.com/oembed?url={encodeURIComponent(ogUrl)}&format=json"
		title={ogTitle} />
	{#if data?.og?.authorDid}
		<meta name="at:uri" content="at://{data.og.authorDid}/app.bsky.feed.post/{rkey}" />
	{/if}
	{#if data?.jsonLd}
		{@html `<script type="application/ld+json">${JSON.stringify(data.jsonLd)}</script>`}
	{/if}
</svelte:head>

<div class="flex h-[100dvh] flex-col bg-gv2-bg-primary">
	<!-- Header -->
	<div class="flex-none flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary px-4">
		<button
			type="button"
			class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
			onclick={goBack}
			aria-label="Back"
		>
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19 12H5" /><polyline points="12 19 5 12 12 5" />
			</svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">投稿</span>
	</div>

	{#if loading}
		<div class="flex flex-col gap-4 p-4" in:fade={staggerFade(0, { duration: 300 })}>
			<div class="flex gap-3">
				<Skeleton variant="circular" class="h-12 w-12 flex-shrink-0" />
				<div class="flex-1 space-y-2">
					<Skeleton variant="text" class="w-2/5 h-4" />
					<Skeleton variant="text" class="w-full h-5" />
					<Skeleton variant="text" class="w-4/5 h-5" />
				</div>
			</div>
		</div>
	{:else if !rootPost}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8" in:fade={{ duration: 300 }}>
			<p class="text-[17px] font-bold text-gv2-text-primary">投稿が見つかりません</p>
			<p class="text-[14px] text-gv2-text-muted">この投稿は削除されたか、アクセス権限がない可能性があります</p>
			{#if loadError}
				<p class="max-w-[28rem] text-center text-[12px] text-red-500/90 break-all">{loadError}</p>
			{/if}
			<button
				class="mt-1 min-h-[44px] rounded-full border border-[#1185FE]/30 px-5 py-2 text-[14px] font-bold text-[#1185FE] touch-manipulation active:opacity-80"
				onclick={() => void loadThread()}
			>
				再読み込み
			</button>
			<button
				class="min-h-[44px] rounded-full bg-[#1185FE] px-6 py-2.5 text-[15px] font-bold text-white touch-manipulation active:opacity-80"
				onclick={goBack}
			>
				戻る
			</button>
		</div>
	{:else}
		{@const author = rootPost!.author}
		{@const rootEmbed = normalizedPostEmbed(rootPost)}
		{@const authorRouteActor = postRouteActor(author, handle)}
		<div class="flex-1 min-h-0 overflow-y-auto scrollbar-none">
			<!-- Root post (expanded view) -->
			<div class="border-b border-gv2-border/20 px-4 pt-3 pb-1">
				<!-- Author row -->
				<div class="flex items-center gap-3">
					<a href="/profile/{encodeURIComponent(authorRouteActor)}" class="flex-shrink-0">
						<Avatar
							src={author.avatar || undefined}
							fallback={(author.displayName || handle).slice(0, 2).toUpperCase()}
							size="lg"
							class="!h-12 !w-12"
						/>
					</a>
					<div class="min-w-0 flex-1">
						<a
							href="/profile/{encodeURIComponent(authorRouteActor)}"
							class="block truncate text-[15px] font-bold text-gv2-text-primary no-underline active:underline"
						>
							{author.displayName || handle}
						</a>
						<span class="block truncate text-[14px] text-gv2-text-muted">@{author.handle || handle}</span>
					</div>
					<!-- More menu button -->
					<button
						type="button"
						class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
						onclick={() => { showMoreMenu = true; }}
						aria-label="その他"
					>
						<svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="2" /><circle cx="12" cy="12" r="2" /><circle cx="19" cy="12" r="2" /></svg>
					</button>
				</div>

				<!-- Post body -->
				<ContentLabel labels={rootPost!.labels}>
					<div class="mt-3 text-[17px] leading-[1.6] text-gv2-text-primary">
						<RichText text={rootPost!.text} facets={rootPost!.facets} />
					</div>

					<!-- Embed -->
					{#if rootEmbed}
						<div class="mt-2">
							<PostEmbed embed={rootEmbed} />
						</div>
					{/if}
				</ContentLabel>

				<!-- Timestamp + reply policy -->
				<div class="mt-3 flex items-center gap-1.5 text-[14px] text-gv2-text-muted">
					<span>{fullTimestamp(rootPost!.indexedAt)}</span>
					<span>&middot;</span>
					<span>誰でも返信可</span>
				</div>

				<!-- Engagement stats (Bluesky-style: clickable links) -->
				{#if replyCount > 0 || repostCount > 0 || likeCount > 0 || quoteCount > 0 || viewCount > 0}
					<div class="mt-3 flex items-center gap-4 border-t border-gv2-border/20 py-2.5 text-[14px]">
						{#if repostCount > 0}
							<a
								href="/profile/{encodeURIComponent(authorRouteActor)}/post/{encodeURIComponent(rkey)}/reposted-by"
								class="no-underline active:underline"
							>
								<strong class="text-gv2-text-primary">{formatCount(repostCount + (reposted ? 1 : 0))}</strong>
								<span class="text-gv2-text-muted"> リポスト</span>
							</a>
						{/if}
						{#if quoteCount > 0}
							<a
								href="/profile/{encodeURIComponent(authorRouteActor)}/post/{encodeURIComponent(rkey)}/quotes"
								class="no-underline active:underline"
							>
								<strong class="text-gv2-text-primary">{formatCount(quoteCount)}</strong>
								<span class="text-gv2-text-muted"> 引用</span>
							</a>
						{/if}
						{#if likeCount > 0}
							<a
								href="/profile/{encodeURIComponent(authorRouteActor)}/post/{encodeURIComponent(rkey)}/liked-by"
								class="no-underline active:underline"
							>
								<strong class="text-gv2-text-primary">{formatCount(likeCount + (liked ? 1 : 0))}</strong>
								<span class="text-gv2-text-muted"> いいね</span>
							</a>
						{/if}
						{#if viewCount > 0}
							<span>
								<strong class="text-gv2-text-primary">{formatCount(viewCount)}</strong>
								<span class="text-gv2-text-muted"> 表示</span>
							</span>
						{/if}
					</div>
				{/if}

				<!-- Action bar (Bluesky-style: reply, repost, like, bookmark, share) -->
				<div class="flex items-center justify-between border-t border-gv2-border/20 py-1">
					<!-- Reply -->
					<button
						type="button"
						class="group flex items-center gap-1 rounded-full p-2.5 touch-manipulation transition-colors active:bg-[#1185FE]/10"
						aria-label="返信"
						onclick={() => { if (!$isSignedIn) { showLoginPrompt = true; return; } document.getElementById('reply-input')?.focus(); }}
					>
						<svg class="h-5 w-5 transition-colors group-active:text-[#1185FE]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
						{#if replyCount > 0}
							<span class="text-[13px] tabular-nums text-gv2-text-muted group-active:text-[#1185FE]">{formatCount(replyCount)}</span>
						{/if}
					</button>
					<!-- Repost -->
					<button
						type="button"
						class="group flex items-center gap-1 rounded-full p-2.5 touch-manipulation transition-colors active:bg-[#00BA7C]/10 {reposted ? 'text-[#00BA7C]' : ''}"
						aria-label="リポスト"
						onclick={toggleRepost}
						disabled={actionBusy}
					>
						<svg class="h-5 w-5 transition-colors {reposted ? 'text-[#00BA7C]' : 'group-active:text-[#00BA7C]'}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 014-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 01-4 4H3" /></svg>
						{#if repostCount > 0 || reposted}
							<span class="text-[13px] tabular-nums {reposted ? 'text-[#00BA7C]' : 'text-gv2-text-muted group-active:text-[#00BA7C]'}">{formatCount(repostCount + (reposted ? 1 : 0))}</span>
						{/if}
					</button>
					<!-- Like -->
					<button
						type="button"
						class="group flex items-center gap-1 rounded-full p-2.5 touch-manipulation transition-colors active:bg-[#F91880]/10 {liked ? 'text-[#F91880]' : ''}"
						aria-label="いいね"
						onclick={toggleLike}
						disabled={actionBusy}
					>
						<svg class="h-5 w-5 transition-colors {liked ? 'text-[#F91880]' : 'group-active:text-[#F91880]'}" viewBox="0 0 24 24" fill={liked ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" /></svg>
						{#if likeCount > 0 || liked}
							<span class="text-[13px] tabular-nums {liked ? 'text-[#F91880]' : 'text-gv2-text-muted group-active:text-[#F91880]'}">{formatCount(likeCount + (liked ? 1 : 0))}</span>
						{/if}
					</button>
					<!-- Bookmark -->
					<button
						type="button"
						class="rounded-full p-2.5 touch-manipulation transition-colors active:bg-[#1185FE]/10 {bookmarked ? 'text-[#1185FE]' : 'text-gv2-text-muted'}"
						aria-label="保存"
						onclick={toggleBookmark}
						disabled={actionBusy}
					>
						<svg class="h-5 w-5" viewBox="0 0 24 24" fill={bookmarked ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" /></svg>
					</button>
					<!-- Share -->
					<button
						type="button"
						class="rounded-full p-2.5 touch-manipulation transition-colors active:bg-[#1185FE]/10 active:text-[#1185FE] text-gv2-text-muted"
						aria-label="共有"
						onclick={sharePost}
					>
						<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8" /><polyline points="16 6 12 2 8 6" /><line x1="12" y1="2" x2="12" y2="15" /></svg>
					</button>
				</div>
			</div>

			<!-- Replies -->
			<div class="divide-y divide-gv2-border/20">
				{#each replies as reply (reply.uri || reply.rkey)}
					{@const replyAuthor = reply.author}
					{@const replyEmbed = normalizedPostEmbed(reply)}
					{@const replyRouteActor = postRouteActor(replyAuthor, handle)}
					<div
						role="button"
						tabindex="0"
						class="flex w-full gap-2.5 px-4 py-3 text-left touch-manipulation transition-colors active:bg-gv2-bg-hover/40 cursor-pointer"
						onclick={() => openPost(reply, handle)}
						onkeydown={(e) => { if (e.key === 'Enter') openPost(reply, handle); }}
					>
						<a href="/profile/{encodeURIComponent(replyRouteActor)}" class="flex-shrink-0 pt-0.5" onclick={(e) => e.stopPropagation()}>
							<Avatar
								src={replyAuthor.avatar || undefined}
								fallback={(replyAuthor.displayName ?? '??').slice(0, 2).toUpperCase()}
								size="sm"
								class="!h-9 !w-9"
							/>
						</a>
						<div class="min-w-0 flex-1">
							<div class="flex items-baseline gap-1 text-[15px] leading-tight">
								<a
									href="/profile/{encodeURIComponent(replyRouteActor)}"
									class="truncate font-bold text-gv2-text-primary no-underline active:underline"
									onclick={(e) => e.stopPropagation()}
								>
									{replyAuthor.displayName || replyAuthor.handle || ''}
								</a>
								<span class="min-w-0 truncate text-[14px] text-gv2-text-muted">@{replyAuthor.handle || ''}</span>
								<span class="flex-shrink-0 text-[14px] text-gv2-text-muted">&middot;</span>
								<span class="flex-shrink-0 text-[14px] text-gv2-text-muted">{timeAgo(reply.indexedAt)}</span>
							</div>
							<ContentLabel labels={reply.labels}>
								<div class="mt-1 text-[15px] leading-[1.5] text-gv2-text-primary">
									<RichText text={reply.text} facets={reply.facets} />
								</div>
								{#if replyEmbed}
									<PostEmbed embed={replyEmbed} />
								{/if}
							</ContentLabel>
						</div>
					</div>
				{/each}

				{#if replies.length === 0 && !loading}
					<div class="py-8 text-center text-[14px] text-gv2-text-muted">まだ返信はありません</div>
				{/if}
			</div>

		</div>

		<!-- Reply composer -->
		<div class="flex-none border-t border-gv2-border/40 bg-gv2-bg-primary px-4 py-2 safe-area-bottom">
			{#if $isSignedIn}
				{#if replyError}
					<div class="mb-1 truncate text-[12px] text-red-500">{replyError}</div>
				{/if}
				<div class="flex items-center gap-3">
					<input
						id="reply-input"
						type="text"
						class="min-h-[40px] flex-1 rounded-full border border-gv2-border bg-gv2-bg-hover/30 px-4 py-2 text-[15px] text-gv2-text-primary outline-none placeholder:text-gv2-text-muted/60 focus:border-[#1185FE]"
						placeholder="返信を書く"
						bind:value={replyText}
						onkeydown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void submitReply(); } }}
						disabled={sending}
					/>
					<button
						type="button"
						class="flex h-10 w-10 items-center justify-center rounded-full bg-[#1185FE] text-white touch-manipulation active:opacity-80 disabled:opacity-40"
						onclick={() => void submitReply()}
						disabled={!replyText.trim() || sending}
						aria-label="送信"
					>
						<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></svg>
					</button>
				</div>
			{:else}
				<button
					type="button"
					class="flex w-full items-center justify-center gap-2 rounded-full bg-[#1185FE] py-2.5 text-[15px] font-semibold text-white touch-manipulation active:opacity-80"
					onclick={() => goto('/welcome')}
				>
					ログインして返信する
				</button>
			{/if}
		</div>
	{/if}
</div>

<!-- Login prompt modal -->
{#if actionError}
<div class="fixed bottom-20 left-1/2 z-50 -translate-x-1/2 max-w-[90vw]" transition:fade={{ duration: 200 }}>
	<div class="rounded-xl bg-red-500/90 px-4 py-3 text-[13px] font-medium text-white shadow-lg backdrop-blur">
		{actionError}
		<button class="ml-2 opacity-70 hover:opacity-100" onclick={() => { actionError = ''; }}>✕</button>
	</div>
</div>
{/if}

{#if showLoginPrompt}
	<button
		type="button"
		class="fixed inset-0 z-[70] bg-black/60"
		onclick={() => { showLoginPrompt = false; }}
		aria-label="閉じる"
		transition:fade={{ duration: 200 }}
	></button>
	<div class="fixed left-1/2 top-1/2 z-[71] w-[90vw] max-w-[360px] -translate-x-1/2 -translate-y-1/2 rounded-3xl bg-gv2-bg-primary p-6 shadow-2xl" transition:fade={{ duration: 200 }}>
		<div class="flex flex-col items-center gap-4 text-center">
			<div class="flex h-16 w-16 items-center justify-center rounded-full bg-[#1185FE]/20 text-[32px]">
				<svg class="h-8 w-8 text-[#1185FE]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4" /><polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" /></svg>
			</div>
			<h3 class="text-[20px] font-black text-gv2-text-primary">ログインが必要です</h3>
			<p class="text-[14px] text-gv2-text-muted leading-relaxed">
				いいね・リポスト・返信するにはログインしてください
			</p>
			<div class="flex w-full gap-2">
				<button
					type="button"
					class="flex-1 rounded-2xl bg-[#1185FE] py-3 text-[14px] font-black text-white touch-manipulation active:opacity-80 transition-opacity"
					onclick={() => { showLoginPrompt = false; goto('/welcome'); }}
				>ログイン</button>
			</div>
			<button type="button" class="text-[14px] font-semibold text-gv2-text-muted" onclick={() => { showLoginPrompt = false; }}>閉じる</button>
		</div>
	</div>
{/if}

<!-- More menu ActionSheet -->
<ActionSheet bind:open={showMoreMenu} actions={moreMenuActions} cancelLabel="キャンセル" />
