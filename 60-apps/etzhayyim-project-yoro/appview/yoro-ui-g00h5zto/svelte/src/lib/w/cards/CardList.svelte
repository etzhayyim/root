<script lang="ts">
	import { Avatar } from '@etzhayyim/design-system';
	import type { CardListPayload } from '../w-types.js';

	interface Props {
		payload: CardListPayload;
		onAction?: (action: string) => void;
	}

	let { payload, onAction }: Props = $props();
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 overflow-hidden">
	{#if payload.title}
		<div class="px-4 pt-3 pb-1">
			<p class="text-[13px] font-bold uppercase tracking-wider text-gv2-text-muted">{payload.title}</p>
		</div>
	{/if}
	<div class="divide-y divide-gv2-border/10">
		{#each payload.items as item (item.id)}
			<button
				type="button"
				class="flex w-full items-center gap-3 px-4 py-3 text-left touch-manipulation active:bg-gv2-bg-hover/50 transition-colors"
				onclick={() => item.action && onAction?.(item.action)}
				disabled={!item.action}
			>
				{#if item.imageUrl}
					<img src={item.imageUrl} alt="" class="h-10 w-10 rounded-xl object-cover shrink-0" />
				{:else if item.icon}
					<span class="text-[20px] shrink-0">{item.icon}</span>
				{:else}
					<Avatar fallback={item.label} size="sm" class="shrink-0 !bg-gv2-bg-hover !text-gv2-text-muted !text-[11px]" />
				{/if}
				<div class="min-w-0 flex-1">
					<p class="text-[15px] font-medium text-gv2-text-primary truncate">{item.label}</p>
					{#if item.sublabel}
						<p class="text-[12px] text-gv2-text-muted truncate">{item.sublabel}</p>
					{/if}
				</div>
				{#if item.action}
					<svg class="h-4 w-4 shrink-0 text-gv2-text-muted/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6" /></svg>
				{/if}
			</button>
		{/each}
	</div>
</div>
