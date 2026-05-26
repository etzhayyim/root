<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import {
		Button,
		Badge,
		NotificationBanner,
		Skeleton,
		EmptyState,
	} from '@etzhayyim/design-system';
	import { apiKey, plan } from '$lib/stores';
	import { plan as planApi, donate, ApiError, type UsageMetric, type DonationPurpose } from '$lib/api';

	// Charter Rider §2 (ADR-2605192115): paid-tier upgrades happen by
	// USDC donation on Base L2 (not Stripe checkout). The form below
	// drives POST /api/donate with purpose='internal-subscription'.
	const TREASURY_ADDRESS = '0x0000000000000000000000000000000000000000'; // TODO: replace with yatabase Safe address on Base L2
	const DEFAULT_PLAN_DONATION_USDC: Record<string, string> = {
		starter:   '11.00',
		developer: '33.00',
		business: '330.00',
	};

	let usage24 = $state<Record<string, UsageMetric> | null>(null);
	let usage30 = $state<Record<string, UsageMetric> | null>(null);
	let loading = $state(true);
	let donateLoading = $state(false);
	let donateOpen = $state(false);
	let donateAmount = $state(DEFAULT_PLAN_DONATION_USDC.developer);
	let donatePurpose = $state<DonationPurpose>('internal-subscription');
	let donateMemo = $state('');
	let donateTxHash = $state<string | null>(null);
	let error = $state('');
	let upgraded = $state(false);

	onMount(() => {
		upgraded = $page.url.searchParams.get('upgraded') === '1';
		void refresh();
	});

	async function refresh() {
		loading = true;
		error = '';
		try {
			const [u24, u30] = await Promise.all([
				planApi.usage($apiKey, 24).catch(() => null),
				planApi.usage($apiKey, 720).catch(() => null),
			]);
			usage24 = u24?.usage ?? null;
			usage30 = u30?.usage ?? null;
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		} finally {
			loading = false;
		}
	}

	function openDonateForm(targetPlan: 'starter' | 'developer' | 'business') {
		donateAmount = DEFAULT_PLAN_DONATION_USDC[targetPlan] ?? donateAmount;
		donatePurpose = 'internal-subscription';
		donateMemo = `yatabase plan: ${targetPlan}`;
		donateTxHash = null;
		donateOpen = true;
	}

	async function submitDonation() {
		donateLoading = true;
		error = '';
		donateTxHash = null;
		try {
			const r = await donate.submit($apiKey, {
				to: TREASURY_ADDRESS,
				amountUsdc: donateAmount,
				purpose: donatePurpose,
				memo: donateMemo || undefined,
			});
			if (r.error) {
				error = r.message || r.error;
				return;
			}
			donateTxHash = r.txHash ?? r.paymentReceipt?.txHash ?? null;
			// Plan flip happens asynchronously via /webhook/usdc after
			// ChartersComplianceRegistry attestation. Refresh after a
			// short delay so the UI reflects the new tier when KV is
			// updated.
			setTimeout(() => { void refresh(); }, 2000);
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		} finally {
			donateLoading = false;
		}
	}

	// Quotas for chart bars
	const PLAN_QUOTAS: Record<string, Record<string, number>> = {
		free: { api_request: 1000, storage_gb_hour: 100 },
		starter: { api_request: 100_000, storage_gb_hour: 10 * 24 },
		developer: { api_request: 1_000_000, storage_gb_hour: 100 * 24 },
		enterprise: { api_request: 50_000_000, storage_gb_hour: 1000 * 24 },
	};

	function quota(metric: string): number {
		const p = $plan?.plan ?? 'free';
		return PLAN_QUOTAS[p]?.[metric] ?? 0;
	}

	function pct(metric: string, qty?: number): number {
		const q = quota(metric);
		if (!q || !qty) return 0;
		return Math.min(100, Math.round((qty / q) * 100));
	}

	const METRIC_ORDER = ['api_request', 'storage_gb_hour', 'storage_egress_gb', 'cypher_query'];
</script>

<div class="mx-auto w-full max-w-5xl space-y-6 px-6 py-10">
	<div class="flex flex-wrap items-end justify-between gap-3">
		<div>
			<h1 class="text-2xl font-semibold text-etzhayyim-text">Billing & usage</h1>
			<p class="mt-1 text-sm text-etzhayyim-secondary">
				Plan from <code>/api/plan</code>, usage from <code>/api/usage</code>. KV-mirrored so it
				stays available even when RW is in recovery.
			</p>
		</div>
		<div class="flex gap-2">
			{#if ($plan?.plan ?? 'free') === 'free'}
				<Button size="md" variant="solid-fill" onclick={() => openDonateForm('developer')}>
					Upgrade via USDC donation — $33
				</Button>
			{:else}
				<Button size="md" variant="outline" onclick={() => openDonateForm('developer')}>
					Make another donation
				</Button>
			{/if}
		</div>
	</div>

	{#if upgraded}
		<NotificationBanner type="success">
			Donation confirmed — your plan has been upgraded.
		</NotificationBanner>
	{/if}

	{#if donateOpen}
		<div class="rounded-2xl border border-etzhayyim-border bg-gftd-card p-6">
			<div class="flex items-start justify-between">
				<div>
					<h2 class="text-lg font-medium text-etzhayyim-text">USDC donation (Base L2)</h2>
					<p class="mt-1 text-sm text-etzhayyim-secondary">
						Per Charter Rider §2 (<a class="underline" href="https://github.com/etzhayyim/root/blob/main/CHARTER-RIDER.md" target="_blank" rel="noreferrer">link</a>),
						paid tiers are SBT↔SBT-bound internal-subscriptions funded by a USDC donation on Base L2.
						The plan flip happens after ChartersComplianceRegistry attestation hits <code>/webhook/usdc</code>.
					</p>
				</div>
				<Button size="sm" variant="outline" onclick={() => (donateOpen = false)}>Close</Button>
			</div>

			<div class="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
				<label class="text-sm text-etzhayyim-secondary">
					Amount (USDC)
					<input
						type="text"
						class="mt-1 w-full rounded-md border border-etzhayyim-border bg-black/30 px-3 py-2 font-mono text-etzhayyim-text"
						bind:value={donateAmount}
						placeholder="33.00"
					/>
				</label>
				<label class="text-sm text-etzhayyim-secondary">
					Purpose
					<select
						class="mt-1 w-full rounded-md border border-etzhayyim-border bg-black/30 px-3 py-2 text-etzhayyim-text"
						bind:value={donatePurpose}
					>
						<option value="donation">donation (unrestricted)</option>
						<option value="kisha">kisha (charitable contribution)</option>
						<option value="grant">grant (time-bound project funding)</option>
						<option value="tithe">tithe (10% Public Fund split)</option>
						<option value="internal-subscription">internal-subscription (plan upgrade)</option>
						<option value="internal-purchase">internal-purchase (one-time SBT-bound)</option>
						<option value="internal-promo">internal-promo (promotional SBT mint)</option>
					</select>
				</label>
				<label class="text-sm text-etzhayyim-secondary md:col-span-2">
					Memo (optional, ≤280 chars)
					<input
						type="text"
						class="mt-1 w-full rounded-md border border-etzhayyim-border bg-black/30 px-3 py-2 text-etzhayyim-text"
						bind:value={donateMemo}
						maxlength="280"
					/>
				</label>
			</div>

			<div class="mt-4 flex gap-2">
				<Button size="md" variant="solid-fill" onclick={submitDonation} aria-disabled={donateLoading}>
					{donateLoading ? 'Submitting…' : 'Submit donation'}
				</Button>
				<Button size="md" variant="outline" onclick={() => (donateOpen = false)}>Cancel</Button>
			</div>

			{#if donateTxHash}
				<NotificationBanner type="success">
					Donation submitted. Tx: <code class="font-mono text-xs">{donateTxHash}</code>
				</NotificationBanner>
			{/if}
		</div>
	{/if}

	{#if error}
		<NotificationBanner type="error">
			<span class="font-mono text-xs">{error}</span>
		</NotificationBanner>
	{/if}

	<!-- Plan card -->
	<div class="rounded-2xl border border-etzhayyim-border bg-gftd-card p-6">
		<div class="flex items-start justify-between">
			<div>
				<p class="text-sm uppercase tracking-wider text-etzhayyim-muted">Current plan</p>
				<p class="mt-2 text-3xl font-semibold text-etzhayyim-text">{$plan?.plan ?? 'free'}</p>
				<p class="mt-1 text-sm text-etzhayyim-secondary">
					{$plan?.status ?? 'active'} ·
					{$plan?.billing_period_end
						? `renews ${new Date($plan.billing_period_end).toLocaleDateString()}`
						: 'no expiry'}
				</p>
			</div>
			<Badge type={$plan?.plan === 'free' ? 'tertiary' : 'primary'}>
				{$plan?.plan === 'free' ? 'free tier' : 'paid'}
			</Badge>
		</div>
	</div>

	<!-- Usage 24h -->
	<div class="rounded-2xl border border-etzhayyim-border bg-gftd-card p-6">
		<h2 class="text-lg font-medium text-etzhayyim-text">Usage (24h)</h2>
		{#if loading}
			<div class="mt-4 space-y-3">
				{#each [1, 2, 3] as _}
					<Skeleton class="h-12 w-full" />
				{/each}
			</div>
		{:else if !usage24 || Object.keys(usage24).length === 0}
			<div class="mt-4">
				<EmptyState
					title="No usage in the last 24h"
					description="Once you start hitting the API, usage events flow into vertex_billing_event and show up here."
				/>
			</div>
		{:else}
			<dl class="mt-4 space-y-4">
				{#each METRIC_ORDER as m}
					{@const v = usage24[m]}
					{#if v}
						<div>
							<div class="flex items-end justify-between text-sm">
								<dt class="font-mono text-etzhayyim-text">{m}</dt>
								<dd class="text-etzhayyim-secondary">
									{v.totalQty.toLocaleString()}
									{#if quota(m)}
										<span class="text-etzhayyim-muted">/ {quota(m).toLocaleString()}</span>
									{/if}
								</dd>
							</div>
							{#if quota(m)}
								<div class="mt-2 h-2 w-full rounded-full bg-black/30">
									<div
										class={`h-2 rounded-full transition-all ${
											pct(m, v.totalQty) > 80
												? 'bg-red-500'
												: pct(m, v.totalQty) > 50
													? 'bg-amber-400'
													: 'bg-emerald-500'
										}`}
										style={`width: ${pct(m, v.totalQty)}%`}
										aria-label={`${m} usage ${pct(m, v.totalQty)}%`}
									></div>
								</div>
							{/if}
						</div>
					{/if}
				{/each}
			</dl>
		{/if}
	</div>

	<!-- Usage 30d -->
	{#if usage30 && Object.keys(usage30).length > 0}
		<div class="rounded-2xl border border-etzhayyim-border bg-gftd-card p-6">
			<h2 class="text-lg font-medium text-etzhayyim-text">Usage (30d total)</h2>
			<dl class="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
				{#each METRIC_ORDER as m}
					{@const v = usage30[m]}
					{#if v}
						<div class="rounded-lg border border-etzhayyim-border bg-black/20 p-3">
							<dt class="text-xs font-mono text-etzhayyim-muted">{m}</dt>
							<dd class="mt-1 text-lg font-semibold text-etzhayyim-text">
								{v.totalQty.toLocaleString()}
							</dd>
						</div>
					{/if}
				{/each}
			</dl>
		</div>
	{/if}
</div>
