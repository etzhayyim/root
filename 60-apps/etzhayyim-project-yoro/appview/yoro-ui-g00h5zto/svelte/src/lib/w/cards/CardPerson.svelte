<script lang="ts">
	import { Avatar, Badge } from '@etzhayyim/design-system';
	import type { CardPersonPayload } from '../w-types.js';

	interface Props {
		payload: CardPersonPayload;
	}

	let { payload }: Props = $props();
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 overflow-hidden">
	<div class="flex items-center gap-3 px-4 py-3">
		<Avatar
			src={payload.avatar}
			fallback={payload.name.slice(0, 2).toUpperCase()}
			size="md"
			class="shrink-0"
		/>
		<div class="min-w-0 flex-1">
			<p class="text-[15px] font-bold text-gv2-text-primary truncate">{payload.name}</p>
			{#if payload.occupation}
				<p class="text-[12px] text-gv2-text-muted truncate">{payload.occupation}</p>
			{/if}
		</div>
		{#if payload.competenceBadge}
			<Badge value={payload.competenceBadge} variant="accent" class="shrink-0 !text-[10px] !h-5 !min-w-0 !px-2" />
		{/if}
	</div>
	{#if payload.description}
		<div class="border-t border-gv2-border/10 px-4 py-2">
			<p class="text-[13px] text-gv2-text-secondary leading-snug">{payload.description}</p>
		</div>
	{/if}
	{#if payload.tags && payload.tags.length > 0}
		<div class="flex flex-wrap gap-1.5 px-4 pb-3">
			{#each payload.tags as tag}
				<span class="rounded-full bg-gv2-bg-hover px-2 py-0.5 text-[11px] font-medium text-gv2-text-muted">{tag}</span>
			{/each}
		</div>
	{/if}
</div>
