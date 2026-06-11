<script lang="ts">
	import { goto } from '$app/navigation';
	function goBack() { if (history.length > 1) history.back(); else void goto('/settings/notifications'); }
	let pushEnabled = $state(true);
	let emailEnabled = $state(false);
	const filterOptions = ['everyone', 'follows-only', 'nobody'];
	let filter = $state('everyone');
</script>

<svelte:head><title>Quotes — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Quotes</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-4">
		<p class="mb-4 text-[13px] text-gv2-text-muted">Manage notifications when someone quotes your post.</p>
		<div class="space-y-1">
			<label class="flex min-h-[52px] items-center justify-between rounded-lg px-3 py-2 touch-manipulation active:bg-gv2-bg-hover/40">
				<div><span class="block text-[15px] text-gv2-text-primary">Push notifications</span><span class="block text-[13px] text-gv2-text-muted">Receive push notifications</span></div>
				<input type="checkbox" bind:checked={pushEnabled} class="h-5 w-5 rounded accent-[#1185FE]" />
			</label>
			<label class="flex min-h-[52px] items-center justify-between rounded-lg px-3 py-2 touch-manipulation active:bg-gv2-bg-hover/40">
				<div><span class="block text-[15px] text-gv2-text-primary">Email notifications</span><span class="block text-[13px] text-gv2-text-muted">Receive email notifications</span></div>
				<input type="checkbox" bind:checked={emailEnabled} class="h-5 w-5 rounded accent-[#1185FE]" />
			</label>
		</div>
		<h4 class="mt-6 mb-3 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">From</h4>
		{#each filterOptions as opt}
			<button type="button" class="flex min-h-[44px] w-full items-center justify-between rounded-lg px-3 py-2 text-left touch-manipulation active:bg-gv2-bg-hover/40" onclick={() => filter = opt}>
				<span class="text-[15px] text-gv2-text-primary capitalize">{opt.replace('-', ' ')}</span>
				<div class="flex h-5 w-5 items-center justify-center rounded-full border-2 {filter === opt ? 'border-[#1185FE] bg-[#1185FE]' : 'border-gv2-text-muted'}">
					{#if filter === opt}<svg class="h-3 w-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round"><path d="M5 13l4 4L19 7" /></svg>{/if}
				</div>
			</button>
		{/each}
	</div>
</div>
