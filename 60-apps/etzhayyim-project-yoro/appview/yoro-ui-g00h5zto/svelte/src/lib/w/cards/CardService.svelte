<script lang="ts">
	import { Badge } from '@etzhayyim/design-system';
	import type { CardServicePayload } from '../w-types.js';

	interface Props {
		payload: CardServicePayload;
	}

	let { payload }: Props = $props();

	const statusConfig = $derived.by(() => {
		switch (payload.status) {
			case 'online': return { label: 'Online', color: 'text-emerald-400', dot: 'bg-emerald-400' };
			case 'degraded': return { label: 'Degraded', color: 'text-amber-400', dot: 'bg-amber-400' };
			case 'offline': return { label: 'Offline', color: 'text-red-400', dot: 'bg-red-400' };
			case 'maintenance': return { label: 'Maintenance', color: 'text-blue-400', dot: 'bg-blue-400' };
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
				<span class="inline-block h-2 w-2 rounded-full {statusConfig.dot}"></span>
				<span class="text-[12px] font-semibold {statusConfig.color}">{statusConfig.label}</span>
				{#if payload.version}
					<span class="text-[11px] text-gv2-text-muted">v{payload.version}</span>
				{/if}
			</div>
		</div>
	</div>
	{#if payload.description}
		<div class="border-t border-gv2-border/10 px-4 py-2">
			<p class="text-[13px] text-gv2-text-secondary leading-snug">{payload.description}</p>
		</div>
	{/if}
	{#if payload.capabilities && payload.capabilities.length > 0}
		<div class="flex flex-wrap gap-1.5 px-4 pb-3">
			{#each payload.capabilities as cap}
				<Badge value={cap} variant="default" class="!text-[10px] !h-5 !min-w-0 !px-2" />
			{/each}
		</div>
	{/if}
</div>
