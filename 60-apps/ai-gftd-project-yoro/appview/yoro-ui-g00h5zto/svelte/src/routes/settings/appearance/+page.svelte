<script lang="ts">
	import { goto } from '$app/navigation';
	import { theme, setTheme, ALL_THEMES, THEME_META, type Theme, type ColorTheme } from '$lib/theme';
	function goBack() { if (history.length > 1) history.back(); else void goto('/settings'); }
	let fontSize = $state('default');

	const themeOptions: Array<{ value: Theme; label: string }> = [
		{ value: 'system', label: 'System' },
		...ALL_THEMES.map((t) => ({ value: t as Theme, label: THEME_META[t].label })),
	];
</script>

<svelte:head><title>Appearance — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Appearance</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none">
		<div class="px-4 py-4">
			<h4 class="mb-3 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">Theme</h4>
			{#each themeOptions as opt}
				<button type="button" class="flex min-h-[44px] w-full items-center gap-3 justify-between rounded-lg px-3 py-2 text-left touch-manipulation active:bg-gv2-bg-hover/40" onclick={() => setTheme(opt.value)}>
					<div class="flex items-center gap-3">
						{#if opt.value !== 'system'}
							<div class="h-5 w-5 rounded-full border border-gv2-border" style="background: {THEME_META[opt.value as ColorTheme].swatch}"></div>
						{:else}
							<div class="flex h-5 w-5 items-center justify-center rounded-full border border-gv2-border bg-gv2-bg-hover">
								<svg class="h-3 w-3 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" /></svg>
							</div>
						{/if}
						<span class="text-[15px] text-gv2-text-primary">{opt.label}</span>
					</div>
					<div class="flex h-5 w-5 items-center justify-center rounded-full border-2 {$theme === opt.value ? 'border-[#1185FE] bg-[#1185FE]' : 'border-gv2-text-muted'}">
						{#if $theme === opt.value}<svg class="h-3 w-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round"><path d="M5 13l4 4L19 7" /></svg>{/if}
					</div>
				</button>
			{/each}
		</div>
		<div class="px-4 py-4">
			<h4 class="mb-3 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">Font size</h4>
			{#each [{ value: 'smaller', label: 'Smaller' }, { value: 'default', label: 'Default' }, { value: 'larger', label: 'Larger' }] as opt}
				<button type="button" class="flex min-h-[44px] w-full items-center justify-between rounded-lg px-3 py-2 text-left touch-manipulation active:bg-gv2-bg-hover/40" onclick={() => fontSize = opt.value}>
					<span class="text-[15px] text-gv2-text-primary">{opt.label}</span>
					<div class="flex h-5 w-5 items-center justify-center rounded-full border-2 {fontSize === opt.value ? 'border-[#1185FE] bg-[#1185FE]' : 'border-gv2-text-muted'}">
						{#if fontSize === opt.value}<svg class="h-3 w-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round"><path d="M5 13l4 4L19 7" /></svg>{/if}
					</div>
				</button>
			{/each}
		</div>
	</div>
</div>
