<script lang="ts">
	import { goto } from '$app/navigation';
	function goBack() { if (history.length > 1) history.back(); else void goto('/support'); }
</script>

<svelte:head><title>Community Guidelines — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Community Guidelines</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-6">
		<div class="prose prose-sm max-w-none text-gv2-text-primary">
			<h2 class="text-[20px] font-bold text-gv2-text-primary mb-4">Community Guidelines</h2>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">YORO is committed to building a safe and welcoming community for everyone. These guidelines help ensure that all users can enjoy a positive experience.</p>

			<h3 class="text-[17px] font-bold text-gv2-text-primary mt-6 mb-2">Be Respectful</h3>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">Treat others with kindness and respect. Harassment, bullying, and hate speech are not tolerated.</p>

			<h3 class="text-[17px] font-bold text-gv2-text-primary mt-6 mb-2">No Spam or Manipulation</h3>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">Do not engage in spamming, artificial engagement manipulation, or coordinated inauthentic behavior.</p>

			<h3 class="text-[17px] font-bold text-gv2-text-primary mt-6 mb-2">Protect Privacy</h3>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">Do not share others' personal information without their consent. Respect the privacy of all users.</p>

			<h3 class="text-[17px] font-bold text-gv2-text-primary mt-6 mb-2">Content Guidelines</h3>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">Label sensitive content appropriately. Do not post illegal content or content that exploits minors.</p>

			<h3 class="text-[17px] font-bold text-gv2-text-primary mt-6 mb-2">Enforcement</h3>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">Violations of these guidelines may result in content removal, account suspension, or permanent ban. Reports are reviewed by our moderation team.</p>
		</div>
	</div>
</div>
