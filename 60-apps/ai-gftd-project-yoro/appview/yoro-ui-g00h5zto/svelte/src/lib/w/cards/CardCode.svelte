<script lang="ts">
	import type { CardCodePayload } from '../w-types.js';

	interface Props {
		payload: CardCodePayload;
	}

	let { payload }: Props = $props();
	let copied = $state(false);

	async function copyCode() {
		try {
			await navigator.clipboard.writeText(payload.code);
			copied = true;
			setTimeout(() => { copied = false; }, 2000);
		} catch { /* ignore */ }
	}
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 overflow-hidden">
	<div class="flex items-center justify-between px-3 py-1.5 bg-gv2-bg-hover/50">
		<span class="text-[11px] font-mono text-gv2-text-muted">{payload.filename ?? payload.language}</span>
		<button
			type="button"
			class="text-[11px] text-gv2-text-muted touch-manipulation active:text-gv2-text-primary"
			onclick={copyCode}
		>{copied ? 'Copied' : 'Copy'}</button>
	</div>
	<pre class="overflow-x-auto p-3 text-[13px] leading-relaxed text-gv2-text-primary scrollbar-none"><code>{payload.code}</code></pre>
</div>
