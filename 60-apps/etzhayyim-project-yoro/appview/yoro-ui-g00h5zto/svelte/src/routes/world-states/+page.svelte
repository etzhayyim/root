<script lang="ts">
	import { onMount } from 'svelte';

	type State = { iso: string; name: string; region: string; graphStatus: 'live' | 'pending'; indexedAt?: string };
	let states = $state<State[]>([]);
	let loading = $state(true);
	let error = $state('');
	let filter = $state<'all' | 'live' | 'pending'>('all');
	let search = $state('');

	async function load() {
		try {
			// Query graph for all stateProfile rkeys under states.etzhayyim.com repo.
			// /api/kagami/query is public (read-only, no auth).
			const sql = `SELECT rkey, value_json, indexed_at
			             FROM vertex_state_profile
			             WHERE repo = 'states.etzhayyim.com'
			             ORDER BY rkey`;
			const r = await fetch('https://atproto.etzhayyim.com/api/kagami/query', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ sql }),
			});
			const d = await r.json();
			const live: Record<string, { iso: string; name: string; region: string; indexedAt: string }> = {};
			for (const row of (d as any)?.rows?.rows ?? []) {
				try {
					const v = JSON.parse(row.value_json);
					if (!v.iso3) continue;
					live[v.iso3] = {
						iso: v.iso3,
						name: v.name || v.iso3,
						region: v.region || '',
						indexedAt: row.indexed_at,
					};
				} catch {}
			}
			// Merge with the canonical 199-country ISO list (hardcoded to match seed_domains)
			const ALL_ISO = [
				"jpn","chn","kor","prk","mng","idn","tha","sgp","mys","phl","vnm","mmr","khm","lao","brn","tls",
				"ind","pak","bgd","lka","npl","btn","mdv","afg","kaz","uzb","tkm","kgz","tjk",
				"tur","sau","are","isr","irn","irq","jor","lbn","syr","yem","omn","kwt","qat","bhr","pse","cyp",
				"geo","arm","aze","gbr","fra","deu","che","nld","bel","aut","irl","lux","mco","lie","and",
				"swe","nor","fin","dnk","isl","est","lva","ltu","ita","esp","prt","grc","hrv","svn","mlt","smr","vat","mne","mkd",
				"pol","rou","hun","cze","svk","ukr","blr","bgr","srb","bih","alb","rus","usa","can","mex",
				"gtm","hnd","slv","nic","cri","pan","blz","cub","dom","hti","jam","bhs","brb","atg","dma","grd","lca","vct","kna","tto",
				"bra","arg","col","chl","per","ven","ecu","bol","pry","ury","guy","sur","aus","nzl","fji","png","slb","vut","wsm","ton","kir","fsm","mhl","plw","tuv","nru",
				"egy","dza","mar","tun","lby","sdn","ssd","nga","gha","civ","sen","mli","bfa","ner","gin","sle","lbr","tgo","ben","gmb","gnb","cpv","mrt",
				"ken","eth","tza","uga","rwa","bdi","som","eri","dji","com","syc","cod","cog","cmr","gab","gnq","caf","tcd","stp",
				"zaf","ago","moz","zmb","zwe","bwa","nam","mwi","lso","swz","mdg","twn","xkx"
			];
			states = ALL_ISO.map(iso => {
				const l = live[iso];
				if (l) return { ...l, graphStatus: 'live' as const };
				return { iso, name: iso.toUpperCase(), region: '', graphStatus: 'pending' as const };
			});
		} catch (e: any) {
			error = e?.message ?? String(e);
		} finally {
			loading = false;
		}
	}

	const filtered = $derived(states.filter(s => {
		if (filter === 'live' && s.graphStatus !== 'live') return false;
		if (filter === 'pending' && s.graphStatus !== 'pending') return false;
		if (search && !s.iso.includes(search.toLowerCase()) && !s.name.toLowerCase().includes(search.toLowerCase())) return false;
		return true;
	}));
	const liveCount = $derived(states.filter(s => s.graphStatus === 'live').length);

	onMount(() => { void load(); });
</script>

<svelte:head>
	<title>World States — {liveCount} / {states.length} — YORO</title>
</svelte:head>

<div class="min-h-screen bg-gv2-bg-primary text-gv2-text-primary">
	<header class="sticky top-0 z-10 border-b border-gv2-border/30 bg-gv2-bg-primary/95 backdrop-blur px-4 py-3">
		<h1 class="text-[16px] font-semibold">World State Profiles</h1>
		<p class="text-[12px] text-gv2-text-muted mt-0.5">
			{liveCount} / {states.length} countries in graph ({((liveCount / Math.max(states.length, 1)) * 100).toFixed(0)}%)
		</p>
		<div class="mt-2 flex items-center gap-2">
			<input
				type="text"
				bind:value={search}
				placeholder="Search iso3 / name"
				class="flex-1 rounded-md border border-gv2-border/30 bg-gv2-bg-secondary px-2 py-1 text-[13px] text-gv2-text-primary placeholder:text-gv2-text-muted"
			/>
			{#each [['all', 'All'], ['live', 'Live'], ['pending', 'Pending']] as [v, label]}
				<button
					class="rounded-md px-2 py-1 text-[12px] border border-gv2-border/30 {filter === v ? 'bg-blue-500 text-white border-blue-500' : 'text-gv2-text-muted hover:text-gv2-text-primary'}"
					onclick={() => (filter = v as typeof filter)}
				>
					{label}
				</button>
			{/each}
		</div>
	</header>

	{#if loading}
		<div class="p-4 text-gv2-text-muted text-[13px]">Loading…</div>
	{:else if error}
		<div class="p-4 text-red-500 text-[13px]">Error: {error}</div>
	{:else}
		<div class="p-3 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
			{#each filtered as s}
				<a
					href={`/profile/did:web:states.etzhayyim.com:state:${s.iso}`}
					class="rounded-lg border border-gv2-border/30 p-2.5 hover:bg-gv2-bg-secondary/50 transition-colors block"
				>
					<div class="flex items-start justify-between gap-1">
						<span class="text-[11px] font-mono text-gv2-text-muted uppercase">{s.iso}</span>
						{#if s.graphStatus === 'live'}
							<span class="inline-block h-2 w-2 rounded-full bg-emerald-500" title="live in graph"></span>
						{:else}
							<span class="inline-block h-2 w-2 rounded-full bg-gv2-text-muted/30" title="pending graph ingest"></span>
						{/if}
					</div>
					<div class="text-[13px] font-semibold text-gv2-text-primary mt-1 truncate">{s.name}</div>
					{#if s.region}
						<div class="text-[10px] text-gv2-text-muted mt-0.5 truncate">{s.region.replace(/_/g, ' ')}</div>
					{/if}
				</a>
			{/each}
		</div>
	{/if}
</div>
