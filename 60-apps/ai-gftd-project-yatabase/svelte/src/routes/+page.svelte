<script lang="ts">
	// ── Plan grid (ADR-2605210001 §5 Plan grid) ──────────────────────────────────
	const plans = [
		{
			name: 'Free',
			priceJpy: '¥0',
			priceUsd: '$0',
			period: '/mo',
			highlight: false,
			features: [
				'500K nodes · 2M edges',
				'1 GB graph storage',
				'2 streaming MVs',
				'OWL EL reasoning',
				'5 QCU-hours / mo',
				'MCP 10K calls / mo',
				'Cypher + SPARQL + SQL',
				'Community support',
			],
			cta: 'Get started',
		},
		{
			name: 'Starter',
			priceJpy: '¥1,980',
			priceUsd: '~$13',
			period: '/mo',
			highlight: false,
			features: [
				'5M nodes · 20M edges',
				'10 GB graph storage',
				'10 streaming MVs',
				'OWL EL + RL reasoning',
				'50 QCU-hours / mo',
				'MCP 100K calls / mo',
				'AT Protocol DID auth',
				'Email support 48h',
			],
			cta: 'Get started',
		},
		{
			name: 'Pro',
			priceJpy: '¥4,980',
			priceUsd: '~$33',
			period: '/mo',
			highlight: true,
			features: [
				'50M nodes · 200M edges',
				'100 GB graph storage',
				'50 streaming MVs',
				'OWL EL + RL + QL reasoning',
				'500 QCU-hours / mo',
				'MCP 1M calls / mo',
				'Custom domain',
				'Email support 24h · SLA 99.9%',
			],
			cta: 'Get started',
		},
		{
			name: 'Business',
			priceJpy: '¥98,000',
			priceUsd: '~$650',
			period: '/mo',
			highlight: false,
			features: [
				'500M nodes · 2B edges',
				'1 TB graph storage',
				'500 streaming MVs',
				'OWL EL/RL/QL/DL reasoning',
				'10,000 QCU-hours / mo',
				'MCP 10M calls / mo',
				'SSO / SAML',
				'Priority support 4h · SLA 99.95%',
			],
			cta: 'Get started',
		},
		{
			name: 'Enterprise',
			priceJpy: 'Custom',
			priceUsd: '',
			period: '',
			highlight: false,
			features: [
				'Unlimited nodes & edges',
				'Dedicated RW cluster',
				'Unlimited MVs',
				'Full OWL DL + custom SHACL',
				'Custom QCU allocation',
				'Unlimited MCP calls',
				'White-label option',
				'Dedicated Slack · SLA 99.99%',
			],
			cta: 'Contact us',
		},
	];

	// ── Overage rates (ADR-2605210001 §6) ────────────────────────────────────────
	const overages = [
		{ axis: 'Graph storage', unit: 'GB-month', price: '¥10', note: '33% below Neptune' },
		{ axis: 'Graph compute', unit: 'QCU-hour', price: '¥300', note: 'CPU-time, not I/O count' },
		{ axis: 'MCP tool call', unit: '100 calls', price: '¥3', note: 'included in bundle first' },
		{ axis: 'OWL DL reasoning', unit: '1 run', price: '¥500', note: 'vs Stardog Enterprise' },
		{ axis: 'Egress', unit: 'GB', price: '¥0', note: 'B2 BWA — structurally free' },
	];

	// ── Comparison table (ADR-2605210001 §1 Regret matrix + §10 Moat) ───────────
	const competitors = [
		{
			feature: 'Free tier',
			yatabase: { val: '✓', sub: '500K nodes + MCP' },
			neo4j:    { val: '✓', sub: '200K nodes, no MCP' },
			neptune:  { val: '✗', sub: 'none' },
			tigergraph: { val: '△', sub: 'self-hosted only' },
		},
		{
			feature: 'Production from',
			yatabase: { val: '¥4,980', sub: '~$33/mo' },
			neo4j:    { val: '$65', sub: '/mo' },
			neptune:  { val: '~$200', sub: '/mo (t3.med + I/O + egress)' },
			tigergraph: { val: '~$970', sub: '/mo (16 GB min)' },
		},
		{
			feature: 'Cypher',
			yatabase: { val: '✓', sub: '' },
			neo4j:    { val: '✓', sub: '' },
			neptune:  { val: '△', sub: 'openCypher beta' },
			tigergraph: { val: '✗', sub: 'GSQL only' },
		},
		{
			feature: 'SPARQL 1.1',
			yatabase: { val: '✓', sub: '' },
			neo4j:    { val: '✗', sub: '' },
			neptune:  { val: '✓', sub: '' },
			tigergraph: { val: '✗', sub: '' },
		},
		{
			feature: 'SQL / PG wire',
			yatabase: { val: '✓', sub: '' },
			neo4j:    { val: '✗', sub: '' },
			neptune:  { val: '✗', sub: '' },
			tigergraph: { val: '✗', sub: '' },
		},
		{
			feature: 'OWL reasoning',
			yatabase: { val: '✓', sub: 'EL/RL/QL/DL' },
			neo4j:    { val: '✗', sub: '' },
			neptune:  { val: '✗', sub: '' },
			tigergraph: { val: '✗', sub: '' },
		},
		{
			feature: 'MCP endpoint',
			yatabase: { val: '✓', sub: 'built-in, all plans' },
			neo4j:    { val: '✗', sub: 'DIY connector' },
			neptune:  { val: '✗', sub: 'DIY connector' },
			tigergraph: { val: '✗', sub: 'DIY connector' },
		},
		{
			feature: 'Billing model',
			yatabase: { val: 'CPU-time', sub: 'predictable, no fan-out shock' },
			neo4j:    { val: 'plan bundled', sub: '' },
			neptune:  { val: 'per-I/O', sub: '$0.20/M req — explodes on fan-out' },
			tigergraph: { val: 'instance', sub: '' },
		},
		{
			feature: 'BWA-free egress',
			yatabase: { val: '✓', sub: '$0 via B2 Alliance' },
			neo4j:    { val: '✗', sub: 'charged per GB' },
			neptune:  { val: '✗', sub: '$0.09/GB + amplification' },
			tigergraph: { val: '✗', sub: 'charged per GB' },
		},
		{
			feature: 'Real-time streaming MV',
			yatabase: { val: '✓', sub: 'sub-100ms' },
			neo4j:    { val: '✗', sub: 'static indexes only' },
			neptune:  { val: '✗', sub: '' },
			tigergraph: { val: '△', sub: 'manual incremental' },
		},
	];

	// ── Features (ADR-2605210001 §10 Moats) ──────────────────────────────────────
	const features = [
		{
			icon: `<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 2.625v2.625m0 2.625v2.625M3.75 9v2.625M3.75 14.25v2.625"/></svg>`,
			title: 'Property Graph + RDF',
			desc: 'One engine, two graph models. Store labelled property graphs and RDF triples together — no schema migration when your data model evolves.',
			badge: 'Core',
		},
		{
			icon: `<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M14.25 9.75L16.5 12l-2.25 2.25m-4.5 0L7.5 12l2.25-2.25M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z"/></svg>`,
			title: 'Cypher · SPARQL · SQL',
			desc: 'The only managed graph DB with all three. Neo4j has Cypher, Neptune has SPARQL — yatabase has both plus PostgreSQL-wire SQL. One credential, all languages.',
			badge: 'Moat',
		},
		{
			icon: `<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1 1 .03 2.699-1.382 2.372l-5.466-1.261a2.25 2.25 0 00-1.708 0l-5.466 1.261c-1.413.327-2.382-1.372-1.382-2.372L5 14.5"/></svg>`,
			title: 'MCP Native',
			desc: 'Every tenant ships with a Model Context Protocol endpoint. Connect Claude, Cursor, or any MCP client directly to your graph. No ETL, no custom connector.',
			badge: 'Moat',
		},
		{
			icon: `<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/></svg>`,
			title: 'Real-time Streaming MVs',
			desc: 'Queries hit streaming materialized views — sub-100ms latency on complex traversals without manual cache warming, denormalization, or batch jobs.',
			badge: 'Core',
		},
		{
			icon: `<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 9.563C9 9.252 9.252 9 9.563 9h4.874c.311 0 .563.252.563.563v4.874c0 .311-.252.563-.563.563H9.564A.562.562 0 019 14.437V9.564zM4.5 5.25v.75A.75.75 0 015.25 6h.75m0-1.5h.013c.085 0 .166.03.228.083l.343.343A.75.75 0 006.75 5.25H7.5m0 0v.75m0-.75h.013c.085 0 .167.03.228.083l.344.343A.75.75 0 008.25 5.25H9m0 0v.75m-4.5 9v-.75a.75.75 0 00-.75-.75H3m0 0v-.75m0 .75h-.013a.375.375 0 01-.228-.083l-.343-.343A.75.75 0 002.25 13.5H1.5m0 0V12m0 1.5h-.013a.375.375 0 00-.228.083l-.343.343A.75.75 0 001.5 14.25V15m3-9V4.5m0 1.5h.75m-.75 0V4.5m4.5 0v.75M12 4.5v.75m0-.75h.75M12 6v.75M7.5 4.5v.75m0-.75h.75m-.75 0V4.5"/></svg>`,
			title: 'OWL Reasoning',
			desc: 'EL, RL, QL included in subscription. DL (HermiT) available as on-demand run. The only graph DB BaaS that lets you reason over your ontology without Stardog Enterprise pricing.',
			badge: 'Unique',
		},
		{
			icon: `<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`,
			title: 'CPU-time, not I/O count',
			desc: "Neptune charges $0.20 per million I/O requests — a 10-hop traversal with fan-out multiplies your bill unpredictably. We charge CPU-time: flat, linear, predictable.",
			badge: 'Moat',
		},
	];

	type Cell = { val: string; sub: string };
	function isYes(c: Cell)  { return c.val === '✓'; }
	function isNo(c: Cell)   { return c.val === '✗'; }
</script>

<svelte:head>
	<title>Yatabase — Graph DB BaaS: Cypher · SPARQL · SQL · MCP · OWL</title>
	<meta name="description" content="Managed graph database with Cypher, SPARQL, SQL, native MCP, and OWL reasoning. ¥4,980/mo. 70% cheaper than Neptune. BWA-free egress." />
</svelte:head>

<!-- Nav -->
<nav class="fixed inset-x-0 top-0 z-50 border-b border-gftd-border bg-gftd-bg/80 backdrop-blur-md">
	<div class="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
		<a href="/" class="flex items-center gap-2">
			<span class="text-xl font-bold tracking-tight text-gftd-text">yatabase</span>
			<span class="rounded-full bg-gftd-accent/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-gftd-accent">beta</span>
		</a>
		<div class="flex items-center gap-4">
			<a href="#features" class="hidden text-sm text-gftd-secondary transition-colors hover:text-gftd-text sm:block">Features</a>
			<a href="#compare"  class="hidden text-sm text-gftd-secondary transition-colors hover:text-gftd-text sm:block">Compare</a>
			<a href="#pricing"  class="hidden text-sm text-gftd-secondary transition-colors hover:text-gftd-text sm:block">Pricing</a>
			<a href="/studio"
				class="rounded-lg bg-gftd-accent px-4 py-1.5 text-sm font-medium text-white shadow-sm transition-opacity hover:opacity-90"
			>Open Studio →</a>
		</div>
	</div>
</nav>

<!-- Hero -->
<section class="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6 pt-20 text-center">
	<div class="pointer-events-none absolute inset-0 opacity-[0.03]"
		style="background-image: linear-gradient(var(--gv2-border) 1px, transparent 1px), linear-gradient(90deg, var(--gv2-border) 1px, transparent 1px); background-size: 48px 48px;"></div>
	<div class="pointer-events-none absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-gftd-accent/5 blur-3xl"></div>

	<div class="relative z-10 max-w-3xl">
		<div class="mb-6 inline-flex items-center gap-2 rounded-full border border-gftd-border bg-gftd-card px-4 py-1.5 text-sm text-gftd-secondary">
			<span class="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
			Graph DB BaaS · Cypher · SPARQL · SQL · MCP · OWL
		</div>

		<h1 class="text-5xl font-bold leading-[1.1] tracking-tight text-gftd-text sm:text-6xl">
			The only graph DB<br />
			<span class="text-gftd-accent">your AI agents can query.</span>
		</h1>

		<p class="mx-auto mt-6 max-w-xl text-lg text-gftd-secondary">
			Cypher + SPARQL + SQL in one managed database. Native MCP endpoint.
			OWL reasoning. CPU-time billing — no I/O fan-out shocks.
			¥4,980/mo. 70% cheaper than Neptune.
		</p>

		<div class="mt-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
			<a href="/studio"
				class="rounded-xl bg-gftd-accent px-8 py-3 text-base font-semibold text-white shadow-lg shadow-gftd-accent/20 transition-opacity hover:opacity-90"
			>Get started free</a>
			<a href="#compare"
				class="rounded-xl border border-gftd-border bg-gftd-card px-8 py-3 text-base font-medium text-gftd-text transition-colors hover:border-gftd-accent/40"
			>Compare pricing →</a>
		</div>

		<div class="mt-12 flex flex-wrap justify-center gap-2">
			{#each ['Cypher / GQL', 'SPARQL 1.1', 'PostgreSQL wire', 'MCP JSON-RPC', 'OWL EL/RL/QL/DL', 'BWA $0 egress', 'AT Protocol auth'] as p}
				<span class="rounded-md border border-gftd-border bg-gftd-card px-3 py-1 text-xs text-gftd-muted">{p}</span>
			{/each}
		</div>
	</div>
</section>

<!-- Features -->
<section id="features" class="px-6 py-24">
	<div class="mx-auto max-w-6xl">
		<div class="mb-16 text-center">
			<h2 class="text-3xl font-bold tracking-tight text-gftd-text">Three structural moats. One database.</h2>
			<p class="mt-3 text-gftd-secondary">Multi-language queries, native MCP, and BWA-free egress — advantages competitors cannot structurally replicate.</p>
		</div>
		<div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
			{#each features as f}
				<div class="group relative rounded-2xl border border-gftd-border bg-gftd-card p-6 transition-colors hover:border-gftd-accent/30">
					{#if f.badge === 'Moat'}
						<span class="absolute top-4 right-4 rounded-md bg-gftd-accent/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-gftd-accent">Moat</span>
					{:else if f.badge === 'Unique'}
						<span class="absolute top-4 right-4 rounded-md bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-400">Unique</span>
					{/if}
					<div class="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-gftd-accent/10 text-gftd-accent">
						{@html f.icon}
					</div>
					<h3 class="mb-2 font-semibold text-gftd-text">{f.title}</h3>
					<p class="text-sm leading-relaxed text-gftd-secondary">{f.desc}</p>
				</div>
			{/each}
		</div>
	</div>
</section>

<!-- Protocol strip -->
<section class="border-y border-gftd-border bg-gftd-card px-6 py-20">
	<div class="mx-auto max-w-6xl">
		<div class="grid gap-12 lg:grid-cols-2 lg:items-center">
			<div>
				<h2 class="text-3xl font-bold tracking-tight text-gftd-text">One graph, five wire protocols</h2>
				<p class="mt-4 text-gftd-secondary">
					Your data scientists use SPARQL. Your app uses Cypher.
					Your BI tool uses psql. Your AI agent uses MCP.
					No sync jobs. No replicas. One credential.
				</p>
				<div class="mt-6 rounded-xl border border-gftd-border bg-gftd-bg p-4 font-mono text-xs text-gftd-secondary">
					<div class="text-gftd-muted mb-2"># same graph, different query languages</div>
					<div><span class="text-gftd-accent">MATCH</span> (p:Person)-[:KNOWS]-&gt;(f) <span class="text-gftd-accent">RETURN</span> f.name</div>
					<div class="mt-1"><span class="text-emerald-400">SELECT</span> ?f <span class="text-emerald-400">WHERE</span> &#123; :p :knows ?f &#125;</div>
					<div class="mt-1"><span class="text-blue-400">SELECT</span> * <span class="text-blue-400">FROM</span> vertex_person <span class="text-blue-400">LIMIT</span> 10</div>
				</div>
				<a href="/studio" class="mt-8 inline-block rounded-lg border border-gftd-accent/40 px-6 py-2.5 text-sm font-medium text-gftd-accent transition-colors hover:bg-gftd-accent/5">Open Studio →</a>
			</div>
			<div class="space-y-2">
				{#each [
					{ badge: 'Graph', name: 'Cypher / GQL', desc: 'Neo4j-compatible traversal' },
					{ badge: 'RDF', name: 'SPARQL 1.1', desc: 'W3C-standard triple query' },
					{ badge: 'SQL', name: 'PostgreSQL wire', desc: 'psql / any PG driver' },
					{ badge: 'AT Proto', name: 'XRPC', desc: 'AT Protocol native wire' },
					{ badge: 'AI', name: 'MCP JSON-RPC', desc: 'Model Context Protocol' },
				] as p}
					<div class="flex items-center justify-between rounded-xl border border-gftd-border bg-gftd-bg px-5 py-3">
						<div class="flex items-center gap-3">
							<span class="rounded-md bg-gftd-accent/10 px-2 py-0.5 text-[11px] font-semibold text-gftd-accent">{p.badge}</span>
							<span class="font-medium text-gftd-text">{p.name}</span>
						</div>
						<span class="text-sm text-gftd-muted">{p.desc}</span>
					</div>
				{/each}
			</div>
		</div>
	</div>
</section>

<!-- Comparison -->
<section id="compare" class="px-6 py-24">
	<div class="mx-auto max-w-6xl">
		<div class="mb-12 text-center">
			<h2 class="text-3xl font-bold tracking-tight text-gftd-text">How we compare</h2>
			<p class="mt-3 text-gftd-secondary">Graph DB BaaS pricing as of May 2026. Sources: vendor pricing pages.</p>
		</div>
		<div class="overflow-x-auto">
			<table class="w-full min-w-[680px] border-collapse text-sm">
				<thead>
					<tr class="border-b border-gftd-border">
						<th class="pb-4 text-left font-medium text-gftd-muted w-44"></th>
						<th class="pb-4 text-center">
							<span class="inline-block rounded-lg bg-gftd-accent/10 px-3 py-1 text-sm font-bold text-gftd-accent">yatabase</span>
						</th>
						<th class="pb-4 text-center text-sm font-medium text-gftd-secondary">Neo4j Aura</th>
						<th class="pb-4 text-center text-sm font-medium text-gftd-secondary">Amazon Neptune</th>
						<th class="pb-4 text-center text-sm font-medium text-gftd-secondary">TigerGraph</th>
					</tr>
				</thead>
				<tbody>
					{#each competitors as row, i}
						<tr class="border-b border-gftd-border/50 {i % 2 === 0 ? '' : 'bg-gftd-card/30'}">
							<td class="py-3.5 pr-4 font-medium text-gftd-secondary">{row.feature}</td>
							{#each [row.yatabase, row.neo4j, row.neptune, row.tigergraph] as cell, ci}
								<td class="py-3.5 text-center">
									<span class="{ci === 0 && isYes(cell) ? 'font-semibold text-emerald-400' : ci === 0 ? 'font-semibold text-gftd-text' : isYes(cell) ? 'text-gftd-secondary' : isNo(cell) ? 'text-gftd-muted/60' : 'text-gftd-secondary'}">{cell.val}</span>
									{#if cell.sub}<div class="text-[11px] text-gftd-muted mt-0.5 leading-tight">{cell.sub}</div>{/if}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="mt-5 text-center text-xs text-gftd-muted">
			Neptune: db.t3.medium ($53/mo) + $0.10/GB storage + $0.20/M I/O + $0.09/GB egress. TigerGraph: 16 GB minimum. Prices excl. taxes.
		</p>
	</div>
</section>

<!-- Pricing -->
<section id="pricing" class="border-t border-gftd-border bg-gftd-card px-6 py-24">
	<div class="mx-auto max-w-6xl">
		<div class="mb-16 text-center">
			<h2 class="text-3xl font-bold tracking-tight text-gftd-text">Simple, predictable pricing</h2>
			<p class="mt-3 text-gftd-secondary">CPU-time billing. No I/O charges. No egress fees. No query-count surprises.</p>
		</div>

		<!-- Plan cards — scroll horizontally on mobile -->
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
			{#each plans as plan}
				<div class="relative flex flex-col rounded-2xl border p-6
					{plan.highlight ? 'border-gftd-accent bg-gftd-accent/5' : 'border-gftd-border bg-gftd-bg'}">
					{#if plan.highlight}
						<div class="absolute -top-3 left-1/2 -translate-x-1/2">
							<span class="rounded-full bg-gftd-accent px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-white">Most popular</span>
						</div>
					{/if}
					<div class="mb-5">
						<h3 class="text-xs font-semibold uppercase tracking-wider text-gftd-secondary">{plan.name}</h3>
						<div class="mt-1.5 flex items-baseline gap-1">
							<span class="text-2xl font-bold text-gftd-text">{plan.priceJpy}</span>
							{#if plan.period}<span class="text-xs text-gftd-muted">{plan.period}</span>{/if}
						</div>
						{#if plan.priceUsd}
							<p class="mt-0.5 text-xs text-gftd-muted">{plan.priceUsd}</p>
						{/if}
					</div>
					<ul class="mb-6 flex-1 space-y-2">
						{#each plan.features as feat}
							<li class="flex items-start gap-2 text-xs text-gftd-secondary">
								<svg class="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"/>
								</svg>
								{feat}
							</li>
						{/each}
					</ul>
					<a href="/studio"
						class="block w-full rounded-xl py-2 text-center text-xs font-semibold transition-opacity
						{plan.highlight ? 'bg-gftd-accent text-white hover:opacity-90' : 'border border-gftd-border text-gftd-text hover:border-gftd-accent/40'}"
					>{plan.cta}</a>
				</div>
			{/each}
		</div>

		<!-- Overage rates -->
		<div class="mt-14">
			<h3 class="mb-5 text-center text-sm font-semibold uppercase tracking-wider text-gftd-secondary">Overage rates</h3>
			<div class="mx-auto max-w-2xl overflow-x-auto">
				<table class="w-full text-sm border-collapse">
					<thead>
						<tr class="border-b border-gftd-border text-xs text-gftd-muted">
							<th class="pb-2 text-left font-medium">Axis</th>
							<th class="pb-2 text-left font-medium">Unit</th>
							<th class="pb-2 text-right font-medium">List price</th>
							<th class="pb-2 text-right font-medium pl-6">Note</th>
						</tr>
					</thead>
					<tbody>
						{#each overages as o}
							<tr class="border-b border-gftd-border/40">
								<td class="py-2.5 text-gftd-text font-medium">{o.axis}</td>
								<td class="py-2.5 text-gftd-secondary text-xs">{o.unit}</td>
								<td class="py-2.5 text-right font-semibold {o.price === '¥0' ? 'text-emerald-400' : 'text-gftd-text'}">{o.price}</td>
								<td class="py-2.5 pl-6 text-right text-xs text-gftd-muted">{o.note}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>
</section>

<!-- CTA -->
<section class="border-t border-gftd-border px-6 py-24 text-center">
	<div class="mx-auto max-w-2xl">
		<h2 class="text-3xl font-bold tracking-tight text-gftd-text">Ready to query your graph?</h2>
		<p class="mt-4 text-gftd-secondary">
			Open Studio, create a tenant, and run your first Cypher query in minutes.
			No credit card required on the free plan.
		</p>
		<a href="/studio"
			class="mt-8 inline-block rounded-xl bg-gftd-accent px-10 py-3 text-base font-semibold text-white shadow-lg shadow-gftd-accent/20 transition-opacity hover:opacity-90"
		>Open Studio →</a>
	</div>
</section>

<!-- Footer -->
<footer class="border-t border-gftd-border px-6 py-8">
	<div class="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
		<span class="text-sm font-semibold text-gftd-text">yatabase</span>
		<span class="text-xs text-gftd-muted">© 2026 Gftd Japan株式会社 · <a href="https://yatabase.etzhayyim.com/.well-known/mcp.json" class="hover:text-gftd-text transition-colors">MCP discovery</a></span>
		<div class="flex gap-4">
			<a href="/studio" class="text-xs text-gftd-muted hover:text-gftd-text transition-colors">Studio</a>
			<a href="https://mcp.etzhayyim.com/mcp" class="text-xs text-gftd-muted hover:text-gftd-text transition-colors">MCP</a>
		</div>
	</div>
</footer>
