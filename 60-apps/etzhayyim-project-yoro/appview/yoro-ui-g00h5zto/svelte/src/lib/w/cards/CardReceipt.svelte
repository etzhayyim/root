<script lang="ts">
	import type { CardReceiptPayload } from '../w-types.js';

	interface Props {
		payload: CardReceiptPayload;
	}

	let { payload }: Props = $props();

	function fmt(n: number): string {
		return n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
	}
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 p-4">
	{#if payload.title}
		<p class="text-[15px] font-bold text-gv2-text-primary mb-3">{payload.title}</p>
	{/if}
	<div class="space-y-2">
		{#each payload.lineItems as item}
			<div class="flex justify-between text-[14px]">
				<span class="text-gv2-text-secondary">{item.desc}{item.qty ? ` x${item.qty}` : ''}</span>
				<span class="font-medium text-gv2-text-primary">{fmt(item.amount)}</span>
			</div>
		{/each}
	</div>
	<div class="mt-3 pt-3 border-t border-gv2-border/20 flex justify-between">
		<span class="text-[15px] font-bold text-gv2-text-primary">Total</span>
		<span class="text-[15px] font-bold text-gv2-text-primary">{fmt(payload.total)} {payload.currency}</span>
	</div>
	{#if payload.paid !== undefined}
		<div class="mt-2 flex justify-end">
			<span class="rounded-full px-2.5 py-0.5 text-[11px] font-bold {payload.paid ? 'bg-emerald-500/15 text-emerald-400' : 'bg-yellow-500/15 text-yellow-400'}">
				{payload.paid ? 'Paid' : 'Pending'}
			</span>
		</div>
	{/if}
</div>
