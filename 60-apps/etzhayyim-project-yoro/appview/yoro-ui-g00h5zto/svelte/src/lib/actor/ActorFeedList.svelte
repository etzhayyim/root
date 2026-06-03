<script lang="ts">
	/**
	 * ActorFeedList — renders getAuthorFeed as a scrollable post list.
	 * AT Protocol feed items (FeedItem) with like/repost actions.
	 */
	import { onMount } from 'svelte';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { getAuthorFeed, likePost, unlikePost, repost, unrepost, sendInteractions } from '$lib/atproto-agent';
	import type { FeedItem, Did } from '$lib/atproto-agent';

	interface Props {
		did: Did;
	}

	let { did }: Props = $props();

	let items = $state<FeedItem[]>([]);
	let loading = $state(true);
	let error = $state('');
	let cursor = $state<string | undefined>(undefined);
	let hasMore = $state(true);
	let likedSet = $state<Set<string>>(new Set());
	let repostedSet = $state<Set<string>>(new Set());

	function timeAgo(ts: string): string {
		const d = new Date(ts);
		if (Number.isNaN(d.getTime())) return '';
		const diff = Date.now() - d.getTime();
		const m = Math.max(0, Math.floor(diff / 60000));
		if (m < 60) return `${m}m`;
		const h = Math.floor(m / 60);
		if (h < 24) return `${h}h`;
		return `${Math.floor(h / 24)}d`;
	}

	async function loadFeed(append = false) {
		if (!append) loading = true;
		error = '';
		try {
			const res = await getAuthorFeed(did, { cursor: append ? cursor : undefined, limit: 30 });
			if (append) {
				const seen = new Set(items.map((fi) => fi.post.uri || `${fi.post.author.did || ''}/${fi.post.rkey || ''}`));
				const next = [...items];
				for (const fi of res.feed) {
					const key = fi.post.uri || `${fi.post.author.did || ''}/${fi.post.rkey || ''}`;
					if (!key || seen.has(key)) continue;
					seen.add(key);
					next.push(fi);
				}
				items = next;
			} else {
				const seen = new Set<string>();
				items = res.feed.filter((fi) => {
					const key = fi.post.uri || `${fi.post.author.did || ''}/${fi.post.rkey || ''}`;
					if (!key || seen.has(key)) return false;
					seen.add(key);
					return true;
				});
				// Mark already-liked/reposted
				for (const fi of items) {
					if (fi.post.viewerLike) likedSet.add(fi.post.rkey);
					if (fi.post.viewerRepost) repostedSet.add(fi.post.rkey);
				}
				// Track view impressions
				if (items.length > 0) {
					void sendInteractions(items.map(fi => ({ uri: fi.post.uri, event: 'view' as const }))).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/actor/ActorFeedList.svelte: suppressed async error", error); });
				}
			}
			cursor = res.cursor;
			hasMore = !!res.cursor;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load feed';
		} finally {
			loading = false;
		}
	}

	function toggleLike(e: Event, post: FeedItem['post']) {
		e.stopPropagation();
		const next = new Set(likedSet);
		if (next.has(post.rkey)) {
			next.delete(post.rkey);
			void unlikePost(post.uri).catch((err) => console.warn('unlike failed', err));
		} else {
			next.add(post.rkey);
			void likePost(post.uri, post.cid).catch((err) => console.warn('like failed', err));
		}
		likedSet = next;
	}

	function toggleRepost(e: Event, post: FeedItem['post']) {
		e.stopPropagation();
		const next = new Set(repostedSet);
		if (next.has(post.rkey)) {
			next.delete(post.rkey);
			void unrepost(post.uri).catch((err) => console.warn('unrepost failed', err));
		} else {
			next.add(post.rkey);
			void repost(post.uri, post.cid).catch((err) => console.warn('repost failed', err));
		}
		repostedSet = next;
	}

	onMount(() => { void loadFeed(); });
</script>

<div class="flex flex-col w-full">
	{#if loading && items.length === 0}
		<div class="flex flex-col gap-4 p-4">
			{#each Array(5) as _}
				<div class="flex gap-3">
					<Skeleton variant="circular" class="h-10 w-10 shrink-0" />
					<div class="flex-1">
						<Skeleton class="h-4 w-32 mb-2" />
						<Skeleton class="h-3 w-full mb-1" />
						<Skeleton class="h-3 w-3/4" />
					</div>
				</div>
			{/each}
		</div>
	{:else if error && items.length === 0}
		<div class="flex items-center justify-center p-8 text-[13px] text-[var(--gv2-text-muted,#777)]">
			{error}
		</div>
	{:else if items.length === 0}
		<div class="flex items-center justify-center p-8 text-[13px] text-[var(--gv2-text-muted,#777)]">
			No posts yet
		</div>
	{:else}
		{#each items as fi (fi.post.uri)}
			{@const post = fi.post}
			{@const liked = likedSet.has(post.rkey)}
			{@const reposted = repostedSet.has(post.rkey)}
			<div class="flex gap-3 px-4 py-3 border-b border-[var(--gv2-border,#2f2f2f)] active:bg-[var(--gv2-bg-hover,#1a1a1a)] touch-manipulation">
				<Avatar src={post.author.avatar} fallback={post.author.displayName?.slice(0, 2) ?? '?'} size="sm" class="shrink-0" />
				<div class="flex-1 min-w-0">
					<!-- Author line -->
					<div class="flex items-baseline gap-1.5">
						<span class="text-[14px] font-bold truncate">{post.author.displayName}</span>
						<span class="text-[12px] text-[var(--gv2-text-muted,#777)] truncate">@{post.author.handle}</span>
						<span class="text-[12px] text-[var(--gv2-text-muted,#777)] shrink-0 ml-auto">{timeAgo(post.indexedAt)}</span>
					</div>

					<!-- Text -->
					{#if post.text}
						<p class="text-[14px] text-[var(--gv2-text-primary,#fff)] mt-1 whitespace-pre-wrap break-words">{post.text}</p>
					{/if}

					<!-- Action bar -->
					<div class="flex items-center gap-6 mt-2 text-[12px] text-[var(--gv2-text-muted,#777)]">
						<!-- Reply -->
						<span class="flex items-center gap-1">
							<svg class="h-4 w-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 10h4l3-7 4 14 3-7h3"/></svg>
							{post.replyCount || ''}
						</span>
						<!-- Repost -->
						<button type="button" class="flex items-center gap-1 touch-manipulation active:opacity-80 {reposted ? 'text-green-500' : ''}" onclick={(e) => toggleRepost(e, post)}>
							<svg class="h-4 w-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 9l3-3 3 3M7 6v8M16 11l-3 3-3-3M13 14V6"/></svg>
							{post.repostCount || ''}
						</button>
						<!-- Like -->
						<button type="button" class="flex items-center gap-1 touch-manipulation active:opacity-80 {liked ? 'text-red-500' : ''}" onclick={(e) => toggleLike(e, post)}>
							<svg class="h-4 w-4" viewBox="0 0 20 20" fill={liked ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="1.5"><path d="M10 17s-7-4.35-7-8.5C3 5.46 5.46 3 8.5 3c1.74 0 3.41.81 4.5 2.09C14.09 3.81 15.76 3 17.5 3 20.54 3 23 5.46 23 8.5c0 4.15-7 8.5-7 8.5" transform="translate(-3,-1) scale(0.87)"/></svg>
							{post.likeCount || ''}
						</button>
						<!-- View count -->
						{#if post.viewCount > 0}
							<span class="flex items-center gap-1">
								<svg class="h-4 w-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2.5 2.5v15h15"/><path d="M5.5 13l3.5-6 3 3.5 3.5-5"/></svg>
								{post.viewCount}
							</span>
						{/if}
					</div>
				</div>
			</div>
		{/each}

		{#if hasMore}
			<button
				type="button"
				class="w-full py-4 text-[13px] text-[var(--gv2-accent,#3b82f6)] font-semibold touch-manipulation active:opacity-80"
				onclick={() => void loadFeed(true)}
			>Load more</button>
		{/if}
	{/if}
</div>
