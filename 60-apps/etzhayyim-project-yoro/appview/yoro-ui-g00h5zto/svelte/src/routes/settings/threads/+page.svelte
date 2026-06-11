<!--
  /settings/threads — Thread display preferences.
-->
<script lang="ts">
	import { goto } from '$app/navigation';

	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/settings');
	}

	let sortOrder = $state('oldest');
	let prioritizeFollows = $state(true);
</script>

<svelte:head>
	<title>Thread Preferences — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Thread Preferences</span>
	</div>

	<div class="flex-1 overflow-y-auto scrollbar-none">
		<div class="px-4 py-4">
			<h4 class="mb-3 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">Sort replies</h4>
			{#each [{ value: 'oldest', label: 'Oldest first' }, { value: 'newest', label: 'Newest first' }, { value: 'most-likes', label: 'Most likes first' }, { value: 'random', label: 'Random (poster\'s choice)' }] as opt}
				<button type="button" class="flex min-h-[44px] w-full items-center justify-between rounded-lg px-3 py-2 text-left touch-manipulation active:bg-gv2-bg-hover/40" onclick={() => sortOrder = opt.value}>
					<span class="text-[15px] text-gv2-text-primary">{opt.label}</span>
					<div class="flex h-5 w-5 items-center justify-center rounded-full border-2 {sortOrder === opt.value ? 'border-[#1185FE] bg-[#1185FE]' : 'border-gv2-text-muted'}">
						{#if sortOrder === opt.value}<svg class="h-3 w-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round"><path d="M5 13l4 4L19 7" /></svg>{/if}
					</div>
				</button>
			{/each}
		</div>
		<div class="px-4 py-4">
			<label class="flex min-h-[52px] items-center justify-between rounded-lg px-3 py-2 touch-manipulation active:bg-gv2-bg-hover/40">
				<div>
					<span class="block text-[15px] text-gv2-text-primary">Prioritize followed users</span>
					<span class="block text-[13px] text-gv2-text-muted">Show replies from people you follow first</span>
				</div>
				<input type="checkbox" bind:checked={prioritizeFollows} class="h-5 w-5 rounded accent-[#1185FE]" />
			</label>
		</div>
	</div>
</div>
