<script lang="ts">
	import type { CardCarouselPayload } from '../w-types.js';

	interface Props {
		payload: CardCarouselPayload;
		onAction?: (action: string) => void;
	}

	let { payload, onAction }: Props = $props();
</script>

<div class="overflow-x-auto scrollbar-none -mx-1">
	<div class="flex gap-2.5 px-1 py-1" style="width: max-content">
		{#each payload.items as item, i (i)}
			<button
				type="button"
				class="w-[200px] shrink-0 rounded-2xl bg-gv2-bg-card border border-gv2-border/20 overflow-hidden touch-manipulation active:scale-[0.98] transition-transform"
				onclick={() => item.action && onAction?.(item.action)}
				disabled={!item.action}
			>
				{#if item.imageUrl}
					<img src={item.imageUrl} alt={item.title ?? ''} class="h-[120px] w-full object-cover" />
				{/if}
				{#if item.title || item.subtitle}
					<div class="p-3">
						{#if item.title}
							<p class="text-[14px] font-semibold text-gv2-text-primary line-clamp-2">{item.title}</p>
						{/if}
						{#if item.subtitle}
							<p class="mt-0.5 text-[12px] text-gv2-text-muted line-clamp-1">{item.subtitle}</p>
						{/if}
					</div>
				{/if}
			</button>
		{/each}
	</div>
</div>
