<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { getPreferences } from '$lib/atproto-agent';

	function goBack() { if (history.length > 1) history.back(); else void goto('/settings'); }

	let feeds = $state<Array<{ uri: string; displayName: string; avatar?: string }>>([]);
	let loading = $state(true);

	async function load() {
		loading = true;
		try {
			const prefs = await getPreferences();
			feeds = (prefs as any)?.savedFeeds ?? (prefs as any)?.feeds ?? [];
		} catch (e) { console.warn('saved feeds load failed', e); } finally { loading = false; }
	}

	onMount(() => { void load(); });
</script>

<svelte:head><title>Saved Feeds — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Saved Feeds</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none">
		{#if loading}
			<div class="p-4" in:fade={staggerFade(0, { duration: 300 })}>
				{#each { length: 5 } as _}<div class="flex items-center gap-3 py-3"><Skeleton variant="rectangular" class="h-10 w-10" /><Skeleton variant="text" class="w-1/3 h-4" /></div>{/each}
			</div>
		{:else if feeds.length === 0}
			<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8">
				<p class="text-[17px] font-bold text-gv2-text-primary">No saved feeds</p>
				<p class="text-[14px] text-gv2-text-muted text-center">Save feeds to quickly access them from your home screen.</p>
			</div>
		{:else}
			<div class="divide-y divide-gv2-border/20">
				{#each feeds as f, i (f.uri)}
					<div class="flex items-center gap-3 px-4 py-3" in:fade={staggerFade(i, { duration: 150 })}>
						<Avatar src={f.avatar || undefined} fallback={(f.displayName ?? '?').slice(0, 2).toUpperCase()} size="sm" class="!h-10 !w-10 rounded-lg" />
						<span class="flex-1 truncate text-[15px] font-medium text-gv2-text-primary">{f.displayName}</span>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
