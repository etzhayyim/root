<script lang="ts">
	import { goto } from '$app/navigation';
	function goBack() { if (history.length > 1) history.back(); else void goto('/support'); }
</script>

<svelte:head><title>Specified Commercial Transactions Disclosure — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Specified Commercial Transactions Disclosure</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-6">
		<div class="max-w-2xl mx-auto">
			<h1 class="text-[22px] font-bold text-gv2-text-primary mb-6">Disclosure under the Act on Specified Commercial Transactions (Japan)</h1>

			<table class="w-full text-[15px] mb-8">
				<tbody>
					<tr class="border-b border-gv2-border/30">
						<td class="py-3 pr-4 font-semibold text-gv2-text-primary whitespace-nowrap align-top w-[120px]">Operator</td>
						<td class="py-3 text-gv2-text-muted">etzhayyim Co., Ltd.</td>
					</tr>
					<tr class="border-b border-gv2-border/30">
						<td class="py-3 pr-4 font-semibold text-gv2-text-primary whitespace-nowrap align-top">Representative</td>
						<td class="py-3 text-gv2-text-muted">(to be filled)</td>
					</tr>
					<tr class="border-b border-gv2-border/30">
						<td class="py-3 pr-4 font-semibold text-gv2-text-primary whitespace-nowrap align-top">Address</td>
						<td class="py-3 text-gv2-text-muted">(to be filled)</td>
					</tr>
					<tr class="border-b border-gv2-border/30">
						<td class="py-3 pr-4 font-semibold text-gv2-text-primary whitespace-nowrap align-top">Contact</td>
						<td class="py-3 text-gv2-text-muted">
							<a href="mailto:support@etzhayyim.com" class="text-gv2-accent underline">support@etzhayyim.com</a>
						</td>
					</tr>
					<tr class="border-b border-gv2-border/30">
						<td class="py-3 pr-4 font-semibold text-gv2-text-primary whitespace-nowrap align-top">Service</td>
						<td class="py-3 text-gv2-text-muted">etzhayyim Platform (<a href="https://yoro.etzhayyim.com" class="text-gv2-accent underline">yoro.etzhayyim.com</a>)</td>
					</tr>
					<tr class="border-b border-gv2-border/30">
						<td class="py-3 pr-4 font-semibold text-gv2-text-primary whitespace-nowrap align-top">Pricing</td>
						<td class="py-3 text-gv2-text-muted">Free (Murakumo credit system). eSIM data charges apply separately</td>
					</tr>
					<tr class="border-b border-gv2-border/30">
						<td class="py-3 pr-4 font-semibold text-gv2-text-primary whitespace-nowrap align-top">Payment</td>
						<td class="py-3 text-gv2-text-muted">Murakumo compute credit / USDC / USDT</td>
					</tr>
					<tr>
						<td class="py-3 pr-4 font-semibold text-gv2-text-primary whitespace-nowrap align-top">Returns / Cancellation</td>
						<td class="py-3 text-gv2-text-muted">eSIM contracts may be cancelled within 8 days (cooling-off right under Telecommunications Business Act, Article 26-3). No refunds after digital service delivery has commenced</td>
					</tr>
				</tbody>
			</table>

			<p class="text-[13px] text-gv2-text-muted mt-8">Last updated: 2026-03-28</p>
		</div>
	</div>
</div>
