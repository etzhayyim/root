<script lang="ts">
	import type { LanguageCode } from '../language/types.js';
	import { translateMessage } from './client.js';
	import { translateLoading } from './stores.js';

	interface Props {
		text: string;
		targetLang: LanguageCode;
		sourceLang?: LanguageCode;
		recordUri?: string;
		convoId?: string;
		senderDid?: string;
		class?: string;
	}

	const {
		text,
		targetLang,
		sourceLang,
		recordUri,
		convoId,
		senderDid,
		class: className = '',
	}: Props = $props();

	let translatedText = $state<string | null>(null);
	let loading = $state(false);

	async function handleTranslate() {
		if (loading || translatedText) return;
		loading = true;
		try {
			const result = await translateMessage({
				text,
				targetLang,
				sourceLang,
				recordUri,
				convoId,
				senderDid,
			});
			translatedText = result.translatedText;
		} catch {
			translatedText = null;
		} finally {
			loading = false;
		}
	}
</script>

{#if translatedText}
	<div class={`text-sm text-slate-600 ${className}`} dir={['ar', 'he', 'fa', 'ur', 'ps', 'sd', 'yi', 'dv', 'ug'].includes(targetLang) ? 'rtl' : 'ltr'}>
		{translatedText}
	</div>
{:else}
	<button
		type="button"
		class={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] text-slate-400 hover:bg-slate-100 hover:text-slate-600 active:opacity-80 ${className}`}
		onclick={handleTranslate}
		disabled={loading}
	>
		{#if loading}
			<svg class="h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
			</svg>
		{:else}
			<svg class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
				<path d="M7.75 2.75a.75.75 0 00-1.5 0v1.258a32.987 32.987 0 00-3.599.278.75.75 0 10.198 1.487A31.545 31.545 0 018.7 5.545 19.381 19.381 0 017 9.56a19.418 19.418 0 01-1.002-2.05.75.75 0 00-1.384.577 20.935 20.935 0 001.492 2.91 19.613 19.613 0 01-3.828 4.154.75.75 0 10.945 1.164A21.116 21.116 0 007 12.331c.095.132.192.262.29.391a.75.75 0 001.194-.91c-.078-.102-.155-.206-.231-.31a20.856 20.856 0 002.007-4.078c.414.078.831.166 1.252.26a.75.75 0 10.34-1.46 32.72 32.72 0 00-1.396-.296l.097-.484a.75.75 0 00-1.47-.294l-.1.498a33.338 33.338 0 00-1.213-.094V2.75zM17.5 14.75a.75.75 0 01-.707-.497l-3-8.5a.75.75 0 011.414-.506l3 8.5a.75.75 0 01-.707 1.003z" />
			</svg>
		{/if}
		Translate
	</button>
{/if}
