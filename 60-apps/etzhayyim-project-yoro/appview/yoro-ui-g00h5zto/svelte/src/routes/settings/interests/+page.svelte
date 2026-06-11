<script lang="ts">
	import { goto } from '$app/navigation';
	function goBack() { if (history.length > 1) history.back(); else void goto('/settings'); }
	const topics = ['Technology', 'Science', 'Sports', 'Music', 'Art', 'Gaming', 'Politics', 'Business', 'Food', 'Travel', 'Fashion', 'Health'];
	let selected = $state<string[]>([]);
</script>

<svelte:head><title>Interests — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Interests</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-4">
		<p class="mb-4 text-[13px] text-gv2-text-muted">Select topics you're interested in to personalize your feed.</p>
		<div class="flex flex-wrap gap-2">
			{#each topics as topic}
				<button type="button" class="min-h-[36px] rounded-full border px-4 py-1.5 text-[14px] font-medium touch-manipulation {selected.includes(topic) ? 'border-[#1185FE] bg-[#1185FE]/10 text-[#1185FE]' : 'border-gv2-border/40 text-gv2-text-primary active:bg-gv2-bg-hover/40'}" onclick={() => selected = selected.includes(topic) ? selected.filter(t => t !== topic) : [...selected, topic]}>
					{topic}
				</button>
			{/each}
		</div>
	</div>
</div>
