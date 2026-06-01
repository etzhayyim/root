<script lang="ts">
  // Giemon fleet part-graph dashboard. Loads the committed CycloneDX SBOMs
  // (giemon kabitori + otete) and renders a cross-robot part table with
  // filters + a shared-manufacturer view — the browser-side projection of the
  // same data that lives in the kotoba EAVT store.
  import { onMount } from 'svelte';

  type Row = {
    robot: string; id: string; name: string; group: string;
    procurement: string; manufacturer: string; product: string;
    supplier: string; qty: number; unitJpy: number; purl: string;
  };

  const SBOMS = [
    { url: '/fleet/kabitori.cdx.json' },
    { url: '/fleet/otete.cdx.json' }
  ];

  let rows: Row[] = [];
  let loaded = false;
  let err = '';

  // filters
  let fRobot = 'all';
  let fProc = 'all';
  let q = '';
  let sharedOnly = false;

  const prop = (c: any, n: string) => c.properties?.find((p: any) => p.name === n)?.value ?? '';

  onMount(async () => {
    try {
      const out: Row[] = [];
      for (const s of SBOMS) {
        const doc = await (await fetch(s.url)).json();
        const robot = (doc.metadata?.properties ?? []).find((p: any) => p.name === 'giemon:bomOf')?.value?.replace('giemon-', '') ?? 'robot';
        for (const c of doc.components ?? []) {
          out.push({
            robot,
            id: c['bom-ref'] ?? c.name,
            name: c.name ?? '',
            group: prop(c, 'giemon:group'),
            procurement: prop(c, 'giemon:procurement'),
            manufacturer: c.publisher ?? prop(c, 'giemon:manufacturer'),
            product: c.version ?? prop(c, 'giemon:product'),
            supplier: prop(c, 'giemon:supplier'),
            qty: Number(prop(c, 'giemon:qty') || 1),
            unitJpy: Number(prop(c, 'giemon:unitJpy') || 0),
            purl: c.purl ?? ''
          });
        }
      }
      rows = out;
      loaded = true;
    } catch (e: any) {
      err = e?.message ?? String(e);
    }
  });

  // manufacturer → set of robots (for shared detection)
  $: mfrRobots = rows.reduce((m, r) => {
    if (!r.manufacturer) return m;
    (m[r.manufacturer] ??= new Set()).add(r.robot);
    return m;
  }, {} as Record<string, Set<string>>);
  $: sharedMfrs = Object.entries(mfrRobots).filter(([, s]) => s.size > 1).map(([k]) => k).sort();
  const isShared = (mfr: string) => (mfrRobots[mfr]?.size ?? 0) > 1;

  $: robots = Array.from(new Set(rows.map((r) => r.robot)));
  $: filtered = rows.filter((r) =>
    (fRobot === 'all' || r.robot === fRobot) &&
    (fProc === 'all' || r.procurement === fProc) &&
    (!sharedOnly || isShared(r.manufacturer)) &&
    (q === '' || `${r.name} ${r.manufacturer} ${r.product} ${r.group}`.toLowerCase().includes(q.toLowerCase()))
  );
  $: cots = rows.filter((r) => r.procurement === 'cots').length;
  $: fab = rows.filter((r) => r.procurement === 'custom-fab').length;
  $: totalJpy = rows.reduce((s, r) => s + r.unitJpy * r.qty, 0);
  const yen = (n: number) => (n ? '¥' + n.toLocaleString() : '—');

  // ── supply-risk (task 2) ──────────────────────────────────────────────────
  $: mfrCount = rows.reduce((m, r) => { if (r.manufacturer) m[r.manufacturer] = (m[r.manufacturer] ?? 0) + 1; return m; }, {} as Record<string, number>);
  // sole-use manufacturers: supply exactly 1 fleet part (discontinuation → requalification)
  $: singleSource = Object.entries(mfrCount).filter(([, n]) => n === 1).map(([k]) => k).sort();
  // custom-fab supplier concentration (single fab-house dependency, e.g. Meviy)
  $: fabConc = Object.entries(
      rows.filter((r) => r.procurement === 'custom-fab')
          .reduce((m, r) => { const s = r.supplier || '(unspecified)'; m[s] = (m[s] ?? 0) + 1; return m; }, {} as Record<string, number>)
    ).sort((a, b) => b[1] - a[1]);

  // ── live kotoba SPARQL (task 1, via /api/kotoba proxy) ────────────────────
  let liveQuery = 'SELECT * WHERE { ?s <kg/claim/part/manufacturer> "Raspberry Pi Ltd" }';
  let liveRes: any = null;
  let liveErr = '';
  let liveBusy = false;
  async function runQuery() {
    liveBusy = true; liveErr = ''; liveRes = null;
    try {
      const r = await fetch('/api/kotoba', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: liveQuery }) });
      const txt = await r.text();
      if (!r.ok) liveErr = `${r.status}: ${txt.slice(0, 240)}`;
      else liveRes = JSON.parse(txt);
    } catch (e: any) {
      liveErr = e?.message ?? String(e);
    } finally {
      liveBusy = false;
    }
  }
</script>

<svelte:head><title>Giemon Fleet — part graph</title></svelte:head>

<main>
  <header>
    <h1>Giemon Fleet — part graph</h1>
    <p class="sub">cross-robot SBOM (kabitori + otete) · the browser projection of the kotoba EAVT part ledger</p>
  </header>

  {#if err}<p class="err">load error: {err}</p>{/if}

  {#if loaded}
    <section class="cards">
      <div class="card"><b>{rows.length}</b><span>parts</span></div>
      <div class="card"><b>{robots.length}</b><span>robots</span></div>
      <div class="card"><b>{cots}</b><span>off-the-shelf</span></div>
      <div class="card"><b>{fab}</b><span>custom-fab</span></div>
      <div class="card"><b>{Object.keys(mfrRobots).length}</b><span>manufacturers</span></div>
      <div class="card hl"><b>{sharedMfrs.length}</b><span>shared across robots</span></div>
      <div class="card"><b>{yen(totalJpy)}</b><span>spec cost (otete)</span></div>
    </section>

    <section class="shared">
      <span class="lbl">shared manufacturers:</span>
      {#each sharedMfrs as m}<span class="chip">{m}</span>{/each}
    </section>

    <section class="risk">
      <h2>supply risk</h2>
      <div class="risk-grid">
        <div>
          <div class="rh">custom-fab supplier concentration</div>
          {#each fabConc as [s, n]}
            <div class="bar"><span class="bn">{s}</span><span class="bv" class:hot={n >= 3}>{n}</span></div>
          {/each}
        </div>
        <div>
          <div class="rh">single-source manufacturers <span class="muted">({singleSource.length} — sole-use, requalification risk)</span></div>
          <div class="ss">{#each singleSource as m}<span class="chip dim">{m}</span>{/each}</div>
        </div>
      </div>
      <p class="muted note">Only robots with a structured BOM are in the graph (kabitori + Giemon Otete); other Tier-B actors have no part list to ingest yet.</p>
    </section>

    <section class="live">
      <h2>live kotoba query <span class="muted">(SPARQL → /api/kotoba → kotoba EAVT)</span></h2>
      <textarea bind:value={liveQuery} rows="2" spellcheck="false"></textarea>
      <div class="live-row">
        <button on:click={runQuery} disabled={liveBusy}>{liveBusy ? 'running…' : 'Run'}</button>
        {#if liveRes}<span class="muted">{liveRes.count} rows · {liveRes.elapsedMs}ms</span>{/if}
        {#if liveErr}<span class="err">{liveErr}</span>{/if}
      </div>
      {#if liveRes?.quads?.length}
        <table class="live-tbl">
          <thead><tr><th>subject</th><th>predicate</th><th>object</th></tr></thead>
          <tbody>
            {#each liveRes.quads.slice(0, 50) as q}
              <tr><td class="mono">{q.subject?.slice(0, 16)}…</td><td class="muted">{q.predicate}</td><td>{q.object?.text ?? ''}</td></tr>
            {/each}
          </tbody>
        </table>
      {/if}
      <p class="muted note">Needs a running <code>kotoba serve</code> and the dev server started with <code>KOTOBA_TOKEN</code> set.</p>
    </section>

    <section class="controls">
      <select bind:value={fRobot}>
        <option value="all">all robots</option>
        {#each robots as r}<option value={r}>{r}</option>{/each}
      </select>
      <select bind:value={fProc}>
        <option value="all">all procurement</option>
        <option value="cots">cots</option>
        <option value="custom-fab">custom-fab</option>
      </select>
      <label class="tog"><input type="checkbox" bind:checked={sharedOnly} /> shared-mfr only</label>
      <input class="search" placeholder="search name / manufacturer / product…" bind:value={q} />
      <span class="count">{filtered.length} shown</span>
    </section>

    <table>
      <thead>
        <tr><th>robot</th><th>part</th><th>group</th><th>proc</th><th>manufacturer</th><th>product</th><th>qty</th><th>unit</th></tr>
      </thead>
      <tbody>
        {#each filtered as r}
          <tr>
            <td><span class="robot {r.robot}">{r.robot}</span></td>
            <td>{r.name}</td>
            <td class="muted">{r.group}</td>
            <td><span class="proc {r.procurement}">{r.procurement}</span></td>
            <td class:shared={isShared(r.manufacturer)}>{r.manufacturer || '—'}</td>
            <td class="muted">{r.product}</td>
            <td class="num">{r.qty}</td>
            <td class="num">{yen(r.unitJpy)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {:else if !err}
    <p class="muted">loading SBOMs…</p>
  {/if}
</main>

<style>
  :global(body) { margin: 0; background: #0d0f12; color: #e6e8ea; font: 14px/1.5 -apple-system, Segoe UI, Roboto, sans-serif; }
  main { max-width: 1100px; margin: 0 auto; padding: 24px 18px 64px; }
  h1 { margin: 0; font-size: 22px; }
  .sub { color: #9aa3ad; margin: 4px 0 16px; }
  .err { color: #ff6b6b; }
  .cards { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; }
  .card { background: #161b22; border: 1px solid #2a2f37; border-radius: 12px; padding: 10px 14px; min-width: 92px; }
  .card b { display: block; font-size: 20px; }
  .card span { color: #9aa3ad; font-size: 12px; }
  .card.hl { border-color: #ffd23f; }
  .shared { margin-bottom: 14px; }
  .shared .lbl { color: #9aa3ad; margin-right: 8px; }
  .chip { display: inline-block; background: #20262e; border: 1px solid #ffd23f55; border-radius: 999px; padding: 2px 10px; margin: 2px; font-size: 12px; }
  .controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; }
  select, .search, .tog { background: #161b22; border: 1px solid #2a2f37; color: #e6e8ea; border-radius: 8px; padding: 6px 10px; }
  .search { flex: 1; min-width: 200px; }
  .tog { display: flex; gap: 6px; align-items: center; }
  .count { color: #9aa3ad; font-size: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #20262e; }
  th { color: #9aa3ad; font-weight: 600; position: sticky; top: 0; background: #0d0f12; }
  .muted { color: #9aa3ad; }
  .num { text-align: right; font-variant-numeric: tabular-nums; }
  td.shared { color: #ffd23f; font-weight: 600; }
  .robot { border-radius: 6px; padding: 1px 7px; font-size: 12px; }
  .robot.kabitori { background: #1d3a2e; color: #5fd38a; }
  .robot.otete { background: #2a2540; color: #b69cff; }
  .proc { border-radius: 6px; padding: 1px 7px; font-size: 11px; }
  .proc.cots { background: #233040; color: #6fb3ff; }
  .proc.custom-fab { background: #3a2a1d; color: #ffb169; }
  h2 { font-size: 15px; margin: 18px 0 8px; }
  .risk, .live { background: #12161c; border: 1px solid #20262e; border-radius: 12px; padding: 12px 14px; margin-bottom: 14px; }
  .risk-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
  @media (max-width: 720px) { .risk-grid { grid-template-columns: 1fr; } }
  .rh { color: #9aa3ad; font-size: 12px; margin-bottom: 6px; }
  .bar { display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #1b2026; }
  .bn { font-size: 13px; }
  .bv { font-variant-numeric: tabular-nums; color: #6fb3ff; }
  .bv.hot { color: #ffb169; font-weight: 700; }
  .ss { display: flex; flex-wrap: wrap; gap: 4px; }
  .chip.dim { border-color: #2a2f37; color: #9aa3ad; }
  .note { font-size: 11px; margin: 8px 0 0; }
  textarea { width: 100%; box-sizing: border-box; background: #0d0f12; color: #e6e8ea; border: 1px solid #2a2f37; border-radius: 8px; padding: 8px; font-family: ui-monospace, Menlo, monospace; font-size: 12px; }
  .live-row { display: flex; gap: 10px; align-items: center; margin: 8px 0; }
  .live-row button { background: #ffd23f; color: #1a1d22; border: 0; border-radius: 8px; padding: 6px 16px; font-weight: 700; cursor: pointer; }
  .live-row button:disabled { opacity: 0.5; cursor: default; }
  .live-tbl { font-size: 12px; }
  .mono { font-family: ui-monospace, Menlo, monospace; color: #9aa3ad; }
  code { background: #20262e; border-radius: 4px; padding: 1px 5px; font-size: 11px; }
</style>
