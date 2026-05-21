<!--
  /profile/{handle}/follows — Bluesky-compatible following list.
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { getFollows, getAuthorProfile, getCurrentDID } from '$lib/atproto-agent';
	import type { FollowView, AuthorProfile } from '$lib/atproto-agent';

	const handle = $derived(decodeURIComponent(($page.params as Record<string, string>).handle ?? ''));

	let profile = $state<AuthorProfile | null>(null);
	let follows = $state<FollowView[]>([]);
	let loading = $state(true);
	let cursor = $state<string | undefined>(undefined);
	let hasMore = $state(false);

	async function loadFollows(append = false) {
		if (!append) loading = true;
		try {
			if (!profile) profile = await getAuthorProfile(handle);
			const did = (profile as any)?.did || handle;
			const result = await getFollows(did, { limit: 50, cursor: append ? cursor : undefined });
			const items = Array.isArray(result) ? result : (result as any).follows ?? [];
			follows = append ? [...follows, ...items] : items;
			cursor = (result as any)?.cursor;
			hasMore = !!cursor;
		} catch (e) { console.warn('follows: loadFollows failed', e); } finally {
			loading = false;
		}
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto(`/profile/${encodeURIComponent(handle)}`);
	}

	onMount(() => { void loadFollows(); });
</script>

<svelte:head>
	<title>Following — {handle} — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<div class="min-w-0 flex-1">
			<span class="block truncate text-[17px] font-bold text-gv2-text-primary">Following</span>
			<span class="block truncate text-[13px] text-gv2-text-muted">@{handle}</span>
		</div>
	</div>

	{#if loading}
		<div class="flex flex-col gap-1 p-2" in:fade={staggerFade(0, { duration: 300 })}>
			{#each { length: 8 } as _}
				<div class="flex items-center gap-3 px-4 py-3">
					<Skeleton variant="circular" class="h-11 w-11 flex-shrink-0" />
					<div class="flex-1 space-y-1.5"><Skeleton variant="text" class="w-2/5 h-4" /><Skeleton variant="text" class="w-3/5 h-3" /></div>
				</div>
			{/each}
		</div>
	{:else if follows.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8">
			<p class="text-[17px] font-bold text-gv2-text-primary">Not following anyone yet</p>
		</div>
	{:else}
		<div class="flex-1 overflow-y-auto scrollbar-none divide-y divide-gv2-border/20">
			{#each follows as f, i (f.did)}
				<button
					type="button"
					class="flex w-full items-center gap-3 px-4 py-3 text-left touch-manipulation active:bg-gv2-bg-hover/40"
					onclick={() => goto(`/profile/${encodeURIComponent(f.handle || f.did)}`)}
					in:fade={staggerFade(i, { duration: 150 })}
				>
					<Avatar src={f.avatar || undefined} fallback={(f.displayName || f.handle || '?').slice(0, 2).toUpperCase()} size="md" class="!h-11 !w-11 flex-shrink-0" />
					<div class="min-w-0 flex-1">
						<span class="block truncate text-[15px] font-bold text-gv2-text-primary">{f.displayName || f.handle}</span>
						<span class="block truncate text-[14px] text-gv2-text-muted">@{f.handle}</span>
					</div>
				</button>
			{/each}
			{#if hasMore}
				<button type="button" class="w-full py-4 text-center text-[14px] text-[#1185FE] touch-manipulation active:opacity-70" onclick={() => void loadFollows(true)}>Load more</button>
			{/if}
		</div>
	{/if}
</div>
