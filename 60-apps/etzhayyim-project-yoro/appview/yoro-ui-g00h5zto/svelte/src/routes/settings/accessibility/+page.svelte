<script lang="ts">
	import { goto } from '$app/navigation';
	function goBack() { if (history.length > 1) history.back(); else void goto('/settings'); }
	let largeText = $state(false);
	let reduceMotion = $state(false);
	let autoplayGifs = $state(true);
	let altTextReminder = $state(false);
</script>

<svelte:head><title>Accessibility — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Accessibility</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-4">
		{#each [{ label: 'Large text', desc: 'Increase default text size', get: () => largeText, set: (v: boolean) => largeText = v }, { label: 'Reduce motion', desc: 'Reduce animations throughout the app', get: () => reduceMotion, set: (v: boolean) => reduceMotion = v }, { label: 'Autoplay GIFs', desc: 'Automatically play animated images', get: () => autoplayGifs, set: (v: boolean) => autoplayGifs = v }, { label: 'Alt text reminder', desc: 'Remind me to add alt text to images', get: () => altTextReminder, set: (v: boolean) => altTextReminder = v }] as item}
			<label class="flex min-h-[52px] items-center justify-between rounded-lg px-3 py-2 touch-manipulation active:bg-gv2-bg-hover/40">
				<div><span class="block text-[15px] text-gv2-text-primary">{item.label}</span><span class="block text-[13px] text-gv2-text-muted">{item.desc}</span></div>
				<input type="checkbox" checked={item.get()} onchange={(e) => item.set((e.target as HTMLInputElement).checked)} class="h-5 w-5 rounded accent-[#1185FE]" />
			</label>
		{/each}
	</div>
</div>
