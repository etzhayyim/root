<script lang="ts">
	import type { CardTablePayload } from '../w-types.js';

	interface Props {
		payload: CardTablePayload;
	}

	let { payload }: Props = $props();
	let sortKey = $state('');
	let sortAsc = $state(true);

	let sortedRows = $derived.by(() => {
		if (!sortKey) return payload.rows;
		return [...payload.rows].sort((a, b) => {
			const va = a[sortKey] ?? '';
			const vb = b[sortKey] ?? '';
			const cmp = typeof va === 'number' && typeof vb === 'number' ? va - vb : String(va).localeCompare(String(vb));
			return sortAsc ? cmp : -cmp;
		});
	});

	function toggleSort(key: string) {
		if (sortKey === key) { sortAsc = !sortAsc; }
		else { sortKey = key; sortAsc = true; }
	}
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 overflow-hidden">
	{#if payload.title}
		<div class="px-4 pt-3 pb-1">
			<p class="text-[13px] font-bold uppercase tracking-wider text-gv2-text-muted">{payload.title}</p>
		</div>
	{/if}
	<div class="overflow-x-auto scrollbar-none">
		<table class="w-full text-[13px]">
			<thead>
				<tr class="border-b border-gv2-border/20">
					{#each payload.columns as col (col.key)}
						<th
							class="px-3 py-2 text-left font-semibold text-gv2-text-muted whitespace-nowrap {col.sortable ? 'cursor-pointer active:opacity-60' : ''}"
							onclick={() => col.sortable && toggleSort(col.key)}
						>
							{col.label}
							{#if sortKey === col.key}
								<span class="ml-0.5">{sortAsc ? '↑' : '↓'}</span>
							{/if}
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each sortedRows as row, i}
					<tr class="border-b border-gv2-border/10 {i % 2 === 0 ? '' : 'bg-gv2-bg-hover/20'}">
						{#each payload.columns as col (col.key)}
							<td class="px-3 py-2 text-gv2-text-primary whitespace-nowrap">{row[col.key] ?? ''}</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
