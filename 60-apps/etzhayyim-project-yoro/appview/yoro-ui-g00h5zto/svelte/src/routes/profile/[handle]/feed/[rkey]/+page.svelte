<!--
  /profile/{handle}/feed/{rkey} — View a custom feed generator.
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { RichText } from '$lib/w';
	import { getFeedGenerator, getFeed, getAuthorProfile } from '$lib/atproto-agent';
	import type { FeedGeneratorView, FeedItem } from '$lib/atproto-agent';

	const handle = $derived(decodeURIComponent(($page.params as Record<string, string>).handle ?? ''));
	const rkey = $derived(decodeURIComponent(($page.params as Record<string, string>).rkey ?? ''));

	let generator = $state<FeedGeneratorView | null>(null);
	let items = $state<FeedItem[]>([]);
	let loading = $state(true);
	let cursor = $state<string | undefined>(undefined);
	let hasMore = $state(false);

	function timeAgo(ts: string): string {
		const diff = Date.now() - new Date(ts).getTime();
		const mins = Math.max(0, Math.floor(diff / 60000));
		if (mins < 60) return `${mins}m`;
		const hrs = Math.floor(mins / 60);
		if (hrs < 24) return `${hrs}h`;
		return `${Math.floor(hrs / 24)}d`;
	}

	async function load(append = false) {
		if (!append) loading = true;
		try {
			const did = handle.startsWith('did:') ? handle : (await getAuthorProfile(handle) as any)?.did || handle;
			const uri = `at://${did}/app.bsky.feed.generator/${rkey}`;
			if (!generator) generator = await getFeedGenerator(uri) as any;
			const result = await getFeed(uri, { limit: 50, cursor: append ? cursor : undefined });
			const feed = Array.isArray(result) ? result : (result as any).feed ?? [];
			items = append ? [...items, ...feed] : feed;
			cursor = (result as any)?.cursor;
			hasMore = !!cursor;
		} catch (e) { console.warn('feed: loadFeed failed', e); } finally {
			loading = false;
		}
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto(`/profile/${encodeURIComponent(handle)}`);
	}

	onMount(() => { void load(); });
</script>

<svelte:head>
	<title>{(generator as any)?.displayName ?? 'Feed'} — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<div class="min-w-0 flex-1">
			<span class="block truncate text-[17px] font-bold text-gv2-text-primary">{(generator as any)?.displayName ?? 'Feed'}</span>
			<span class="block truncate text-[13px] text-gv2-text-muted">by @{handle}</span>
		</div>
	</div>

	{#if loading}
		<div class="flex flex-col gap-1 p-2" in:fade={staggerFade(0, { duration: 300 })}>
			{#each { length: 6 } as _}
				<div class="flex items-center gap-3 px-4 py-3">
					<Skeleton variant="circular" class="h-11 w-11 flex-shrink-0" />
					<div class="flex-1 space-y-1.5">
						<Skeleton variant="text" class="w-2/5 h-4" />
						<Skeleton variant="text" class="w-full h-3" />
					</div>
				</div>
			{/each}
		</div>
	{:else}
		{#if (generator as any)?.description}
			<div class="border-b border-gv2-border/20 px-4 py-3">
				<p class="text-[14px] text-gv2-text-muted">{(generator as any).description}</p>
				{#if (generator as any)?.likeCount > 0}
					<a href="/profile/{encodeURIComponent(handle)}/feed/{encodeURIComponent(rkey)}/liked-by" class="mt-1 inline-block text-[13px] text-[#1185FE] no-underline active:underline">
						{(generator as any).likeCount} likes
					</a>
				{/if}
			</div>
		{/if}
		<div class="flex-1 overflow-y-auto scrollbar-none divide-y divide-gv2-border/20">
			{#each items as item, i (item.post.uri || i)}
				{@const p = item.post}
				<button
					type="button"
					class="flex w-full gap-2.5 px-4 py-3 text-left touch-manipulation active:bg-gv2-bg-hover/40"
					onclick={() => goto(`/profile/${encodeURIComponent(p.author.handle)}/post/${encodeURIComponent(p.rkey)}`)}
					in:fade={staggerFade(i, { duration: 150 })}
				>
					<Avatar src={p.author.avatar || undefined} fallback={(p.author.displayName || p.author.handle || '?').slice(0, 2).toUpperCase()} size="sm" class="!h-9 !w-9 flex-shrink-0" />
					<div class="min-w-0 flex-1">
						<div class="flex items-baseline gap-1 text-[15px]">
							<span class="truncate font-bold text-gv2-text-primary">{p.author.displayName || p.author.handle}</span>
							<span class="truncate text-[14px] text-gv2-text-muted">@{p.author.handle}</span>
							<span class="flex-shrink-0 text-[14px] text-gv2-text-muted">&middot; {timeAgo(p.indexedAt)}</span>
						</div>
						<div class="mt-1 text-[15px] leading-[1.5] text-gv2-text-primary">
							<RichText text={p.text} facets={p.facets} />
						</div>
					</div>
				</button>
			{/each}
			{#if items.length === 0}
				<div class="py-8 text-center text-[14px] text-gv2-text-muted">No posts in this feed</div>
			{/if}
			{#if hasMore}
				<button type="button" class="w-full py-4 text-center text-[14px] text-[#1185FE] touch-manipulation active:opacity-70" onclick={() => void load(true)}>Load more</button>
			{/if}
		</div>
	{/if}
</div>
