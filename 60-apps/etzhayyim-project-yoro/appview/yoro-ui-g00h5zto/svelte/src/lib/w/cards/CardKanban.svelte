<script lang="ts">
	import type { CardKanbanPayload } from '../w-types.js';

	interface Props {
		payload: CardKanbanPayload;
		onAction?: (action: string) => void;
	}

	let { payload, onAction }: Props = $props();
</script>

<div class="overflow-x-auto scrollbar-none -mx-1">
	<div class="flex gap-2.5 px-1 py-1" style="width: max-content">
		{#each payload.columns as col (col.id)}
			<div class="w-[200px] shrink-0">
				<p class="mb-2 px-1 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">{col.title} <span class="text-gv2-text-muted/50">({col.cards.length})</span></p>
				<div class="space-y-2">
					{#each col.cards as card (card.id)}
						<button
							type="button"
							class="w-full rounded-xl bg-gv2-bg-card border border-gv2-border/20 p-3 text-left touch-manipulation active:scale-[0.98] transition-transform"
							onclick={() => onAction?.(`card:${card.id}`)}
						>
							{#if card.color}
								<div class="w-6 h-1 rounded-full mb-2" style="background:{card.color}"></div>
							{/if}
							<p class="text-[13px] font-medium text-gv2-text-primary line-clamp-2">{card.title}</p>
							{#if card.assignee}
								<p class="mt-1 text-[11px] text-gv2-text-muted">{card.assignee}</p>
							{/if}
						</button>
					{/each}
				</div>
			</div>
		{/each}
	</div>
</div>
