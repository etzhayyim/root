<script lang="ts">
	import type { CardEmbedPayload } from '../w-types.js';

	interface Props {
		payload: CardEmbedPayload;
	}

	let { payload }: Props = $props();

	const TRUSTED_EMBED_HOSTS = new Set([
		'yoro.etzhayyim.com',
		'youtube.com',
		'www.youtube.com',
		'www.youtube-nocookie.com',
		'player.vimeo.com',
	]);

	function isTrustedEmbedUrl(url: string): boolean {
		try {
			const parsed = new URL(url);
			if (parsed.protocol !== 'https:') return false;
			return parsed.hostname.endsWith('.etzhayyim.com') || TRUSTED_EMBED_HOSTS.has(parsed.hostname);
		} catch {
			return false;
		}
	}

	const trustedUrl = $derived(isTrustedEmbedUrl(payload.url) ? payload.url : null);
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 overflow-hidden">
	{#if payload.title}
		<div class="px-3 py-2 border-b border-gv2-border/10">
			<p class="text-[13px] font-semibold text-gv2-text-muted truncate">{payload.title}</p>
		</div>
	{/if}
	{#if trustedUrl}
		<iframe
			src={trustedUrl}
			title={payload.title ?? 'Embedded content'}
			width={payload.width ?? '100%'}
			height={payload.height ?? 300}
			class="w-full border-0"
			sandbox="allow-scripts allow-popups"
			loading="lazy"
			referrerpolicy="strict-origin-when-cross-origin"
		></iframe>
	{:else}
		<div class="px-3 py-4 text-[13px] text-gv2-text-muted">
			Blocked an untrusted embed source.
		</div>
	{/if}
</div>
