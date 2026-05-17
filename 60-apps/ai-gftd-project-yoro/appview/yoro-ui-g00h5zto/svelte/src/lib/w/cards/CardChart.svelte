<script lang="ts">
	import type { CardChartPayload, CardChartSeries } from '../w-types.js';

	interface Props {
		payload: CardChartPayload;
	}

	let { payload }: Props = $props();

	// Simple SVG bar chart (no external library)
	const allValues = $derived(payload.series.flatMap((s: CardChartSeries) => s.data));
	const maxVal = $derived(Math.max(...allValues, 1));
	const barCount = $derived(payload.series[0]?.data.length ?? 0);

	const colors = ['#4ade80', '#60a5fa', '#fb923c', '#f472b6', '#a78bfa'];
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 p-4">
	{#if payload.title}
		<p class="text-[13px] font-bold uppercase tracking-wider text-gv2-text-muted mb-3">{payload.title}</p>
	{/if}

	{#if payload.chartType === 'bar' || payload.chartType === 'line'}
		<svg class="w-full h-[120px]" viewBox="0 0 {barCount * 40} 100" preserveAspectRatio="none">
			{#each payload.series as series, si}
				{#if payload.chartType === 'bar'}
					{#each series.data as val, di}
						{@const barH = (val / maxVal) * 90}
						<rect
							x={di * 40 + si * (30 / payload.series.length) + 2}
							y={100 - barH}
							width={28 / payload.series.length}
							height={barH}
							fill={colors[si % colors.length]}
							rx="2"
							opacity="0.85"
						/>
					{/each}
				{:else}
					<polyline
						fill="none"
						stroke={colors[si % colors.length]}
						stroke-width="2"
						points={series.data.map((v: number, i: number) => `${i * 40 + 15},${100 - (v / maxVal) * 90}`).join(' ')}
					/>
				{/if}
			{/each}
		</svg>
		{#if payload.labels}
			<div class="flex justify-between mt-1 px-1">
				{#each payload.labels as label}
					<span class="text-[10px] text-gv2-text-muted/60">{label}</span>
				{/each}
			</div>
		{/if}
	{:else if payload.chartType === 'pie'}
		{@const pieData = payload.series[0]?.data ?? []}
		{@const total = pieData.reduce((a: number, b: number) => a + b, 0) ?? 1}
		<div class="flex items-center gap-4">
			<svg class="h-[80px] w-[80px] shrink-0" viewBox="-1 -1 2 2">
				{#each pieData as val, i}
					{@const pct = val / total}
					{@const offset = (pieData.slice(0, i).reduce((a: number, b: number) => a + b, 0) ?? 0) / total}
					{@const startAngle = offset * 2 * Math.PI - Math.PI / 2}
					{@const endAngle = (offset + pct) * 2 * Math.PI - Math.PI / 2}
					<path
						d="M {Math.cos(startAngle)} {Math.sin(startAngle)} A 1 1 0 {pct > 0.5 ? 1 : 0} 1 {Math.cos(endAngle)} {Math.sin(endAngle)} L 0 0"
						fill={colors[i % colors.length]}
						opacity="0.85"
					/>
				{/each}
			</svg>
			{#if payload.labels}
				<div class="space-y-1">
					{#each payload.labels as label, i}
						<div class="flex items-center gap-1.5">
							<div class="h-2.5 w-2.5 rounded-full" style="background:{colors[i % colors.length]}"></div>
							<span class="text-[11px] text-gv2-text-muted">{label}</span>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/if}

	<!-- Legend -->
	{#if payload.series.length > 1}
		<div class="flex gap-3 mt-2">
			{#each payload.series as series, i}
				<div class="flex items-center gap-1">
					<div class="h-2 w-2 rounded-full" style="background:{colors[i % colors.length]}"></div>
					<span class="text-[11px] text-gv2-text-muted">{series.name}</span>
				</div>
			{/each}
		</div>
	{/if}
</div>
