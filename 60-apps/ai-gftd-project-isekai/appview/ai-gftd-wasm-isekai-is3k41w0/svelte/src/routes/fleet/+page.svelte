<script lang="ts">
  // Giemon fleet part-graph dashboard. Loads the committed CycloneDX SBOMs
  // (giemon kabitori + otete) and renders a cross-robot part table with
  // filters + a shared-manufacturer view — the browser-side projection of the
  // same data that lives in the kotoba EAVT store.
  import { onMount } from 'svelte';

  type Row = {
    robot: string; id: string; name: string; group: string;
    procurement: string; manufacturer: string; product: string;
    qty: number; unitJpy: number; purl: string;
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
</style>
