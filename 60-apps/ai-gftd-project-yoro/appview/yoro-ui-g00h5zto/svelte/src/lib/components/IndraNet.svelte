<script lang="ts">
  /*
   * IndraNet — Karma Hegemon edge graph visualization.
   *
   * Shows the karma dependency graph for the viewer's DID:
   *   - vertices = organism DIDs (current viewer + 1-hop neighbors)
   *   - edges    = edge_karma_dependency rows (axis color, dashed=harm)
   *
   * Pure read path — consumes existing XRPCs:
   *   ai.gftd.apps.karma.coverage    — ecosystem stats banner
   *   ai.gftd.apps.karma.listEdges   — viewer-scoped edges
   *   ai.gftd.apps.karma.wbtBalance  — side-panel balance lookup
   *
   * Vanilla SVG force-directed layout (no D3 dep). Phase K3 baseline;
   * full interactive zoom + cohort-coloring deferred to K4.
   */
  import { onMount } from 'svelte';
  import { atQuery } from '$lib/atproto-agent';

  interface Props {
    viewerDid?: string;
    width?: number;
    height?: number;
  }

  const { viewerDid = '', width = 720, height = 480 }: Props = $props();

  // ── Karma.lean axis → color ────────────────────────────────────────
  const AXIS_COLOR: Record<string, string> = {
    vita:     '#e74c3c',  // life — red
    vivere:   '#f39c12',  // livelihood — amber
    veritas:  '#3498db',  // truth — blue
    vinculum: '#9b59b6',  // spirit-connection — purple
    venturum: '#27ae60',  // future/world — green
  };

  type Edge = {
    edgeId: string;
    sourceDid: string;
    targetDid: string;
    axis: string;
    tier: string;
    magnitude: number;
    direction: 'harm' | 'help' | 'witness';
    victimVul: number;
    tsMs: number;
    ipfsCid?: string;
    proofEncrypted?: boolean;
  };

  type Coverage = {
    edgesTotal?: number;
    edgesLast24h?: number;
    organismsActive?: number;
    organismsDissolved?: number;
    pinComplete?: number;
    pinPartial?: number;
    floorViolations24h?: number;
    axes?: Record<string, number>;
  };

  type Vertex = { did: string; x: number; y: number; vx: number; vy: number; isViewer: boolean };

  let coverage = $state<Coverage>({});
  let edges = $state<Edge[]>([]);
  let loading = $state(true);
  let errorMsg = $state('');
  let selectedDid = $state<string | null>(null);
  let selectedBalance = $state<number | null>(null);
  let vertices = $state<Vertex[]>([]);

  // ── Force-directed layout ─────────────────────────────────────────
  function buildLayout(es: Edge[], viewer: string): Vertex[] {
    const dids = new Set<string>();
    if (viewer) dids.add(viewer);
    for (const e of es) {
      if (e.sourceDid) dids.add(e.sourceDid);
      if (e.targetDid) dids.add(e.targetDid);
    }
    const cx = width / 2;
    const cy = height / 2;
    const r = Math.min(width, height) * 0.35;
    const list: Vertex[] = [];
    let i = 0;
    for (const d of dids) {
      const isViewer = d === viewer;
      if (isViewer) {
        list.push({ did: d, x: cx, y: cy, vx: 0, vy: 0, isViewer: true });
      } else {
        const angle = (i * 2 * Math.PI) / Math.max(dids.size - 1, 1);
        list.push({
          did: d,
          x: cx + r * Math.cos(angle),
          y: cy + r * Math.sin(angle),
          vx: 0, vy: 0,
          isViewer: false,
        });
      }
      i++;
    }
    // Run a few force-relax iterations
    for (let it = 0; it < 80; it++) {
      for (let a = 0; a < list.length; a++) {
        for (let b = a + 1; b < list.length; b++) {
          const dx = list[b].x - list[a].x;
          const dy = list[b].y - list[a].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          // Coulomb repulsion
          const f = 800 / (dist * dist);
          const fx = (dx / dist) * f;
          const fy = (dy / dist) * f;
          if (!list[a].isViewer) { list[a].vx -= fx; list[a].vy -= fy; }
          if (!list[b].isViewer) { list[b].vx += fx; list[b].vy += fy; }
        }
      }
      for (const v of list) {
        if (v.isViewer) continue;
        v.x += v.vx * 0.05;
        v.y += v.vy * 0.05;
        v.vx *= 0.85;
        v.vy *= 0.85;
        // Bound to viewport
        v.x = Math.max(40, Math.min(width - 40, v.x));
        v.y = Math.max(40, Math.min(height - 40, v.y));
      }
    }
    return list;
  }

  function vertexFor(did: string): Vertex | undefined {
    return vertices.find((v) => v.did === did);
  }

  function shortDid(did: string): string {
    if (!did) return '?';
    if (did.startsWith('did:web:')) return did.replace(/^did:web:/, '').replace(/^([^.]+)\..*$/, '$1');
    if (did.startsWith('did:plc:')) return did.slice(0, 12) + '…';
    return did.slice(0, 12) + '…';
  }

  async function loadEverything() {
    loading = true;
    errorMsg = '';
    try {
      const [cov, edgeRes] = await Promise.all([
        atQuery<Coverage>('ai.gftd.apps.karma.coverage', {}),
        viewerDid
          ? atQuery<{ edges: Edge[]; total: number }>('ai.gftd.apps.karma.listEdges', {
              did: viewerDid,
              direction: 'both',
              limit: 50,
            })
          : Promise.resolve({ edges: [] as Edge[], total: 0 }),
      ]);
      coverage = cov || {};
      edges = (edgeRes?.edges || []) as Edge[];
      vertices = buildLayout(edges, viewerDid);
    } catch (e) {
      errorMsg = (e as Error).message || 'load failed';
    } finally {
      loading = false;
    }
  }

  async function selectDid(did: string) {
    selectedDid = did;
    selectedBalance = null;
    try {
      const r = await atQuery<{ balance: number }>('ai.gftd.apps.karma.wbtBalance', { did });
      selectedBalance = r?.balance ?? 0;
    } catch {
      selectedBalance = null;
    }
  }

  onMount(() => {
    loadEverything();
  });
</script>

<div class="indranet">
  <header>
    <h2>因陀羅網 — Karma Edge Graph</h2>
    {#if !loading && coverage.edgesTotal !== undefined}
      <div class="stats">
        <span><b>{coverage.edgesTotal}</b> edges</span>
        <span><b>{coverage.organismsActive ?? 0}</b> alive</span>
        <span><b>{coverage.organismsDissolved ?? 0}</b> dissolved</span>
        <span><b>{coverage.pinComplete ?? 0}</b> 5/5 pinned</span>
        {#if (coverage.floorViolations24h ?? 0) > 0}
          <span class="alert"><b>{coverage.floorViolations24h}</b> floor violations 24h</span>
        {/if}
      </div>
    {/if}
  </header>

  {#if loading}
    <div class="loading">loading karma graph…</div>
  {:else if errorMsg}
    <div class="err">error: {errorMsg}</div>
  {:else}
    <div class="canvas">
      <svg width={width} height={height} viewBox="0 0 {width} {height}">
        <!-- edges first so vertices render on top -->
        {#each edges as e}
          {@const a = vertexFor(e.sourceDid)}
          {@const b = vertexFor(e.targetDid)}
          {#if a && b}
            <line
              x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              stroke={AXIS_COLOR[e.axis] ?? '#888'}
              stroke-width={1 + Math.min(6, Math.log10(Math.max(e.magnitude, 1)) * 1.5)}
              stroke-dasharray={e.direction === 'harm' ? '6 4' : 'none'}
              opacity={e.tier === 'floor' ? 1.0 : 0.7}
            />
          {/if}
        {/each}
        {#each vertices as v}
          <g
            tabindex="0"
            role="button"
            aria-label="organism {v.did}"
            on:click={() => selectDid(v.did)}
            on:keydown={(ev) => { if (ev.key === 'Enter' || ev.key === ' ') selectDid(v.did); }}
            style="cursor:pointer"
          >
            <circle
              cx={v.x} cy={v.y}
              r={v.isViewer ? 14 : 8}
              fill={v.isViewer ? '#222' : (selectedDid === v.did ? '#ffd700' : '#fafafa')}
              stroke={v.isViewer ? '#ffd700' : '#444'}
              stroke-width="2"
            />
            <text x={v.x} y={v.y + 24} text-anchor="middle" font-size="10" fill="#444">
              {shortDid(v.did)}
            </text>
          </g>
        {/each}
      </svg>
      <aside class="panel">
        {#if selectedDid}
          <h3>{shortDid(selectedDid)}</h3>
          <p class="did">{selectedDid}</p>
          <dl>
            <dt>WBT balance</dt>
            <dd>{selectedBalance === null ? '—' : selectedBalance}</dd>
          </dl>
        {:else}
          <p class="hint">click a vertex for details</p>
        {/if}
        <h4>axis legend</h4>
        <ul class="legend">
          <li><span class="sw" style="background:#e74c3c"></span> 命 Vita (life)</li>
          <li><span class="sw" style="background:#f39c12"></span> 業 Vivere (livelihood)</li>
          <li><span class="sw" style="background:#3498db"></span> 語 Veritas (truth)</li>
          <li><span class="sw" style="background:#9b59b6"></span> 縁 Vinculum (relation)</li>
          <li><span class="sw" style="background:#27ae60"></span> 世 Venturum (future)</li>
        </ul>
        <p class="hint">— — dashed = harm; solid = help</p>
      </aside>
    </div>
  {/if}
</div>

<style>
  .indranet {
    font-family: ui-sans-serif, system-ui, sans-serif;
    color: #222;
  }
  header h2 {
    font-size: 1.1rem;
    margin: 0 0 0.5rem 0;
  }
  .stats {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    font-size: 0.85rem;
    color: #555;
    margin-bottom: 0.75rem;
  }
  .stats .alert {
    color: #c0392b;
    font-weight: 600;
  }
  .canvas {
    display: flex;
    gap: 1rem;
  }
  svg {
    background: #f7f7f9;
    border: 1px solid #e2e2e2;
    border-radius: 6px;
    flex: 0 0 auto;
  }
  .panel {
    flex: 1 1 auto;
    min-width: 200px;
    font-size: 0.85rem;
  }
  .panel h3 {
    margin: 0 0 0.25rem 0;
  }
  .panel .did {
    font-family: ui-monospace, monospace;
    font-size: 0.75rem;
    color: #666;
    word-break: break-all;
  }
  .panel dl {
    margin: 0.5rem 0;
  }
  .panel dt {
    font-weight: 600;
    color: #555;
  }
  .panel dd {
    margin: 0.1rem 0 0.5rem 0;
  }
  .panel h4 {
    margin: 1rem 0 0.25rem 0;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #666;
  }
  .legend {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  .legend li {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.15rem 0;
  }
  .sw {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 2px;
  }
  .hint {
    color: #888;
    font-size: 0.75rem;
    margin: 0.5rem 0;
  }
  .loading, .err {
    padding: 2rem;
    text-align: center;
    color: #666;
  }
  .err {
    color: #c0392b;
  }

  @media (max-width: 720px) {
    .canvas { flex-direction: column; }
    svg { width: 100%; height: auto; }
  }
</style>
