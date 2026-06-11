<script lang="ts">
	import { goto } from '$app/navigation';
	function goBack() { if (history.length > 1) history.back(); else void goto('/settings'); }
	let selectedIcon = $state('default');
	const icons = [
		{ id: 'default', label: 'Default', color: '#1185FE' },
		{ id: 'dark', label: 'Dark', color: '#1a1a2e' },
		{ id: 'sunset', label: 'Sunset', color: '#F97316' },
		{ id: 'ocean', label: 'Ocean', color: '#06B6D4' },
		{ id: 'forest', label: 'Forest', color: '#22C55E' },
		{ id: 'berry', label: 'Berry', color: '#A855F7' },
	];
</script>

<svelte:head><title>App Icon — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">App Icon</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-4">
		<div class="grid grid-cols-3 gap-3">
			{#each icons as icon}
				<button type="button" class="flex flex-col items-center gap-2 rounded-xl p-3 touch-manipulation {selectedIcon === icon.id ? 'bg-gv2-bg-hover ring-2 ring-[#1185FE]' : 'active:bg-gv2-bg-hover/40'}" onclick={() => selectedIcon = icon.id}>
					<div class="h-16 w-16 rounded-2xl" style="background-color: {icon.color}"></div>
					<span class="text-[13px] text-gv2-text-primary">{icon.label}</span>
				</button>
			{/each}
		</div>
	</div>
</div>
