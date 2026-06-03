<!--
  /lists — Browse lists.
-->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { getLists, getCurrentDID } from '$lib/atproto-agent';

	let lists = $state<Array<{ uri: string; name: string; description?: string; avatar?: string; purpose?: string }>>([]);
	let loading = $state(true);

	async function load() {
		loading = true;
		try {
			const did = await getCurrentDID();
			const result = await getLists(did);
			lists = Array.isArray(result) ? result : (result as any).lists ?? [];
		} catch (e) { console.warn('lists load failed', e); } finally {
			loading = false;
		}
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/');
	}

	function listRoute(uri: string): string {
		const m = uri.match(/at:\/\/([^/]+)\/app\.bsky\.graph\.list\/(.+)/);
		if (m) return `/profile/${encodeURIComponent(m[1])}/lists/${encodeURIComponent(m[2])}`;
		return '/lists';
	}

	onMount(() => { void load(); });
</script>

<svelte:head>
	<title>Lists — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Lists</span>
	</div>

	{#if loading}
		<div class="flex flex-col gap-1 p-2" in:fade={staggerFade(0, { duration: 300 })}>
			{#each { length: 6 } as _}
				<div class="flex items-center gap-3 px-4 py-3">
					<Skeleton variant="rectangular" class="h-11 w-11 flex-shrink-0" />
					<div class="flex-1 space-y-1.5"><Skeleton variant="text" class="w-2/5 h-4" /><Skeleton variant="text" class="w-4/5 h-3" /></div>
				</div>
			{/each}
		</div>
	{:else if lists.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8">
			<p class="text-[17px] font-bold text-gv2-text-primary">No lists yet</p>
			<p class="text-[14px] text-gv2-text-muted text-center">Lists let you organize accounts into groups.</p>
		</div>
	{:else}
		<div class="flex-1 overflow-y-auto scrollbar-none divide-y divide-gv2-border/20">
			{#each lists as l, i (l.uri)}
				<button type="button" class="flex w-full items-center gap-3 px-4 py-3 text-left touch-manipulation active:bg-gv2-bg-hover/40" onclick={() => goto(listRoute(l.uri))} in:fade={staggerFade(i, { duration: 150 })}>
					<Avatar src={l.avatar || undefined} fallback={(l.name || '?').slice(0, 2).toUpperCase()} size="md" class="!h-11 !w-11 flex-shrink-0 rounded-lg" />
					<div class="min-w-0 flex-1">
						<span class="block truncate text-[15px] font-bold text-gv2-text-primary">{l.name}</span>
						{#if l.description}<span class="block truncate text-[13px] text-gv2-text-muted">{l.description}</span>{/if}
					</div>
					<svg class="h-4 w-4 flex-shrink-0 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M9 5l7 7-7 7" /></svg>
				</button>
			{/each}
		</div>
	{/if}
</div>
