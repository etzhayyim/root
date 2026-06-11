<!--
  /starter-pack/{name}/{rkey} — View a starter pack.
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { getStarterPack, getAuthorProfile } from '$lib/atproto-agent';
	import type { StarterPackView } from '$lib/atproto-agent';

	const name = $derived(decodeURIComponent(($page.params as Record<string, string>).name ?? ''));
	const rkey = $derived(decodeURIComponent(($page.params as Record<string, string>).rkey ?? ''));

	let pack = $state<StarterPackView | null>(null);
	let members = $state<Array<{ did: string; handle: string; displayName?: string; avatar?: string }>>([]);
	let loading = $state(true);

	async function load() {
		loading = true;
		try {
			const profile = await getAuthorProfile(name);
			const did = (profile as any)?.did || name;
			const uri = `at://${did}/app.bsky.graph.starterpack/${rkey}`;
			const result = await getStarterPack(uri);
			pack = (result as any)?.starterPack ?? result ?? null;
			members = (result as any)?.items?.map((it: any) => it.subject) ?? (result as any)?.list?.items?.map((it: any) => it.subject) ?? [];
		} catch (e) { console.warn('starter pack load failed', e); } finally {
			loading = false;
		}
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/');
	}

	onMount(() => { void load(); });
</script>

<svelte:head>
	<title>{(pack as any)?.record?.name || 'Starter Pack'} — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Starter Pack</span>
	</div>

	{#if loading}
		<div class="flex flex-col gap-1 p-4" in:fade={staggerFade(0, { duration: 300 })}>
			<Skeleton variant="text" class="w-1/2 h-6 mb-2" />
			<Skeleton variant="text" class="w-3/4 h-4 mb-4" />
			{#each { length: 6 } as _}
				<div class="flex items-center gap-3 py-3"><Skeleton variant="circular" class="h-11 w-11" /><div class="flex-1 space-y-1.5"><Skeleton variant="text" class="w-2/5 h-4" /><Skeleton variant="text" class="w-3/5 h-3" /></div></div>
			{/each}
		</div>
	{:else if !pack}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8">
			<p class="text-[17px] font-bold text-gv2-text-primary">Starter pack not found</p>
		</div>
	{:else}
		<div class="border-b border-gv2-border/20 px-4 py-4">
			<h2 class="text-[20px] font-bold text-gv2-text-primary">{(pack as any)?.record?.name || 'Starter Pack'}</h2>
			{#if (pack as any)?.record?.description}
				<p class="mt-1 text-[14px] text-gv2-text-muted">{(pack as any).record.description}</p>
			{/if}
			<p class="mt-2 text-[13px] text-gv2-text-muted">by @{(pack as any)?.creator?.handle || name}</p>
		</div>
		<div class="flex-1 overflow-y-auto scrollbar-none divide-y divide-gv2-border/20">
			{#each members as u, i (u.did)}
				<button type="button" class="flex w-full items-center gap-3 px-4 py-3 text-left touch-manipulation active:bg-gv2-bg-hover/40" onclick={() => goto(`/profile/${encodeURIComponent(u.handle || u.did)}`)} in:fade={staggerFade(i, { duration: 150 })}>
					<Avatar src={u.avatar || undefined} fallback={(u.displayName || u.handle || '?').slice(0, 2).toUpperCase()} size="md" class="!h-11 !w-11 flex-shrink-0" />
					<div class="min-w-0 flex-1">
						<span class="block truncate text-[15px] font-bold text-gv2-text-primary">{u.displayName || u.handle}</span>
						<span class="block truncate text-[14px] text-gv2-text-muted">@{u.handle}</span>
					</div>
				</button>
			{/each}
			{#if members.length === 0}
				<div class="py-8 text-center text-[14px] text-gv2-text-muted">No members in this starter pack</div>
			{/if}
		</div>
	{/if}
</div>
