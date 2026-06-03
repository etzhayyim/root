<script lang="ts">
	import type { CardPollPayload, CardPollOption } from '../w-types.js';

	interface Props {
		payload: CardPollPayload;
		onAction?: (action: string, data?: Record<string, unknown>) => void;
	}

	let { payload, onAction }: Props = $props();

	const totalVotes = $derived(payload.options.reduce((sum: number, o: CardPollOption) => sum + (o.count ?? 0), 0));

	function vote(optionId: string) {
		if (payload.closed) return;
		onAction?.('poll.vote', { optionId });
	}
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 p-4 space-y-3">
	<p class="text-[15px] font-bold text-gv2-text-primary">{payload.question}</p>
	{#each payload.options as opt (opt.id)}
		{@const pct = totalVotes > 0 ? Math.round(((opt.count ?? 0) / totalVotes) * 100) : 0}
		<button
			type="button"
			class="relative w-full rounded-xl overflow-hidden text-left min-h-[44px] touch-manipulation {payload.closed ? 'cursor-default' : 'active:opacity-80'}"
			onclick={() => vote(opt.id)}
			disabled={payload.closed}
		>
			<div class="absolute inset-0 bg-[var(--gv2-accent,#06c755)]/10 rounded-xl" style="width:{pct}%"></div>
			<div class="relative flex items-center justify-between px-3 py-2.5">
				<span class="text-[14px] font-medium text-gv2-text-primary">{opt.label}</span>
				<span class="text-[13px] font-semibold text-gv2-text-muted">{pct}%</span>
			</div>
		</button>
	{/each}
	<p class="text-[11px] text-gv2-text-muted">{totalVotes} votes{payload.closed ? ' (closed)' : ''}</p>
</div>
