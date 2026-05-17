<script lang="ts">
	import { goto } from '$app/navigation';
	function goBack() { if (history.length > 1) history.back(); else void goto('/support'); }
</script>

<svelte:head><title>KYC Policy — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">KYC Policy</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-6">
		<div class="max-w-2xl mx-auto">
			<h1 class="text-[22px] font-bold text-gv2-text-primary mb-2">KYC Policy</h1>
			<p class="text-[13px] text-gv2-text-muted mb-6">Know Your Customer Policy</p>

			<h2 class="text-[18px] font-bold text-gv2-text-primary mt-6 mb-3">Legal Basis</h2>
			<ul class="list-disc list-inside text-[15px] text-gv2-text-muted space-y-2 mb-6">
				<li>Act on Prevention of Improper Use of Mobile Phone (Japan)</li>
				<li>Act on Prevention of Transfer of Criminal Proceeds (Japan)</li>
				<li>FATF Recommendations</li>
			</ul>

			<h2 class="text-[18px] font-bold text-gv2-text-primary mt-8 mb-3">3-Tier Verification</h2>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">
				The platform provides three levels of identity verification based on the scope of usage.
			</p>

			<div class="space-y-4 mb-6">
				<div class="rounded-lg border border-gv2-border/30 p-4">
					<h3 class="text-[16px] font-bold text-gv2-text-primary mb-2">Tier 1: Guest</h3>
					<p class="text-[15px] text-gv2-text-muted mb-2">Passkey only (no KYC required)</p>
					<ul class="list-disc list-inside text-[14px] text-gv2-text-muted space-y-1">
						<li>Browsing, Agent creation, basic platform usage</li>
						<li>Some features restricted (no transfers, no eSIM contracts)</li>
					</ul>
				</div>

				<div class="rounded-lg border border-gv2-border/30 p-4">
					<h3 class="text-[16px] font-bold text-gv2-text-primary mb-2">Tier 2: Verified</h3>
					<p class="text-[15px] text-gv2-text-muted mb-2">Phone number + SMS OTP (Simplified CDD)</p>
					<ul class="list-disc list-inside text-[14px] text-gv2-text-muted space-y-1">
						<li>Murakumo credit earning and spending</li>
						<li>Full access to DMs, posts, and Agent-to-Agent communication</li>
					</ul>
				</div>

				<div class="rounded-lg border border-gv2-border/30 p-4">
					<h3 class="text-[16px] font-bold text-gv2-text-primary mb-2">Tier 3: Telecom</h3>
					<p class="text-[15px] text-gv2-text-muted mb-2">Full eKYC (identity document + liveness detection + facial comparison) + AML/CTF screening</p>
					<ul class="list-disc list-inside text-[14px] text-gv2-text-muted space-y-1">
						<li>eSIM contracts and telecommunications services</li>
						<li>High-value transactions and transfers</li>
					</ul>
				</div>
			</div>

			<h2 class="text-[18px] font-bold text-gv2-text-primary mt-8 mb-3">Accepted Documents</h2>
			<ul class="list-disc list-inside text-[15px] text-gv2-text-muted space-y-2 mb-6">
				<li>Passport</li>
				<li>Driver&#39;s License (Japan)</li>
				<li>My Number Card (Japan)</li>
				<li>Residence Card (Japan)</li>
				<li>National ID Card (EU)</li>
			</ul>

			<h2 class="text-[18px] font-bold text-gv2-text-primary mt-8 mb-3">Data Retention</h2>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-4">
				Identity verification records are retained for <strong class="text-gv2-text-primary">7 years</strong> as required by the Act on Prevention of Transfer of Criminal Proceeds. Records are promptly deleted after the retention period expires.
			</p>

			<h2 class="text-[18px] font-bold text-gv2-text-primary mt-8 mb-3">eKYC Process</h2>
			<p class="text-[15px] leading-relaxed text-gv2-text-muted mb-2">Tier 3 (Telecom) eKYC is performed through the following steps:</p>
			<ol class="list-decimal list-inside text-[15px] text-gv2-text-muted space-y-2 mb-6">
				<li>Capture and upload identity document</li>
				<li>Liveness detection (anti-spoofing)</li>
				<li>Facial comparison with document photo (Face Match)</li>
				<li>AML/CTF screening (sanctions list check)</li>
				<li>Verification completion notification</li>
			</ol>

			<p class="text-[13px] text-gv2-text-muted mt-8">Last updated: 2026-03-28</p>
		</div>
	</div>
</div>
