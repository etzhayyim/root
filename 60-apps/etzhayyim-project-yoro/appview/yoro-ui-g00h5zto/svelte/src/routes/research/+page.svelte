<!--
  /research — Product/price research dashboard (yoro.productIngest).
  Reads vertex_yoro_product_research via XRPC com.etzhayyim.apps.yoro.listProductResearch.
  Triggers ingest via XRPC com.etzhayyim.apps.yoro.ingestProductCategory.
-->
<script lang="ts">
	import { browser } from '$app/environment';
	import { atQuery, atProcedure } from '$lib/atproto-agent';
	import { Skeleton } from '@etzhayyim/design-system';

	type ResearchRow = {
		vertex_id: string;
		actor_did: string;
		query: string;
		category: string | null;
		retailers: string;
		total_offers: number;
		offers_by_retailer: string;
		min_price_jpy: number | null;
		max_price_jpy: number | null;
		median_price_jpy: number | null;
		created_at: string;
		job_id: string;
	};

	let items = $state<ResearchRow[]>([]);
	let loading = $state(true);
	let triggering = $state(false);
	let queryInput = $state('スタンディングデスク器具');
	let categoryInput = $state('office.standing-desk');
	let lastJobStatus = $state<string | null>(null);

	const RETAILERS = ['amazon-jp', 'rakuten', 'ikea-jp', 'flexispot-jp', 'yodobashi', 'kagu365'];

	async function load() {
		loading = true;
		try {
			const res = await atQuery('com.etzhayyim.apps.yoro.listProductResearch', { limit: 50 }) as { items: ResearchRow[] };
			items = res.items ?? [];
		} catch {
			items = [];
		} finally {
			loading = false;
		}
	}

	async function trigger() {
		if (!queryInput.trim()) return;
		triggering = true;
		lastJobStatus = null;
		try {
			const res = await atProcedure('com.etzhayyim.apps.yoro.ingestProductCategory', {
				query: queryInput.trim(),
				category: categoryInput.trim() || undefined,
				retailers: [],
				maxItemsPerRetailer: 20,
			}) as { jobId: string; status: string };
			lastJobStatus = `${res.status} (${res.jobId || 'no-id'})`;
			setTimeout(load, 5000);
		} catch (e) {
			lastJobStatus = `error: ${(e as Error).message}`;
		} finally {
			triggering = false;
		}
	}

	function fmt(n: number | null): string {
		if (n === null || n === undefined) return '—';
		return `¥${n.toLocaleString('ja-JP')}`;
	}

	function timeAgo(ts: string): string {
		const t = new Date(ts).getTime();
		if (Number.isNaN(t)) return '';
		const m = Math.max(0, Math.floor((Date.now() - t) / 60000));
		if (m < 60) return `${m}分前`;
		const h = Math.floor(m / 60);
		if (h < 24) return `${h}時間前`;
		return `${Math.floor(h / 24)}日前`;
	}

	function parseRetailers(s: string): Record<string, number> {
		try { return JSON.parse(s) as Record<string, number>; } catch { return {}; }
	}

	$effect(() => {
		if (browser) void load();
	});
</script>

<svelte:head>
	<title>Product Research — yoro</title>
</svelte:head>

<div class="mx-auto max-w-3xl px-4 py-6">
	<header class="mb-6">
		<h1 class="text-2xl font-semibold mb-1">Product Research</h1>
		<p class="text-sm opacity-70">Public-retailer price ingest (Amazon JP / 楽天 / IKEA / FlexiSpot / Yodobashi / Kagu365). Powered by LangGraph yoro_product_ingest.</p>
	</header>

	<section class="mb-6 rounded-2xl border border-white/10 p-4 bg-[var(--gv2-bg-secondary,#161616)]">
		<h2 class="text-sm font-medium mb-3">New ingest run</h2>
		<div class="flex flex-col gap-2">
			<label class="text-xs opacity-70">Query
				<input bind:value={queryInput} class="mt-1 w-full rounded-lg bg-black/40 px-3 py-2 text-sm" placeholder="例: スタンディングデスク" />
			</label>
			<label class="text-xs opacity-70">Category (optional)
				<input bind:value={categoryInput} class="mt-1 w-full rounded-lg bg-black/40 px-3 py-2 text-sm" placeholder="例: office.standing-desk" />
			</label>
			<div class="flex flex-wrap gap-1 text-[10px] opacity-60 mt-1">
				{#each RETAILERS as r}
					<span class="rounded-full border border-white/10 px-2 py-0.5">{r}</span>
				{/each}
			</div>
			<button
				onclick={trigger}
				disabled={triggering || !queryInput.trim()}
				class="mt-2 self-start rounded-full bg-[#1185FE] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
			>
				{triggering ? 'Queuing…' : 'Run ingest'}
			</button>
			{#if lastJobStatus}
				<p class="text-xs opacity-70 mt-1">{lastJobStatus}</p>
			{/if}
		</div>
	</section>

	<section>
		<div class="flex items-center justify-between mb-3">
			<h2 class="text-sm font-medium">Recent runs</h2>
			<button onclick={load} class="text-xs opacity-70 hover:opacity-100">↻ Refresh</button>
		</div>

		{#if loading}
			<div class="flex flex-col gap-2">
				{#each Array(4) as _}
					<Skeleton class="h-20 w-full rounded-xl" />
				{/each}
			</div>
		{:else if items.length === 0}
			<p class="text-sm opacity-60">No research runs yet. Run one above or wait for the daily CronJob.</p>
		{:else}
			<ul class="flex flex-col gap-2">
				{#each items as it (it.vertex_id)}
					{@const byR = parseRetailers(it.offers_by_retailer)}
					<li class="rounded-xl border border-white/10 p-3 bg-[var(--gv2-bg-secondary,#161616)]">
						<div class="flex items-baseline justify-between gap-2">
							<div class="font-medium text-sm truncate">{it.query}</div>
							<div class="text-[11px] opacity-60 shrink-0">{timeAgo(it.created_at)}</div>
						</div>
						{#if it.category}
							<div class="text-[11px] opacity-60 mt-0.5">{it.category}</div>
						{/if}
						<div class="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs">
							<span><b>{it.total_offers}</b> offers</span>
							<span>min {fmt(it.min_price_jpy)}</span>
							<span>median {fmt(it.median_price_jpy)}</span>
							<span>max {fmt(it.max_price_jpy)}</span>
						</div>
						<div class="flex flex-wrap gap-1 mt-2">
							{#each Object.entries(byR).filter(([k]) => !k.startsWith('_')) as [r, n]}
								<span class="rounded-full bg-white/5 px-2 py-0.5 text-[10px]">{r}: {n}</span>
							{/each}
						</div>
					</li>
				{/each}
			</ul>
		{/if}
	</section>
</div>
