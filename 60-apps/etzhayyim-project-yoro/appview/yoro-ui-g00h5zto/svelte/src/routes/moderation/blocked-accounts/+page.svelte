<!--
  /moderation/blocked-accounts — Bluesky-compatible blocked accounts list.
-->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { agent, syncFromAtprotoSession } from '$lib/atproto-agent';

	type BlockedProfile = {
		did: string;
		handle?: string;
		displayName?: string;
		avatar?: string;
		viewer?: { blocking?: string };
	};

	let blocked = $state<BlockedProfile[]>([]);
	let loading = $state(true);
	let cursor = $state<string | undefined>(undefined);
	let hasMore = $state(false);

	async function load(append = false) {
		if (!append) loading = true;
		try {
			syncFromAtprotoSession();
			const { data } = await agent.app.bsky.graph.getBlocks({
				limit: 50,
				cursor: append ? cursor : undefined,
			});
			const blocks = data.blocks as BlockedProfile[];
			blocked = append ? [...blocked, ...blocks] : blocks;
			cursor = data.cursor;
			hasMore = !!data.cursor;
		} catch (e) { console.warn('blocked accounts load failed', e); } finally {
			loading = false;
		}
	}

	async function handleUnblock(did: string) {
		try {
			const target = blocked.find(b => b.did === did);
			const blockUri = target?.viewer?.blocking;
			const myDid = agent.session?.did;
			if (!blockUri || !myDid) return;
			const rkey = blockUri.split('/').pop();
			if (!rkey) return;
			await agent.app.bsky.graph.block.delete({ repo: myDid, rkey });
			blocked = blocked.filter(b => b.did !== did);
		} catch (e) { console.warn('unblock failed', e); }
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/moderation');
	}

	onMount(() => { void load(); });
</script>

<svelte:head>
	<title>Blocked accounts — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Blocked accounts</span>
	</div>

	{#if loading}
		<div class="flex flex-col gap-1 p-2" in:fade={staggerFade(0, { duration: 300 })}>
			{#each { length: 5 } as _}
				<div class="flex items-center gap-3 px-4 py-3"><Skeleton variant="circular" class="h-11 w-11 flex-shrink-0" /><div class="flex-1 space-y-1.5"><Skeleton variant="text" class="w-2/5 h-4" /><Skeleton variant="text" class="w-3/5 h-3" /></div></div>
			{/each}
		</div>
	{:else if blocked.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8">
			<p class="text-[17px] font-bold text-gv2-text-primary">No blocked accounts</p>
			<p class="text-[14px] text-gv2-text-muted">Blocked accounts cannot see your posts or interact with you</p>
		</div>
	{:else}
		<div class="flex-1 overflow-y-auto scrollbar-none divide-y divide-gv2-border/20">
			{#each blocked as b, i (b.did)}
				<div class="flex items-center gap-3 px-4 py-3" in:fade={staggerFade(i, { duration: 150 })}>
					<Avatar src={b.avatar || undefined} fallback={(b.displayName || b.handle || '?').slice(0, 2).toUpperCase()} size="md" class="!h-11 !w-11 flex-shrink-0" />
					<div class="min-w-0 flex-1">
						<span class="block truncate text-[15px] font-bold text-gv2-text-primary">{b.displayName || b.handle}</span>
						<span class="block truncate text-[14px] text-gv2-text-muted">@{b.handle}</span>
					</div>
					<button type="button" class="flex-shrink-0 rounded-full border border-red-500/50 px-3 py-1.5 text-[13px] font-semibold text-red-400 touch-manipulation active:bg-red-500/10" onclick={() => void handleUnblock(b.did)}>Unblock</button>
				</div>
			{/each}
			{#if hasMore}
				<button type="button" class="w-full py-4 text-center text-[14px] text-[#1185FE] touch-manipulation active:opacity-70" onclick={() => void load(true)}>Load more</button>
			{/if}
		</div>
	{/if}
</div>
