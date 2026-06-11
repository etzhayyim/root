<!--
  /profile/{handle}/post/{rkey}/reposted-by — Who reposted this post.
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { getRepostedBy, getAuthorProfile } from '$lib/atproto-agent';

	const handle = $derived(decodeURIComponent(($page.params as Record<string, string>).handle ?? ''));
	const rkey = $derived(decodeURIComponent(($page.params as Record<string, string>).rkey ?? ''));

	let users = $state<Array<{ did: string; handle: string; displayName?: string; avatar?: string }>>([]);
	let loading = $state(true);
	let cursor = $state<string | undefined>(undefined);
	let hasMore = $state(false);

	async function load(append = false) {
		if (!append) loading = true;
		try {
			const did = handle.startsWith('did:') ? handle : (await getAuthorProfile(handle) as any)?.did || handle;
			const uri = `at://${did}/app.bsky.feed.post/${rkey}`;
			const result = await getRepostedBy(uri, { limit: 50, cursor: append ? cursor : undefined } as any);
			const items = Array.isArray(result) ? result : (result as any).repostedBy ?? [];
			users = append ? [...users, ...items] : items;
			cursor = (result as any)?.cursor;
			hasMore = !!cursor;
		} catch (e) { console.warn('reposted-by: load failed', e); } finally {
			loading = false;
		}
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto(`/profile/${encodeURIComponent(handle)}/post/${encodeURIComponent(rkey)}`);
	}

	onMount(() => { void load(); });
</script>

<svelte:head>
	<title>Reposted by — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Reposted by</span>
	</div>

	{#if loading}
		<div class="flex flex-col gap-1 p-2" in:fade={staggerFade(0, { duration: 300 })}>
			{#each { length: 8 } as _}
				<div class="flex items-center gap-3 px-4 py-3">
					<Skeleton variant="circular" class="h-11 w-11 flex-shrink-0" />
					<div class="flex-1 space-y-1.5">
						<Skeleton variant="text" class="w-2/5 h-4" />
						<Skeleton variant="text" class="w-3/5 h-3" />
					</div>
				</div>
			{/each}
		</div>
	{:else if users.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8">
			<p class="text-[17px] font-bold text-gv2-text-primary">No reposts yet</p>
		</div>
	{:else}
		<div class="flex-1 overflow-y-auto scrollbar-none divide-y divide-gv2-border/20">
			{#each users as u, i (u.did)}
				<button
					type="button"
					class="flex w-full items-center gap-3 px-4 py-3 text-left touch-manipulation active:bg-gv2-bg-hover/40"
					onclick={() => goto(`/profile/${encodeURIComponent(u.handle || u.did)}`)}
					in:fade={staggerFade(i, { duration: 150 })}
				>
					<Avatar src={u.avatar || undefined} fallback={(u.displayName || u.handle || '?').slice(0, 2).toUpperCase()} size="md" class="!h-11 !w-11 flex-shrink-0" />
					<div class="min-w-0 flex-1">
						<span class="block truncate text-[15px] font-bold text-gv2-text-primary">{u.displayName || u.handle}</span>
						<span class="block truncate text-[14px] text-gv2-text-muted">@{u.handle}</span>
					</div>
				</button>
			{/each}
			{#if hasMore}
				<button type="button" class="w-full py-4 text-center text-[14px] text-[#1185FE] touch-manipulation active:opacity-70" onclick={() => void load(true)}>Load more</button>
			{/if}
		</div>
	{/if}
</div>
