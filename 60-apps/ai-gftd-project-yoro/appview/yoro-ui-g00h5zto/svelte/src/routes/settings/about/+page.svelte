<script lang="ts">
	import { goto } from '$app/navigation';
	function goBack() { if (history.length > 1) history.back(); else void goto('/settings'); }
</script>

<svelte:head><title>About — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">About</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-4">
		<div class="space-y-1">
			<div class="flex min-h-[44px] items-center justify-between rounded-lg px-3 py-2">
				<span class="text-[14px] text-gv2-text-muted">App version</span>
				<span class="text-[15px] text-gv2-text-primary">1.0.0</span>
			</div>
			<div class="flex min-h-[44px] items-center justify-between rounded-lg px-3 py-2">
				<span class="text-[14px] text-gv2-text-muted">Protocol</span>
				<span class="text-[15px] text-gv2-text-primary">AT Protocol + Signal</span>
			</div>
			<button type="button" class="flex min-h-[44px] w-full items-center rounded-lg px-3 py-2 text-left touch-manipulation active:bg-gv2-bg-hover/40" onclick={() => goto('/terms')}>
				<span class="text-[15px] text-gv2-text-primary">Terms of Service</span>
				<svg class="ml-auto h-4 w-4 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M9 5l7 7-7 7" /></svg>
			</button>
			<button type="button" class="flex min-h-[44px] w-full items-center rounded-lg px-3 py-2 text-left touch-manipulation active:bg-gv2-bg-hover/40" onclick={() => goto('/privacy')}>
				<span class="text-[15px] text-gv2-text-primary">Privacy Policy</span>
				<svg class="ml-auto h-4 w-4 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M9 5l7 7-7 7" /></svg>
			</button>
		</div>
	</div>
</div>
