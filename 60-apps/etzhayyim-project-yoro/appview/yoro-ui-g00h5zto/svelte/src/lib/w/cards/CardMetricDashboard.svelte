<script lang="ts">
	import type { CardMetricDashboardPayload } from '../w-types.js';

	interface Props {
		payload: CardMetricDashboardPayload;
	}

	let { payload }: Props = $props();

	function trendIcon(trend?: 'up' | 'down' | 'flat'): string {
		if (trend === 'up') return '↑';
		if (trend === 'down') return '↓';
		return '';
	}

	function trendColor(trend?: 'up' | 'down' | 'flat'): string {
		if (trend === 'up') return 'text-emerald-400';
		if (trend === 'down') return 'text-red-400';
		return 'text-gv2-text-muted';
	}
</script>

<div class="grid grid-cols-2 gap-2">
	{#each payload.metrics as metric}
		<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 p-3">
			<p class="text-[11px] font-semibold uppercase tracking-wider text-gv2-text-muted">{metric.label}</p>
			<div class="mt-1 flex items-baseline gap-1.5">
				<span class="text-[22px] font-bold text-gv2-text-primary">{metric.value}</span>
				{#if metric.unit}
					<span class="text-[12px] text-gv2-text-muted">{metric.unit}</span>
				{/if}
				{#if metric.trend}
					<span class="text-[14px] font-semibold {trendColor(metric.trend)}">{trendIcon(metric.trend)}</span>
				{/if}
			</div>
			{#if metric.sparkline && metric.sparkline.length > 1}
				{@const max = Math.max(...metric.sparkline)}
				{@const min = Math.min(...metric.sparkline)}
				{@const range = max - min || 1}
				<svg class="mt-2 h-6 w-full" viewBox="0 0 {metric.sparkline.length - 1} 20" preserveAspectRatio="none">
					<polyline
						fill="none"
						stroke={metric.trend === 'down' ? '#f87171' : '#4ade80'}
						stroke-width="1.5"
						points={metric.sparkline.map((v: number, i: number) => `${i},${20 - ((v - min) / range) * 18}`).join(' ')}
					/>
				</svg>
			{/if}
		</div>
	{/each}
</div>
