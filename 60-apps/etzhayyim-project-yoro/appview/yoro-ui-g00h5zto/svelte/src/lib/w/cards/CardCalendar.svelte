<script lang="ts">
	import type { CardCalendarPayload } from '../w-types.js';

	interface Props {
		payload: CardCalendarPayload;
		onAction?: (action: string) => void;
	}

	let { payload, onAction }: Props = $props();

	function fmtTime(iso: string): string {
		try { return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }); }
		catch { return iso; }
	}
	function fmtDate(iso: string): string {
		try { return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }); }
		catch { return iso; }
	}
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 divide-y divide-gv2-border/10">
	{#each payload.events as ev (ev.id)}
		<button
			type="button"
			class="flex w-full items-center gap-3 px-4 py-3 text-left touch-manipulation active:bg-gv2-bg-hover/50"
			onclick={() => onAction?.(`event:${ev.id}`)}
		>
			<div class="w-1 h-8 rounded-full shrink-0" style="background:{ev.color ?? 'var(--gv2-accent,#06c755)'}"></div>
			<div class="min-w-0 flex-1">
				<p class="text-[14px] font-medium text-gv2-text-primary truncate">{ev.title}</p>
				<p class="text-[12px] text-gv2-text-muted">
					{fmtDate(ev.start)} {fmtTime(ev.start)}{ev.end ? ` – ${fmtTime(ev.end)}` : ''}
				</p>
				{#if ev.location}
					<p class="text-[11px] text-gv2-text-muted/60 truncate">{ev.location}</p>
				{/if}
			</div>
		</button>
	{/each}
</div>
