<script lang="ts">
	import { onMount } from 'svelte';
	import { Button, Textarea, NotificationBanner, EmptyState } from '@gftdcojp/design-system';
	import { apiKey } from '$lib/stores';
	import { graph, ApiError, type CypherResp } from '$lib/api';

	const HISTORY_KEY = 'yatabase-studio:cypher:history';
	const SAMPLES = [
		`CREATE (n:Thing {name: 'hello', created_at: '${new Date().toISOString()}'})\nRETURN n`,
		`MATCH (n:Thing) RETURN n.name, n.created_at LIMIT 25`,
		`MATCH (a:Person)-[:KNOWS]->(b:Person) RETURN a.name, b.name LIMIT 10`,
	];

	let query = $state(`MATCH (n:Thing) RETURN n.name LIMIT 25`);
	let running = $state(false);
	let resp = $state<CypherResp | null>(null);
	let error = $state('');
	let history = $state<string[]>([]);

	onMount(() => {
		try {
			history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
		} catch {
			history = [];
		}
	});

	async function run() {
		running = true;
		error = '';
		resp = null;
		try {
			const r = await graph.cypher($apiKey, query);
			resp = r;
			history = [query, ...history.filter((q) => q !== query)].slice(0, 20);
			localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		} finally {
			running = false;
		}
	}

	function loadSample(s: string) {
		query = s;
	}

	function loadHistory(q: string) {
		query = q;
	}

	function clearHistory() {
		history = [];
		localStorage.removeItem(HISTORY_KEY);
	}

	const columns = $derived(
		resp?.rows && resp.rows.length > 0 ? Object.keys(resp.rows[0]) : [],
	);
</script>

<div class="mx-auto w-full max-w-6xl space-y-6 px-6 py-10">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-semibold text-gftd-text">Cypher editor</h1>
			<p class="mt-1 text-sm text-gftd-secondary">
				POSTs to <code class="font-mono">/cypher</code> with your API key. Use Ctrl/⌘+Enter to
				run.
			</p>
		</div>
		<Button size="md" variant="solid-fill" onclick={run} aria-disabled={running || !query.trim()}>
			{running ? 'Running…' : 'Run query'}
		</Button>
	</div>

	<div class="grid gap-4 lg:grid-cols-[1fr_280px]">
		<!-- Editor + result -->
		<div class="space-y-4">
			<div class="rounded-xl border border-gftd-border bg-gftd-card">
				<Textarea
					blockSize="lg"
					rows={10}
					placeholder="MATCH (n) RETURN n LIMIT 25"
					bind:value={query}
					class="code !rounded-xl !border-0 !bg-transparent font-mono text-sm"
					onkeydown={(e) => {
						if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
							e.preventDefault();
							void run();
						}
					}}
				/>
			</div>

			{#if error}
				<NotificationBanner type="error">
					<span class="font-mono text-xs">{error}</span>
				</NotificationBanner>
			{/if}

			{#if resp}
				<div class="rounded-xl border border-gftd-border bg-gftd-card">
					<div
						class="flex items-center justify-between border-b border-gftd-border px-4 py-2 text-xs text-gftd-muted"
					>
						<span>
							{resp.row_count ?? resp.rows?.length ?? 0} row(s)
							{resp.took_ms ? `· ${resp.took_ms}ms` : ''}
							{resp.source ? `· source=${resp.source}` : ''}
						</span>
						{#if resp.accepted}
							<span class="rounded bg-emerald-900/40 px-2 py-0.5 text-emerald-200">accepted</span>
						{/if}
					</div>

					{#if !resp.rows || resp.rows.length === 0}
						<div class="px-6 py-10">
							<EmptyState
								title="No rows returned"
								description="The query ran but returned an empty result set."
							/>
						</div>
					{:else}
						<div class="overflow-x-auto">
							<table class="w-full border-collapse text-sm">
								<thead>
									<tr class="border-b border-gftd-border bg-black/20 text-left text-gftd-muted">
										{#each columns as col}
											<th class="px-4 py-2 font-medium">{col}</th>
										{/each}
									</tr>
								</thead>
								<tbody>
									{#each resp.rows as row, i (i)}
										<tr class="border-b border-gftd-border/60 last:border-0">
											{#each columns as col}
												<td class="px-4 py-2 font-mono text-xs text-gftd-text">
													{typeof row[col] === 'object'
														? JSON.stringify(row[col])
														: String(row[col] ?? '')}
												</td>
											{/each}
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Sidebar: samples + history -->
		<aside class="space-y-4 lg:sticky lg:top-6">
			<div class="rounded-xl border border-gftd-border bg-gftd-card p-4">
				<h2 class="text-sm font-medium text-gftd-secondary">Samples</h2>
				<ul class="mt-3 space-y-1 text-xs">
					{#each SAMPLES as s, i}
						<li>
							<button
								class="w-full rounded-md px-2 py-1.5 text-left font-mono text-gftd-text hover:bg-white/5"
								onclick={() => loadSample(s)}
								type="button"
							>
								{i === 0 ? 'CREATE node' : i === 1 ? 'MATCH 25' : 'MATCH relation'}
							</button>
						</li>
					{/each}
				</ul>
			</div>

			<div class="rounded-xl border border-gftd-border bg-gftd-card p-4">
				<div class="flex items-center justify-between">
					<h2 class="text-sm font-medium text-gftd-secondary">History</h2>
					{#if history.length > 0}
						<button
							class="text-xs text-gftd-muted hover:text-gftd-text"
							onclick={clearHistory}
							type="button">clear</button
						>
					{/if}
				</div>
				{#if history.length === 0}
					<p class="mt-2 text-xs text-gftd-muted">No queries yet.</p>
				{:else}
					<ul class="mt-3 space-y-1 text-xs">
						{#each history as q, i (i + q)}
							<li>
								<button
									class="block w-full truncate rounded-md px-2 py-1 text-left font-mono text-gftd-secondary hover:bg-white/5 hover:text-gftd-text"
									onclick={() => loadHistory(q)}
									title={q}
									type="button"
								>
									{q.slice(0, 60)}
								</button>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		</aside>
	</div>
</div>
