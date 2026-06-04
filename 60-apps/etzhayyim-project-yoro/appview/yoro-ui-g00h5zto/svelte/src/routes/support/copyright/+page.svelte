<script lang="ts">
	import { goto } from '$app/navigation';
	function goBack() { if (history.length > 1) history.back(); else void goto('/support'); }
</script>

<svelte:head><title>Copyright Policy — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Copyright Policy</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-6">
		<div class="prose prose-sm max-w-none text-gv2-text-primary">
			<h2 class="text-[20px] font-bold text-gv2-text-primary mb-4">Copyright Policy</h2>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">YORO respects the intellectual property rights of others and expects users to do the same.</p>

			<h3 class="text-[17px] font-bold text-gv2-text-primary mt-6 mb-2">DMCA Compliance</h3>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">YORO complies with the Digital Millennium Copyright Act (DMCA). If you believe your copyrighted work has been infringed, please submit a DMCA takedown notice.</p>

			<h3 class="text-[17px] font-bold text-gv2-text-primary mt-6 mb-2">Filing a Copyright Complaint</h3>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">To file a copyright complaint, you must provide: identification of the copyrighted work, identification of the infringing material, your contact information, a statement of good faith, and a signature.</p>

			<h3 class="text-[17px] font-bold text-gv2-text-primary mt-6 mb-2">Counter-Notification</h3>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">If you believe content was removed in error, you may submit a counter-notification. Details will be provided in the takedown notice.</p>

			<h3 class="text-[17px] font-bold text-gv2-text-primary mt-6 mb-2">Repeat Infringers</h3>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">Accounts that repeatedly infringe copyright will be terminated in accordance with our policies.</p>
		</div>
	</div>
</div>
