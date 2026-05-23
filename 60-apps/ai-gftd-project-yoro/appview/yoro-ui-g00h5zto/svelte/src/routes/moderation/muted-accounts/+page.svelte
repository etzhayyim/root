<!--
  /moderation/muted-accounts — Bluesky-compatible muted accounts list.
-->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { getMutes, unmuteActor } from '$lib/atproto-agent';
	import type { MutedUser } from '$lib/atproto-agent';

	let muted = $state<MutedUser[]>([]);
	let loading = $state(true);
	let cursor = $state<string | undefined>(undefined);
	let hasMore = $state(false);

	async function load(append = false) {
		if (!append) loading = true;
		try {
			const result = await getMutes({ limit: 50, cursor: append ? cursor : undefined } as any);
			const items = Array.isArray(result) ? result : (result as any).mutes ?? [];
			muted = append ? [...muted, ...items] : items;
			cursor = (result as any)?.cursor;
			hasMore = !!cursor;
		} catch (e) { console.warn('muted accounts load failed', e); } finally {
			loading = false;
		}
	}

	async function handleUnmute(did: string) {
		try {
			await unmuteActor(did);
			muted = muted.filter(m => m.did !== did);
		} catch (e) { console.warn('unmute failed', e); }
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/moderation');
	}

	onMount(() => { void load(); });
</script>

<svelte:head>
	<title>Muted accounts — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Muted accounts</span>
	</div>

	{#if loading}
		<div class="flex flex-col gap-1 p-2" in:fade={staggerFade(0, { duration: 300 })}>
			{#each { length: 5 } as _}
				<div class="flex items-center gap-3 px-4 py-3"><Skeleton variant="circular" class="h-11 w-11 flex-shrink-0" /><div class="flex-1 space-y-1.5"><Skeleton variant="text" class="w-2/5 h-4" /><Skeleton variant="text" class="w-3/5 h-3" /></div></div>
			{/each}
		</div>
	{:else if muted.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8">
			<p class="text-[17px] font-bold text-gv2-text-primary">No muted accounts</p>
			<p class="text-[14px] text-gv2-text-muted">Accounts you mute won't appear in your feeds</p>
		</div>
	{:else}
		<div class="flex-1 overflow-y-auto scrollbar-none divide-y divide-gv2-border/20">
			{#each muted as m, i (m.did)}
				<div class="flex items-center gap-3 px-4 py-3" in:fade={staggerFade(i, { duration: 150 })}>
					<button type="button" class="flex-shrink-0" onclick={() => goto(`/profile/${encodeURIComponent(m.handle || m.did)}`)}>
						<Avatar src={m.avatar || undefined} fallback={(m.displayName || m.handle || '?').slice(0, 2).toUpperCase()} size="md" class="!h-11 !w-11" />
					</button>
					<button type="button" class="min-w-0 flex-1 text-left" onclick={() => goto(`/profile/${encodeURIComponent(m.handle || m.did)}`)}>
						<span class="block truncate text-[15px] font-bold text-gv2-text-primary">{m.displayName || m.handle}</span>
						<span class="block truncate text-[14px] text-gv2-text-muted">@{m.handle}</span>
					</button>
					<button type="button" class="flex-shrink-0 rounded-full border border-gv2-border px-3 py-1.5 text-[13px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={() => void handleUnmute(m.did)}>Unmute</button>
				</div>
			{/each}
			{#if hasMore}
				<button type="button" class="w-full py-4 text-center text-[14px] text-[#1185FE] touch-manipulation active:opacity-70" onclick={() => void load(true)}>Load more</button>
			{/if}
		</div>
	{/if}
</div>
