<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import {
		Button,
		Badge,
		NotificationBanner,
		Skeleton,
		EmptyState,
	} from '@gftdcojp/design-system';
	import { apiKey, plan } from '$lib/stores';
	import { plan as planApi, auth, ApiError, type UsageMetric } from '$lib/api';

	let usage24 = $state<Record<string, UsageMetric> | null>(null);
	let usage30 = $state<Record<string, UsageMetric> | null>(null);
	let loading = $state(true);
	let portalLoading = $state(false);
	let upgradeLoading = $state(false);
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

	async function openPortal() {
		portalLoading = true;
		error = '';
		try {
			const r = await auth.stripePortal($apiKey);
			const url = r.portalUrl ?? r.url;
			if (url) window.location.href = url;
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		} finally {
			portalLoading = false;
		}
	}

	async function startUpgrade() {
		upgradeLoading = true;
		error = '';
		try {
			const r = await auth.upgrade($apiKey, 'developer');
			if (r.checkoutUrl) window.location.href = r.checkoutUrl;
			else if (r.message) error = r.message; // stub mode
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		} finally {
			upgradeLoading = false;
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
			<h1 class="text-2xl font-semibold text-gftd-text">Billing & usage</h1>
			<p class="mt-1 text-sm text-gftd-secondary">
				Plan from <code>/api/plan</code>, usage from <code>/api/usage</code>. KV-mirrored so it
				stays available even when RW is in recovery.
			</p>
		</div>
		<div class="flex gap-2">
			{#if ($plan?.plan ?? 'free') === 'free'}
				<Button size="md" variant="solid-fill" onclick={startUpgrade} aria-disabled={upgradeLoading}>
					{upgradeLoading ? 'Redirecting…' : 'Upgrade to Developer — $33/mo'}
				</Button>
			{:else}
				<Button size="md" variant="outline" onclick={openPortal} aria-disabled={portalLoading}>
					{portalLoading ? 'Opening…' : 'Manage subscription'}
				</Button>
			{/if}
		</div>
	</div>

	{#if upgraded}
		<NotificationBanner type="success">
			Payment confirmed — your plan has been upgraded. Welcome to Developer!
		</NotificationBanner>
	{/if}

	{#if error}
		<NotificationBanner type="error">
			<span class="font-mono text-xs">{error}</span>
		</NotificationBanner>
	{/if}

	<!-- Plan card -->
	<div class="rounded-2xl border border-gftd-border bg-gftd-card p-6">
		<div class="flex items-start justify-between">
			<div>
				<p class="text-sm uppercase tracking-wider text-gftd-muted">Current plan</p>
				<p class="mt-2 text-3xl font-semibold text-gftd-text">{$plan?.plan ?? 'free'}</p>
				<p class="mt-1 text-sm text-gftd-secondary">
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
	<div class="rounded-2xl border border-gftd-border bg-gftd-card p-6">
		<h2 class="text-lg font-medium text-gftd-text">Usage (24h)</h2>
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
								<dt class="font-mono text-gftd-text">{m}</dt>
								<dd class="text-gftd-secondary">
									{v.totalQty.toLocaleString()}
									{#if quota(m)}
										<span class="text-gftd-muted">/ {quota(m).toLocaleString()}</span>
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
		<div class="rounded-2xl border border-gftd-border bg-gftd-card p-6">
			<h2 class="text-lg font-medium text-gftd-text">Usage (30d total)</h2>
			<dl class="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
				{#each METRIC_ORDER as m}
					{@const v = usage30[m]}
					{#if v}
						<div class="rounded-lg border border-gftd-border bg-black/20 p-3">
							<dt class="text-xs font-mono text-gftd-muted">{m}</dt>
							<dd class="mt-1 text-lg font-semibold text-gftd-text">
								{v.totalQty.toLocaleString()}
							</dd>
						</div>
					{/if}
				{/each}
			</dl>
		</div>
	{/if}
</div>
