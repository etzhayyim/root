<script lang="ts">
	import type { Language, LanguageCode } from './types.js';

	interface Props {
		languages: Language[];
		currentLang: LanguageCode;
		getUrl: (langCode: LanguageCode) => string;
		onchange?: (from: LanguageCode, to: LanguageCode) => void;
		variant?: 'links' | 'select' | 'search';
		class?: string;
	}

	const {
		languages,
		currentLang,
		getUrl,
		onchange,
		variant = 'links',
		class: className = '',
	}: Props = $props();

	let searchQuery = $state('');
	let searchOpen = $state(false);

	const filteredLanguages = $derived(
		variant === 'search' && searchQuery
			? languages.filter(
					(l) =>
						l.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
						l.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
						(l.enName?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false)
				)
			: languages
	);

	const tier1Languages = $derived(
		variant === 'search' ? filteredLanguages.filter((l) => (l.tier ?? 1) <= 1) : []
	);

	const otherLanguages = $derived(
		variant === 'search' ? filteredLanguages.filter((l) => (l.tier ?? 1) > 1) : []
	);

	function handleSelectChange(value: string) {
		if (value !== currentLang) {
			onchange?.(currentLang, value);
			window.location.href = getUrl(value);
		}
	}

	function handleSearchSelect(code: string) {
		if (code !== currentLang) {
			onchange?.(currentLang, code);
			window.location.href = getUrl(code);
		}
		searchOpen = false;
		searchQuery = '';
	}
</script>

{#if variant === 'search'}
	<div class={`relative ${className}`}>
		<button
			type="button"
			class="flex min-h-9 cursor-pointer items-center gap-1 rounded-md border border-current bg-white px-3 py-0.5 text-sm font-bold hover:bg-blue-100"
			onclick={() => (searchOpen = !searchOpen)}
		>
			{languages.find((l) => l.code === currentLang)?.name ?? currentLang}
			<svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
				<path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
			</svg>
		</button>
		{#if searchOpen}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div
				class="absolute top-full z-50 mt-1 max-h-80 w-64 overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-lg"
				onkeydown={(e) => { if (e.key === 'Escape') searchOpen = false; }}
			>
				<div class="sticky top-0 border-b border-slate-100 bg-white p-2">
					<input
						type="text"
						class="w-full rounded-md border border-slate-200 px-2 py-1.5 text-sm outline-none focus:border-blue-400"
						placeholder="Search languages..."
						bind:value={searchQuery}
					/>
				</div>
				{#if tier1Languages.length > 0}
					<div class="border-b border-slate-100 px-2 py-1">
						<div class="px-1 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">Pinned</div>
						{#each tier1Languages as lang}
							<button
								type="button"
								class="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-sm hover:bg-blue-50"
								class:bg-blue-50={currentLang === lang.code}
								class:font-bold={currentLang === lang.code}
								onclick={() => handleSearchSelect(lang.code)}
							>
								<span dir={lang.dir ?? 'ltr'}>{lang.name}</span>
								<span class="text-[10px] text-slate-400">{lang.code}</span>
							</button>
						{/each}
					</div>
				{/if}
				{#if otherLanguages.length > 0}
					<div class="px-2 py-1">
						{#each otherLanguages as lang}
							<button
								type="button"
								class="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-sm hover:bg-blue-50"
								class:bg-blue-50={currentLang === lang.code}
								class:font-bold={currentLang === lang.code}
								onclick={() => handleSearchSelect(lang.code)}
							>
								<span dir={lang.dir ?? 'ltr'}>{lang.name}</span>
								<span class="text-[10px] text-slate-400">{lang.code}</span>
							</button>
						{/each}
					</div>
				{/if}
				{#if filteredLanguages.length === 0}
					<div class="p-4 text-center text-sm text-slate-400">No languages found</div>
				{/if}
			</div>
		{/if}
	</div>
{:else if variant === 'select'}
	<select
		class={`min-h-9 cursor-pointer rounded-md border border-current bg-white px-3 py-0.5 text-sm font-bold hover:bg-blue-100 focus-visible:outline focus-visible:outline-4 focus-visible:outline-black ${className}`}
		onchange={(e) => handleSelectChange(e.currentTarget.value)}
	>
		{#each languages as lang}
			<option value={lang.code} selected={currentLang === lang.code}>{lang.name}</option>
		{/each}
	</select>
{:else}
	<div class={`flex flex-wrap items-center gap-1 rounded-lg border border-slate-200/50 bg-slate-100 p-1 ${className}`}>
		{#each languages as lang}
			<a
				href={getUrl(lang.code)}
				data-sveltekit-reload
				class="rounded-md px-2 py-1 text-[10px] font-black no-underline text-slate-400 hover:text-slate-600"
				class:bg-white={currentLang === lang.code}
				class:text-blue-600={currentLang === lang.code}
				class:shadow-sm={currentLang === lang.code}
				dir={lang.dir ?? 'ltr'}
				onclick={() => {
					if (lang.code !== currentLang) {
						onchange?.(currentLang, lang.code);
					}
				}}
			>
				{lang.name}
			</a>
		{/each}
	</div>
{/if}
