<script lang="ts">
	/**
	 * Resource Flow tab — ADR-0035 reverse-topology actor money-flow visualization.
	 *
	 * For any actor DID, render incoming flows (受け取り) / outgoing flows (支払) /
	 * UBO chain (実質的支配者) read from the kotoba Datom log.
	 *
	 * Data path (kagami-free, ADR-2605262130 / 2605312345): getResourceFlow →
	 * `com.etzhayyim.yoro.fiscal.getResourceFlow` → kotoba-sw.js assembles the view
	 * ENTIRELY in the browser from `:yoro.fiscal/*` + `:yoro.ownership/*` datoms in
	 * the in-page kotoba Datom log (the first-class canonical state). The deprecated
	 * kagami SQL path (`$lib/graph-sql` → RisingWave) has been pruned.
	 *
	 * AS-OF (point-in-time / 過去の記録): the Datom log is append-only, so a past
	 * fact is never overwritten. The as-of control filters to facts observed at or
	 * before the selected day — real time-travel over the canonical log. (This is
	 * the observed-dimension as-of carried on each datom; the transaction-time
	 * basis-t-CID as-of — `com.etzhayyim.apps.kotoba.datomic.asOf` — swaps in at the
	 * SW layer once the wasm node exposes an as-of root, with no UI change.)
	 *
	 * Empty state shows ADR-0035 explanation so non-fiscal actors still get
	 * meaningful context (every actor can appear in the fiscal log once ingest
	 * catches up; today the published blocks carry no `:yoro.fiscal/*` datoms yet).
	 */
	import { getResourceFlow, type FlowRow, type OwnershipRow } from '$lib/kotoba/fiscal';

	interface Props {
		did?: string;
	}
	const { did }: Props = $props();

	let incoming = $state<FlowRow[]>([]);
	let outgoing = $state<FlowRow[]>([]);
	let uboParents = $state<OwnershipRow[]>([]);
	let uboChildren = $state<OwnershipRow[]>([]);
	let totalIn = $state(0);
	let totalOut = $state(0);
	let loading = $state(false);
	let loaded = $state(false);
	let error = $state<string | null>(null);

	// AS-OF point-in-time. null = current (latest known). 'YYYY-MM-DD' = as-of that day.
	let asOf = $state<string | null>(null);
	// Monotonic token guards against out-of-order responses when asOf changes rapidly.
	let loadToken = 0;

	async function load() {
		if (!did) return;
		const token = ++loadToken;
		loading = true;
		error = null;
		try {
			const flow = await getResourceFlow(did, asOf);
			if (token !== loadToken) return; // a newer as-of request superseded this one
			incoming = flow.incoming;
			outgoing = flow.outgoing;
			uboParents = flow.uboParents;
			uboChildren = flow.uboChildren;
			totalIn = flow.totalIn;
			totalOut = flow.totalOut;
		} catch (e: any) {
			if (token !== loadToken) return;
			error = String(e?.message ?? e);
		} finally {
			if (token === loadToken) {
				loading = false;
				loaded = true;
			}
		}
	}

	// Re-run whenever the actor or the as-of point changes.
	$effect(() => {
		void did;
		void asOf;
		void load();
	});

	const today = new Date().toISOString().slice(0, 10);

	function setAsOf(v: string) {
		asOf = v || null;
	}
	function clearAsOf() {
		asOf = null;
	}

	function formatJpy(n: number | null): string {
		if (n == null) return '—';
		if (n >= 1e12) return `${(n / 1e12).toFixed(2)} 兆円`;
		if (n >= 1e8) return `${(n / 1e8).toFixed(2)} 億円`;
		if (n >= 1e4) return `${(n / 1e4).toFixed(1)} 万円`;
		return `${n.toLocaleString()} 円`;
	}

	function shortDid(d: string): string {
		if (!d) return '';
		if (d.length <= 48) return d;
		return d.slice(0, 22) + '…' + d.slice(-22);
	}

	const stageLabel: Record<string, string> = {
		L0: 'L0 受給者', L1: 'L1 契約', L2: 'L2 執行課', L3: 'L3 独法',
		L4: 'L4 自治体', L5: 'L5 省庁', L6: 'L6 横串', L7: 'L7 国庫',
	};
</script>

<div class="flex flex-col gap-4">
	{#if did}
		<!-- AS-OF time-travel control (observed_at fact-time over the kotoba log) -->
		<div class="flex flex-wrap items-center gap-2 rounded-2xl border border-gv2-border/30 bg-gv2-bg-hover/20 px-3 py-2">
			<span class="text-[11px] font-semibold uppercase tracking-wide text-gv2-text-muted">As-of 時点</span>
			<input
				type="date"
				max={today}
				value={asOf ?? ''}
				oninput={(e) => setAsOf((e.currentTarget as HTMLInputElement).value)}
				class="rounded-lg border border-gv2-border/40 bg-gv2-bg-primary/60 px-2 py-1 text-[12px] text-gv2-text-primary"
				aria-label="As-of 日付を選択"
			/>
			{#if asOf}
				<button
					type="button"
					onclick={clearAsOf}
					class="rounded-lg border border-gv2-border/40 bg-gv2-bg-primary/40 px-2 py-1 text-[11px] text-gv2-text-muted hover:text-gv2-text-primary"
				>
					⟲ 現在に戻す
				</button>
				<span class="text-[11px] text-amber-300">
					🕐 {asOf} 時点で記録されていた資金フロー
				</span>
			{:else}
				<span class="text-[11px] text-gv2-text-muted">現在(最新の記録)</span>
			{/if}
			{#if loading && loaded}
				<span class="text-[11px] text-gv2-text-muted">…更新中</span>
			{/if}
		</div>
	{/if}

	{#if !did}
		<div class="rounded-2xl bg-gv2-bg-hover/30 px-4 py-6 text-center text-[13px] text-gv2-text-muted">
			DID 不明 — Resource Flow を表示できません
		</div>
	{:else if loading && !loaded}
		<div class="flex flex-col gap-2 px-4 py-6">
			<div class="h-4 w-32 animate-pulse rounded bg-gv2-bg-hover"></div>
			<div class="h-12 w-full animate-pulse rounded-xl bg-gv2-bg-hover"></div>
			<div class="h-12 w-full animate-pulse rounded-xl bg-gv2-bg-hover"></div>
		</div>
	{:else if error}
		<div class="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-[13px] text-red-300">
			Resource Flow 取得失敗: {error}
		</div>
	{:else if incoming.length === 0 && outgoing.length === 0 && uboParents.length === 0 && uboChildren.length === 0}
		<div class="rounded-2xl bg-gv2-bg-hover/30 px-4 py-8 text-center">
			<div class="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/10 text-[28px]">💴</div>
			<p class="mb-1 text-[15px] font-bold text-gv2-text-primary">Resource Flow データなし</p>
			<p class="text-[12px] text-gv2-text-muted leading-relaxed">
				{#if asOf}
					{asOf} 時点では、このアクターに公開資金フロー (税金 / 契約 / 補助金 / UBO) が記録されていません。
				{:else}
					このアクターには公開資金フロー (税金 / 契約 / 補助金 / UBO) が紐付いていません。
				{/if}
			</p>
			<p class="mt-2 text-[11px] text-gv2-text-muted">kotoba Datom log に `:yoro.fiscal/*` が ingest 済みになると自動表示されます。</p>
		</div>
	{:else}
		<!-- Summary -->
		<div class="grid grid-cols-2 gap-2">
			<div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3">
				<p class="text-[11px] font-semibold uppercase tracking-wide text-emerald-400/80">受け取り合計</p>
				<p class="mt-1 text-[18px] font-bold text-gv2-text-primary">{formatJpy(totalIn)}</p>
				<p class="text-[11px] text-gv2-text-muted">{incoming.length} 件</p>
			</div>
			<div class="rounded-2xl border border-rose-500/20 bg-rose-500/5 px-4 py-3">
				<p class="text-[11px] font-semibold uppercase tracking-wide text-rose-400/80">支払合計</p>
				<p class="mt-1 text-[18px] font-bold text-gv2-text-primary">{formatJpy(totalOut)}</p>
				<p class="text-[11px] text-gv2-text-muted">{outgoing.length} 件</p>
			</div>
		</div>

		<!-- Incoming -->
		{#if incoming.length > 0}
			<section class="rounded-2xl border border-gv2-border/30 bg-gv2-bg-hover/20 p-3">
				<h3 class="mb-2 text-[13px] font-bold text-gv2-text-primary">⬇ 受け取り (incoming)</h3>
				<ul class="flex flex-col gap-1.5">
					{#each incoming as f}
						<li class="rounded-lg border border-gv2-border/30 bg-gv2-bg-primary/40 px-3 py-2">
							<div class="flex items-center justify-between gap-2">
								<span class="text-[11px] font-mono text-emerald-400">{stageLabel[f.stage] ?? f.stage}</span>
								<span class="text-[14px] font-bold text-gv2-text-primary">{formatJpy(f.amount_jpy)}</span>
							</div>
							<p class="mt-1 text-[11px] text-gv2-text-muted">from {shortDid(f.from_did)}</p>
							{#if f.basis || f.program_code || f.fiscal_year}
								<p class="mt-0.5 text-[11px] text-gv2-text-muted">
									{#if f.fiscal_year}FY{f.fiscal_year} {/if}{f.basis ?? ''} {f.program_code ?? ''}
								</p>
							{/if}
							{#if f.source_url}
								<a href={f.source_url} target="_blank" rel="noopener noreferrer" class="mt-1 inline-block text-[11px] text-blue-400 hover:underline">出典 ↗</a>
							{/if}
						</li>
					{/each}
				</ul>
			</section>
		{/if}

		<!-- Outgoing -->
		{#if outgoing.length > 0}
			<section class="rounded-2xl border border-gv2-border/30 bg-gv2-bg-hover/20 p-3">
				<h3 class="mb-2 text-[13px] font-bold text-gv2-text-primary">⬆ 支払 (outgoing)</h3>
				<ul class="flex flex-col gap-1.5">
					{#each outgoing as f}
						<li class="rounded-lg border border-gv2-border/30 bg-gv2-bg-primary/40 px-3 py-2">
							<div class="flex items-center justify-between gap-2">
								<span class="text-[11px] font-mono text-rose-400">{stageLabel[f.stage] ?? f.stage}</span>
								<span class="text-[14px] font-bold text-gv2-text-primary">{formatJpy(f.amount_jpy)}</span>
							</div>
							<p class="mt-1 text-[11px] text-gv2-text-muted">to {shortDid(f.to_did)}</p>
							{#if f.basis || f.program_code || f.fiscal_year}
								<p class="mt-0.5 text-[11px] text-gv2-text-muted">
									{#if f.fiscal_year}FY{f.fiscal_year} {/if}{f.basis ?? ''} {f.program_code ?? ''}
								</p>
							{/if}
							{#if f.source_url}
								<a href={f.source_url} target="_blank" rel="noopener noreferrer" class="mt-1 inline-block text-[11px] text-blue-400 hover:underline">出典 ↗</a>
							{/if}
						</li>
					{/each}
				</ul>
			</section>
		{/if}

		<!-- UBO -->
		{#if uboParents.length > 0 || uboChildren.length > 0}
			<section class="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-3">
				<h3 class="mb-2 text-[13px] font-bold text-gv2-text-primary">🔎 UBO 実質的支配者</h3>
				{#if uboParents.length > 0}
					<p class="mb-1 text-[11px] font-semibold text-amber-400/80">親 (このアクターを支配)</p>
					<ul class="mb-2 flex flex-col gap-1">
						{#each uboParents as o}
							<li class="rounded-lg bg-gv2-bg-primary/40 px-3 py-1.5 text-[12px] text-gv2-text-primary">
								<span class="font-mono text-amber-300">{o.ownership_pct?.toFixed(1)}%</span>
								&nbsp;←&nbsp;{shortDid(o.parent_did)}
								{#if o.evidence_kind}<span class="ml-1 text-[10px] text-gv2-text-muted">({o.evidence_kind})</span>{/if}
							</li>
						{/each}
					</ul>
				{/if}
				{#if uboChildren.length > 0}
					<p class="mb-1 text-[11px] font-semibold text-amber-400/80">子 (このアクターが支配)</p>
					<ul class="flex flex-col gap-1">
						{#each uboChildren as o}
							<li class="rounded-lg bg-gv2-bg-primary/40 px-3 py-1.5 text-[12px] text-gv2-text-primary">
								<span class="font-mono text-amber-300">{o.ownership_pct?.toFixed(1)}%</span>
								&nbsp;→&nbsp;{shortDid(o.child_did)}
								{#if o.evidence_kind}<span class="ml-1 text-[10px] text-gv2-text-muted">({o.evidence_kind})</span>{/if}
							</li>
						{/each}
					</ul>
				{/if}
			</section>
		{/if}

		<p class="text-center text-[10px] text-gv2-text-muted">
			出典: ADR-0035 reverse-topology / kotoba Datom log `:yoro.fiscal/*` + `:yoro.ownership/*`
			{#if asOf}· as-of {asOf} (observed){/if}
		</p>
	{/if}
</div>
