<script lang="ts">
	import { goto } from '$app/navigation';
	function goBack() { if (history.length > 1) history.back(); else void goto('/settings'); }
	let enableGiphy = $state(true);
	let enableTenor = $state(true);
	let enableYoutube = $state(true);
	let enableTwitch = $state(true);
	let enableSpotify = $state(true);
</script>

<svelte:head><title>External Embeds — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">External Embeds</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-4">
		<p class="mb-4 text-[13px] text-gv2-text-muted">Control which third-party services can embed content in your feed.</p>
		{#each [{ label: 'Giphy', get: () => enableGiphy, set: (v: boolean) => enableGiphy = v }, { label: 'Tenor', get: () => enableTenor, set: (v: boolean) => enableTenor = v }, { label: 'YouTube', get: () => enableYoutube, set: (v: boolean) => enableYoutube = v }, { label: 'Twitch', get: () => enableTwitch, set: (v: boolean) => enableTwitch = v }, { label: 'Spotify', get: () => enableSpotify, set: (v: boolean) => enableSpotify = v }] as item}
			<label class="flex min-h-[44px] items-center justify-between rounded-lg px-3 py-2 touch-manipulation active:bg-gv2-bg-hover/40">
				<span class="text-[15px] text-gv2-text-primary">{item.label}</span>
				<input type="checkbox" checked={item.get()} onchange={(e) => item.set((e.target as HTMLInputElement).checked)} class="h-5 w-5 rounded accent-[#1185FE]" />
			</label>
		{/each}
	</div>
</div>
