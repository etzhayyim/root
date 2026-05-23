<script lang="ts">
	import { Badge } from '@etzhayyim/design-system';
	import type { CardSystemPayload } from '../w-types.js';

	interface Props {
		payload: CardSystemPayload;
	}

	let { payload }: Props = $props();

	const healthConfig = $derived.by(() => {
		switch (payload.healthStatus) {
			case 'healthy': return { label: 'Healthy', color: 'text-emerald-400', dot: 'bg-emerald-400' };
			case 'warning': return { label: 'Warning', color: 'text-amber-400', dot: 'bg-amber-400' };
			case 'critical': return { label: 'Critical', color: 'text-red-400', dot: 'bg-red-400' };
			default: return { label: 'Unknown', color: 'text-gv2-text-muted', dot: 'bg-gv2-text-muted' };
		}
	});
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 overflow-hidden">
	<div class="flex items-center gap-3 px-4 py-3">
		<span class="text-[24px] shrink-0">{payload.icon ?? '???'}</span>
		<div class="min-w-0 flex-1">
			<p class="text-[15px] font-bold text-gv2-text-primary truncate">{payload.name}</p>
			<div class="flex items-center gap-1.5 mt-0.5">
				<span class="inline-block h-2 w-2 rounded-full {healthConfig.dot}"></span>
				<span class="text-[12px] font-semibold {healthConfig.color}">{healthConfig.label}</span>
				{#if payload.version}
					<span class="text-[11px] text-gv2-text-muted">v{payload.version}</span>
				{/if}
			</div>
		</div>
		{#if payload.uptime}
			<div class="shrink-0 text-right">
				<p class="text-[13px] font-bold text-gv2-text-primary">{payload.uptime}</p>
				<p class="text-[10px] text-gv2-text-muted">uptime</p>
			</div>
		{/if}
	</div>
	{#if payload.description}
		<div class="border-t border-gv2-border/10 px-4 py-2">
			<p class="text-[13px] text-gv2-text-secondary leading-snug">{payload.description}</p>
		</div>
	{/if}
	{#if payload.components && payload.components.length > 0}
		<div class="flex flex-wrap gap-1.5 px-4 pb-3">
			{#each payload.components as comp}
				<Badge value={comp} variant="default" class="!text-[10px] !h-5 !min-w-0 !px-2" />
			{/each}
		</div>
	{/if}
</div>
