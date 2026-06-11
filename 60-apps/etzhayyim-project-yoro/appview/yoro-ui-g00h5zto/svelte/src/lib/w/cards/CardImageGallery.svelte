<script lang="ts">
	import type { CardImageGalleryPayload } from '../w-types.js';

	interface Props {
		payload: CardImageGalleryPayload;
	}

	let { payload }: Props = $props();
	let selected = $state<number | null>(null);
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 overflow-hidden">
	{#if selected !== null}
		<!-- Full preview -->
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="relative" onclick={() => { selected = null; }}>
			<img src={payload.images[selected].url} alt={payload.images[selected].alt ?? ''} class="w-full max-h-[400px] object-contain bg-black" />
			{#if payload.images[selected].caption}
				<p class="p-2 text-[13px] text-gv2-text-muted text-center">{payload.images[selected].caption}</p>
			{/if}
		</div>
	{:else}
		<!-- Grid -->
		<div class="grid grid-cols-3 gap-0.5">
			{#each payload.images as img, i (i)}
				<button
					type="button"
					class="aspect-square overflow-hidden touch-manipulation active:opacity-80"
					onclick={() => { selected = i; }}
				>
					<img src={img.url} alt={img.alt ?? ''} class="h-full w-full object-cover" />
				</button>
			{/each}
		</div>
	{/if}
</div>
