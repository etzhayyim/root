<!--
  /profile/{handle}/search — Search within user's posts.
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { RichText } from '$lib/w';
	import { searchPosts } from '$lib/atproto-agent';
	import type { PostView } from '$lib/atproto-agent';

	const handle = $derived(decodeURIComponent(($page.params as Record<string, string>).handle ?? ''));

	let query = $state('');
	let posts = $state<PostView[]>([]);
	let loading = $state(false);
	let searched = $state(false);

	function timeAgo(ts: string): string {
		const diff = Date.now() - new Date(ts).getTime();
		const mins = Math.max(0, Math.floor(diff / 60000));
		if (mins < 60) return `${mins}m`;
		const hrs = Math.floor(mins / 60);
		if (hrs < 24) return `${hrs}h`;
		return `${Math.floor(hrs / 24)}d`;
	}

	async function doSearch() {
		const q = query.trim();
		if (!q) return;
		loading = true;
		searched = true;
		try {
			const result = await searchPosts(`from:${handle} ${q}`, { limit: 50 });
			posts = Array.isArray(result) ? result : (result as any).posts ?? [];
		} catch (e) { console.warn('profile search: searchPosts failed', e); } finally {
			loading = false;
		}
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto(`/profile/${encodeURIComponent(handle)}`);
	}
</script>

<svelte:head>
	<title>Search @{handle} — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<div class="min-w-0 flex-1">
			<form class="flex" onsubmit={(e) => { e.preventDefault(); void doSearch(); }}>
				<input
					type="search"
					bind:value={query}
					placeholder="Search @{handle}'s posts"
					class="min-h-[36px] flex-1 rounded-full bg-gv2-bg-hover/60 px-4 py-1.5 text-[15px] text-gv2-text-primary placeholder:text-gv2-text-muted focus:outline-none focus:ring-2 focus:ring-[#1185FE]/50"
				/>
			</form>
		</div>
	</div>

	{#if loading}
		<div class="flex flex-col gap-1 p-2" in:fade={staggerFade(0, { duration: 300 })}>
			{#each { length: 6 } as _}
				<div class="flex items-center gap-3 px-4 py-3">
					<Skeleton variant="circular" class="h-9 w-9 flex-shrink-0" />
					<div class="flex-1 space-y-1.5">
						<Skeleton variant="text" class="w-2/5 h-4" />
						<Skeleton variant="text" class="w-full h-3" />
					</div>
				</div>
			{/each}
		</div>
	{:else if searched && posts.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8">
			<p class="text-[17px] font-bold text-gv2-text-primary">No posts found</p>
			<p class="text-[14px] text-gv2-text-muted">Try a different search term</p>
		</div>
	{:else if !searched}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8">
			<p class="text-[14px] text-gv2-text-muted">Search posts by @{handle}</p>
		</div>
	{:else}
		<div class="flex-1 overflow-y-auto scrollbar-none divide-y divide-gv2-border/20">
			{#each posts as p, i (p.uri || p.uri.split('/').pop())}
				<button
					type="button"
					class="flex w-full gap-2.5 px-4 py-3 text-left touch-manipulation active:bg-gv2-bg-hover/40"
					onclick={() => goto(`/profile/${encodeURIComponent(p.author.handle)}/post/${encodeURIComponent(p.uri.split('/').pop() || '')}`)}
					in:fade={staggerFade(i, { duration: 150 })}
				>
					<Avatar src={p.author.avatar || undefined} fallback={(p.author.displayName || p.author.handle || '?').slice(0, 2).toUpperCase()} size="sm" class="!h-9 !w-9 flex-shrink-0" />
					<div class="min-w-0 flex-1">
						<div class="flex items-baseline gap-1 text-[15px]">
							<span class="truncate font-bold text-gv2-text-primary">{p.author.displayName || p.author.handle}</span>
							<span class="flex-shrink-0 text-[14px] text-gv2-text-muted">&middot; {timeAgo(p.indexedAt)}</span>
						</div>
						<div class="mt-1 text-[15px] leading-[1.5] text-gv2-text-primary">
							<RichText text={(p.record as any)?.text ?? ''} facets={(p.record as any)?.facets ?? []} />
						</div>
					</div>
				</button>
			{/each}
		</div>
	{/if}
</div>
