<!--
  /settings/language — Language settings.
-->
<script lang="ts">
	import { goto } from '$app/navigation';

	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/settings');
	}

	let primaryLang = $state('en');
	let contentLangs = $state(['en', 'ja']);
	const languages = [
		{ code: 'en', label: 'English' },
		{ code: 'ja', label: 'Japanese' },
		{ code: 'pt', label: 'Portuguese' },
		{ code: 'es', label: 'Spanish' },
		{ code: 'ko', label: 'Korean' },
		{ code: 'zh', label: 'Chinese' },
		{ code: 'fr', label: 'French' },
		{ code: 'de', label: 'German' },
	];
</script>

<svelte:head>
	<title>Language — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Language</span>
	</div>

	<div class="flex-1 overflow-y-auto scrollbar-none">
		<div class="px-4 py-4">
			<h4 class="mb-3 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">Primary language</h4>
			<select bind:value={primaryLang} class="min-h-[44px] w-full rounded-lg border border-gv2-border/40 bg-gv2-bg-primary px-3 py-2 text-[15px] text-gv2-text-primary">
				{#each languages as lang}
					<option value={lang.code}>{lang.label}</option>
				{/each}
			</select>
		</div>
		<div class="px-4 py-4">
			<h4 class="mb-3 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">Content languages</h4>
			<p class="mb-3 text-[13px] text-gv2-text-muted">Select languages you want to see in your feed.</p>
			<div class="space-y-1">
				{#each languages as lang}
					<label class="flex min-h-[44px] items-center justify-between rounded-lg px-3 py-2 touch-manipulation active:bg-gv2-bg-hover/40">
						<span class="text-[15px] text-gv2-text-primary">{lang.label}</span>
						<input type="checkbox" checked={contentLangs.includes(lang.code)} onchange={() => { contentLangs = contentLangs.includes(lang.code) ? contentLangs.filter(c => c !== lang.code) : [...contentLangs, lang.code]; }} class="h-5 w-5 rounded accent-[#1185FE]" />
					</label>
				{/each}
			</div>
		</div>
	</div>
</div>
