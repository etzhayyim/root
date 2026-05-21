<script lang="ts">
	import { Badge, Button } from '@gftdcojp/design-system';
	import { identity, plan, apiKey, tenantLabel } from '$lib/stores';

	function copyKey() {
		if (!$apiKey) return;
		void navigator.clipboard.writeText($apiKey);
	}
</script>

<div class="mx-auto w-full max-w-5xl space-y-6 px-6 py-10">
	<div>
		<p class="text-sm uppercase tracking-wider text-gftd-muted">Welcome back</p>
		<h1 class="mt-1 text-3xl font-semibold text-gftd-text">{$tenantLabel}</h1>
		<p class="mt-2 text-sm text-gftd-secondary">
			Your yatabase tenant — graph DB, storage, auth, and MCP from one dashboard.
		</p>
	</div>

	<div class="grid gap-4 md:grid-cols-3">
		<!-- Plan card -->
		<div class="rounded-2xl border border-gftd-border bg-gftd-card p-5">
			<div class="flex items-center justify-between">
				<h2 class="text-sm font-medium text-gftd-secondary">Current plan</h2>
				<Badge type={$plan?.plan === 'free' ? 'tertiary' : 'primary'}>
					{$plan?.plan ?? 'free'}
				</Badge>
			</div>
			<p class="mt-3 text-2xl font-semibold text-gftd-text">
				{$plan?.plan === 'free' ? 'Free tier' : `${$plan?.plan} plan`}
			</p>
			<p class="mt-1 text-xs text-gftd-muted">
				{$plan?.status ?? 'active'} ·
				{$plan?.billing_period_end
					? `until ${new Date($plan.billing_period_end).toLocaleDateString()}`
					: 'no expiry'}
			</p>
			<a href="/studio/billing" class="mt-4 inline-block text-sm text-gftd-accent hover:underline"
				>Manage billing →</a
			>
		</div>

		<!-- Identity card -->
		<div class="rounded-2xl border border-gftd-border bg-gftd-card p-5">
			<h2 class="text-sm font-medium text-gftd-secondary">Identity</h2>
			<dl class="mt-3 space-y-2 text-sm">
				<div>
					<dt class="text-gftd-muted">orgDid</dt>
					<dd class="truncate font-mono text-xs text-gftd-text">{$identity?.orgDid ?? '—'}</dd>
				</div>
				<div>
					<dt class="text-gftd-muted">actor did</dt>
					<dd class="truncate font-mono text-xs text-gftd-text">{$identity?.did ?? '—'}</dd>
				</div>
				<div>
					<dt class="text-gftd-muted">product scope</dt>
					<dd class="font-mono text-xs text-gftd-text">{$identity?.productScope ?? 'yata'}</dd>
				</div>
			</dl>
		</div>

		<!-- API key card -->
		<div class="rounded-2xl border border-gftd-border bg-gftd-card p-5">
			<h2 class="text-sm font-medium text-gftd-secondary">API key</h2>
			<p class="mt-3 font-mono text-xs text-gftd-text">
				{$apiKey ? `${$apiKey.slice(0, 18)}…${$apiKey.slice(-4)}` : '—'}
			</p>
			<p class="mt-1 text-xs text-gftd-muted">Stored locally in this browser.</p>
			<Button size="sm" variant="outline" onclick={copyKey}>Copy</Button>
		</div>
	</div>

	<!-- Quickstart -->
	<div class="rounded-2xl border border-gftd-border bg-gftd-card p-6">
		<h2 class="text-lg font-semibold text-gftd-text">Quick wins (60 seconds each)</h2>
		<ol class="mt-4 space-y-3 text-sm text-gftd-secondary">
			<li class="flex items-start gap-3">
				<span class="mt-0.5 w-5 shrink-0 text-gftd-accent">1.</span>
				<span>
					Run a Cypher query —
					<a href="/studio/cypher" class="text-gftd-accent hover:underline">open editor</a> and
					try <code class="rounded bg-black/40 px-1 py-0.5 text-gftd-text">CREATE (n:Thing {`{name:'hello'}`})</code>.
				</span>
			</li>
			<li class="flex items-start gap-3">
				<span class="mt-0.5 w-5 shrink-0 text-gftd-accent">2.</span>
				<span>
					Upload an object —
					<a href="/studio/storage" class="text-gftd-accent hover:underline">storage browser</a>
					→ drag a file in.
				</span>
			</li>
			<li class="flex items-start gap-3">
				<span class="mt-0.5 w-5 shrink-0 text-gftd-accent">3.</span>
				<span>
					Wire MCP into Claude Code:
					<code class="rounded bg-black/40 px-1 py-0.5 text-gftd-text"
						>https://yatabase.gftd.ai/mcp</code
					>
					with your API key as the bearer.
				</span>
			</li>
		</ol>
	</div>
</div>
