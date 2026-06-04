<script lang="ts">
	import type { LanguageCode } from '../language/types.js';
	import { getLanguagesByTier, getLanguageName } from '../language/languages.js';
	import { autoTranslatePage } from './client.js';
	import { pageTranslateActive, translateTargetLang, translateLoading, detectedSourceLang } from './stores.js';

	interface Props {
		class?: string;
	}

	const { class: className = '' }: Props = $props();

	let translatedCount = $state(0);
	let selectedLang = $state<LanguageCode | null>(null);

	const tier1Languages = getLanguagesByTier(1);

	async function handleTranslate() {
		if (!selectedLang) return;
		translateTargetLang.set(selectedLang);
		pageTranslateActive.set(true);
		const count = await autoTranslatePage(selectedLang);
		translatedCount = count;
	}

	function handleRestore() {
		pageTranslateActive.set(false);
		translateTargetLang.set(null);
		translatedCount = 0;
		window.location.reload();
	}
</script>

<div class={`flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm ${className}`}>
	{#if $pageTranslateActive}
		<span class="text-[13px] text-slate-600">
			Translated to {getLanguageName($translateTargetLang ?? '')} ({translatedCount} texts)
		</span>
		<button
			type="button"
			class="ml-auto rounded px-2 py-1 text-[12px] font-medium text-blue-600 hover:bg-blue-50 active:opacity-80"
			onclick={handleRestore}
		>
			Show original
		</button>
	{:else}
		<svg class="h-4 w-4 shrink-0 text-slate-400" viewBox="0 0 20 20" fill="currentColor">
			<path d="M7.75 2.75a.75.75 0 00-1.5 0v1.258a32.987 32.987 0 00-3.599.278.75.75 0 10.198 1.487A31.545 31.545 0 018.7 5.545 19.381 19.381 0 017 9.56a19.418 19.418 0 01-1.002-2.05.75.75 0 00-1.384.577 20.935 20.935 0 001.492 2.91 19.613 19.613 0 01-3.828 4.154.75.75 0 10.945 1.164A21.116 21.116 0 007 12.331c.095.132.192.262.29.391a.75.75 0 001.194-.91c-.078-.102-.155-.206-.231-.31a20.856 20.856 0 002.007-4.078c.414.078.831.166 1.252.26a.75.75 0 10.34-1.46 32.72 32.72 0 00-1.396-.296l.097-.484a.75.75 0 00-1.47-.294l-.1.498a33.338 33.338 0 00-1.213-.094V2.75z" />
		</svg>
		<span class="text-[13px] text-slate-500">Translate this page</span>
		<select
			class="ml-1 rounded border border-slate-200 bg-white px-2 py-1 text-[12px] outline-none"
			onchange={(e) => { selectedLang = e.currentTarget.value as LanguageCode; }}
		>
			<option value="">Select language</option>
			{#each tier1Languages as lang}
				<option value={lang.code}>{lang.name}</option>
			{/each}
		</select>
		<button
			type="button"
			class="rounded bg-blue-500 px-3 py-1 text-[12px] font-medium text-white hover:bg-blue-600 active:opacity-80 disabled:opacity-40"
			onclick={handleTranslate}
			disabled={!selectedLang || $translateLoading}
		>
			{$translateLoading ? 'Translating...' : 'Translate'}
		</button>
	{/if}
</div>
