<script lang="ts">
  type MetricSet = {
    actorCount: number;
    flowCount: number;
    jurisdictionCount: number;
    activeDiversificationProjects: number;
    mineralCount: number;
  };

  type Bottleneck = {
    title: string;
    detail: string;
    severity: string;
  };

  type StageCoverage = {
    stage: string;
    count: number;
  };

  type Actor = {
    did: string;
    displayName: string;
    stage: string;
    jurisdiction: string;
    priority: number;
    deps: string[];
  };

  type Flow = {
    source: string;
    target: string;
    kind: string;
    status: string;
  };

  type Mineral = {
    did: string;
    displayName: string;
    priority: number;
    deps: string[];
    keySectors: string[];
    coverage: string;
  };

  type Coverage = {
    updatedAt: string;
    primaryActorDid: string;
    appviewDid: string;
    metrics: MetricSet;
    bottlenecks: Bottleneck[];
    stageCoverage: StageCoverage[];
    minerals: Mineral[];
    actors: Actor[];
    flows: Flow[];
  };

  type HeartbeatAction = {
    action: string;
    mood?: string;
    reason?: string;
    ts: string;
    summary?: string;
  };

  type ShinkaState = {
    updatedAt: string;
    collections: string[];
    subDids: Array<{ path: string; displayName: string }>;
    heartbeat: {
      mood: string;
      summary: string;
      actions: HeartbeatAction[];
    };
  };

  let data: Coverage | null = null;
  let shinka: ShinkaState | null = null;
  let stageFilter = 'all';
  let flowFilter = 'all';

  const stageColor: Record<string, string> = {
    policy: '#f97316',
    finance: '#14b8a6',
    extraction: '#84cc16',
    separation: '#38bdf8',
    processing: '#60a5fa',
    'magnet-manufacturing': '#f43f5e',
    demand: '#facc15',
  };

  fetch('/xrpc/com.etzhayyim.apps.rareEarth.coverage.listActors')
    .then((res) => res.json())
    .then((payload) => payload.actors)
    .then((actors: Actor[]) =>
      fetch('/xrpc/com.etzhayyim.apps.rareEarth.coverage.listFlows')
        .then((res) => res.json())
        .then((payload) => payload.flows)
        .then((flows: Flow[]) => ({ actors, flows }))
    )
    .then(({ actors, flows }) =>
      fetch('/api/rare-earth/coverage')
        .then((res) => res.json())
        .then((json: Coverage) => ({ ...json, actors, flows }))
    )
    .then((json: Coverage) => {
      data = json;
    });

  fetch('/api/rare-earth/shinka')
    .then((res) => res.json())
    .then((json: ShinkaState) => {
      shinka = json;
    });

  const visibleActors = () =>
    data?.actors.filter((actor) => stageFilter === 'all' || actor.stage === stageFilter) ?? [];

  const visibleFlows = () =>
    data?.flows.filter((flow) => flowFilter === 'all' || flow.kind === flowFilter) ?? [];
</script>

{#if data}
  <main class="shell">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Rare Earth Coverage</p>
        <h1>Actor DID registry for the current rare earth bottleneck map.</h1>
        <p class="lede">
          The appview fronts <code>{data.primaryActorDid}</code> and tracks mining, separation,
          magnet, policy, finance, and demand actors as one flow system.
        </p>
      </div>
      <div class="hero-meta">
        <div class="meta-card">
          <span>Updated</span>
          <strong>{new Date(data.updatedAt).toLocaleString()}</strong>
        </div>
        <div class="meta-card">
          <span>Appview DID</span>
          <strong>{data.appviewDid}</strong>
        </div>
      </div>
    </section>

    <section class="metrics">
      <article>
        <span>Actors</span>
        <strong>{data.metrics.actorCount}</strong>
      </article>
      <article>
        <span>Flows</span>
        <strong>{data.metrics.flowCount}</strong>
      </article>
      <article>
        <span>Jurisdictions</span>
        <strong>{data.metrics.jurisdictionCount}</strong>
      </article>
      <article>
        <span>Diversification Projects</span>
        <strong>{data.metrics.activeDiversificationProjects}</strong>
      </article>
      <article>
        <span>Mineral Registries</span>
        <strong>{data.metrics.mineralCount}</strong>
      </article>
    </section>

    <section class="grid">
      <article class="panel panel-wide">
        <div class="panel-head">
          <h2>Stage Coverage</h2>
          <p>Current registered actor spread by supply-chain stage.</p>
        </div>
        <div class="bars">
          {#each data.stageCoverage as item}
            <div class="bar-row">
              <div class="bar-label">
                <span>{item.stage}</span>
                <strong>{item.count}</strong>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  style={`width:${Math.max(12, item.count * 8)}%; background:${stageColor[item.stage] ?? '#94a3b8'}`}
                ></div>
              </div>
            </div>
          {/each}
        </div>
      </article>

      <article class="panel">
        <div class="panel-head">
          <h2>Bottlenecks</h2>
          <p>Highest-impact coverage and market risks.</p>
        </div>
        <div class="stack">
          {#each data.bottlenecks as item}
            <div class="risk">
              <span class={`severity severity-${item.severity}`}>{item.severity}</span>
              <strong>{item.title}</strong>
              <p>{item.detail}</p>
            </div>
          {/each}
        </div>
      </article>
    </section>

    <section class="grid">
      {#if shinka}
        <article class="panel">
          <div class="panel-head">
            <h2>Heartbeat / Shinka</h2>
            <p>Cadence-driven coverage evolution state for this appview.</p>
          </div>
          <div class="stack">
            <div class="risk">
              <span class="severity severity-high">{shinka.heartbeat.mood}</span>
              <strong>{shinka.heartbeat.summary}</strong>
              <p>{shinka.collections.join(' / ')}</p>
            </div>
            {#each shinka.heartbeat.actions as item}
              <div class="flow-item">
                <div class="flow-top">
                  <span class="flow-kind">{item.action}</span>
                  <span class="flow-status">{item.mood ?? 'steady'}</span>
                </div>
                <strong>{item.summary ?? item.reason ?? 'heartbeat action'}</strong>
              </div>
            {/each}
          </div>
        </article>
      {/if}

      <article class="panel panel-wide">
        <div class="panel-head">
          <h2>Mineral DID Registry</h2>
          <p>Tungsten, antimony, gallium, germanium, graphite, and rare-earth dependency nodes.</p>
        </div>
        <div class="actor-list mineral-list">
          {#each data.minerals as mineral}
            <div class="actor-card mineral-card">
              <div class="actor-top">
                <strong>{mineral.displayName}</strong>
                <span class={`badge badge-${mineral.coverage}`}>{mineral.coverage}</span>
              </div>
              <div class="actor-meta">
                <span>P{mineral.priority}</span>
                <span>{mineral.keySectors.join(' / ')}</span>
              </div>
              <code>{mineral.did}</code>
              <p class="deps-line">{mineral.deps.length} deps</p>
            </div>
          {/each}
        </div>
      </article>

      <article class="panel panel-wide">
        <div class="panel-head">
          <h2>Priority Actors</h2>
          <p>Registered mitama DIDs across the backbone.</p>
        </div>
        <div class="toolbar">
          <label>
            <span>Stage</span>
            <select bind:value={stageFilter}>
              <option value="all">all</option>
              {#each [...new Set(data.actors.map((actor) => actor.stage))] as stage}
                <option value={stage}>{stage}</option>
              {/each}
            </select>
          </label>
        </div>
        <div class="actor-list">
          {#each visibleActors() as actor}
            <div class="actor-card">
              <div class="actor-top">
                <strong>{actor.displayName}</strong>
                <span class="badge">{actor.jurisdiction}</span>
              </div>
              <div class="actor-meta">
                <span>{actor.stage}</span>
                <span>P{actor.priority}</span>
              </div>
              <code>{actor.did}</code>
              <p class="deps-line">{actor.deps.length} deps</p>
            </div>
          {/each}
        </div>
      </article>

      <article class="panel">
        <div class="panel-head">
          <h2>Backbone Flows</h2>
          <p>Active and planned edges across policy, capital, and material movement.</p>
        </div>
        <div class="toolbar">
          <label>
            <span>Kind</span>
            <select bind:value={flowFilter}>
              <option value="all">all</option>
              {#each [...new Set(data.flows.map((flow) => flow.kind))] as kind}
                <option value={kind}>{kind}</option>
              {/each}
            </select>
          </label>
        </div>
        <div class="flow-list">
          {#each visibleFlows() as flow}
            <div class="flow-item">
              <div class="flow-top">
                <span class="flow-kind">{flow.kind}</span>
                <span class={`flow-status flow-status-${flow.status}`}>{flow.status}</span>
              </div>
              <strong>{flow.source}</strong>
              <span class="arrow">→</span>
              <strong>{flow.target}</strong>
            </div>
          {/each}
        </div>
      </article>
    </section>
  </main>
{:else}
  <main class="loading">Loading rare earth coverage...</main>
{/if}

<style>
  :global(body) {
    margin: 0;
    font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
    color: #ecfeff;
    background:
      radial-gradient(circle at top left, rgba(34, 197, 94, 0.2), transparent 28%),
      radial-gradient(circle at top right, rgba(244, 63, 94, 0.18), transparent 30%),
      linear-gradient(180deg, #082f49 0%, #071827 48%, #020617 100%);
  }

  .shell {
    max-width: 1380px;
    margin: 0 auto;
    padding: 40px 20px 72px;
  }

  .hero {
    display: grid;
    grid-template-columns: 1.6fr 0.9fr;
    gap: 20px;
    align-items: end;
    margin-bottom: 24px;
  }

  .eyebrow {
    margin: 0 0 10px;
    color: #67e8f9;
    font-size: 0.85rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  h1, h2, p {
    margin: 0;
  }

  h1 {
    font-family: "Space Grotesk", "IBM Plex Sans", sans-serif;
    font-size: clamp(2rem, 4vw, 4.8rem);
    line-height: 0.94;
    max-width: 12ch;
  }

  .lede {
    margin-top: 14px;
    max-width: 62ch;
    color: #cbd5e1;
    line-height: 1.65;
  }

  .hero-meta {
    display: grid;
    gap: 12px;
  }

  .meta-card,
  .panel,
  .metrics article {
    background: rgba(8, 15, 29, 0.72);
    border: 1px solid rgba(125, 211, 252, 0.15);
    box-shadow: 0 20px 50px rgba(2, 6, 23, 0.28);
    backdrop-filter: blur(18px);
  }

  .meta-card {
    padding: 16px;
    border-radius: 18px;
  }

  .meta-card span {
    display: block;
    color: #67e8f9;
    font-size: 0.8rem;
    margin-bottom: 8px;
  }

  .meta-card strong {
    display: block;
    word-break: break-word;
  }

  .metrics {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 14px;
    margin-bottom: 24px;
  }

  .metrics article {
    padding: 18px;
    border-radius: 18px;
  }

  .metrics span {
    display: block;
    color: #93c5fd;
    margin-bottom: 10px;
  }

  .metrics strong {
    font-size: 2rem;
    font-family: "Space Grotesk", sans-serif;
  }

  .grid {
    display: grid;
    grid-template-columns: 1.25fr 0.9fr;
    gap: 16px;
    margin-bottom: 16px;
  }

  .panel {
    border-radius: 24px;
    padding: 22px;
  }

  .panel-wide {
    min-width: 0;
  }

  .panel-head {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: end;
    margin-bottom: 18px;
  }

  .panel-head p {
    max-width: 30ch;
    color: #94a3b8;
    font-size: 0.95rem;
    line-height: 1.5;
  }

  .bars,
  .stack,
  .flow-list {
    display: grid;
    gap: 12px;
  }

  .bar-row {
    display: grid;
    gap: 8px;
  }

  .bar-label {
    display: flex;
    justify-content: space-between;
    color: #cbd5e1;
  }

  .bar-track {
    height: 12px;
    border-radius: 999px;
    overflow: hidden;
    background: rgba(148, 163, 184, 0.16);
  }

  .bar-fill {
    height: 100%;
    border-radius: 999px;
  }

  .risk,
  .flow-item,
  .actor-card {
    padding: 14px;
    border-radius: 18px;
    background: rgba(15, 23, 42, 0.68);
    border: 1px solid rgba(148, 163, 184, 0.12);
  }

  .risk p {
    color: #cbd5e1;
    margin-top: 6px;
    line-height: 1.55;
  }

  .severity {
    display: inline-flex;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
  }

  .severity-critical {
    background: rgba(244, 63, 94, 0.16);
    color: #fda4af;
  }

  .severity-high {
    background: rgba(249, 115, 22, 0.16);
    color: #fdba74;
  }

  .actor-list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 12px;
  }

  .mineral-list {
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  }

  .actor-top,
  .actor-meta,
  .flow-top {
    display: flex;
    justify-content: space-between;
    gap: 10px;
  }

  .actor-meta {
    color: #94a3b8;
    margin: 10px 0;
    font-size: 0.9rem;
  }

  .badge,
  .flow-kind,
  .flow-status {
    display: inline-flex;
    align-items: center;
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 0.76rem;
    background: rgba(56, 189, 248, 0.14);
    color: #7dd3fc;
  }

  .badge-expanded {
    background: rgba(250, 204, 21, 0.16);
    color: #fde68a;
  }

  code {
    display: block;
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.76rem;
    color: #67e8f9;
    word-break: break-all;
  }

  .deps-line {
    margin-top: 10px;
    color: #94a3b8;
    font-size: 0.82rem;
  }

  .mineral-card {
    background: linear-gradient(180deg, rgba(12, 74, 110, 0.5), rgba(15, 23, 42, 0.78));
  }

  .flow-item {
    display: grid;
    gap: 6px;
  }

  .arrow {
    color: #67e8f9;
  }

  .flow-status-planned {
    background: rgba(250, 204, 21, 0.16);
    color: #fde68a;
  }

  .loading {
    min-height: 100vh;
    display: grid;
    place-items: center;
    font-family: "Space Grotesk", sans-serif;
    font-size: 1.4rem;
  }

  .toolbar {
    display: flex;
    margin-bottom: 14px;
  }

  .toolbar label {
    display: grid;
    gap: 6px;
    color: #94a3b8;
    font-size: 0.88rem;
  }

  .toolbar select {
    appearance: none;
    background: rgba(15, 23, 42, 0.92);
    color: #e2e8f0;
    border: 1px solid rgba(125, 211, 252, 0.18);
    border-radius: 12px;
    padding: 8px 10px;
  }

  @media (max-width: 980px) {
    .hero,
    .grid {
      grid-template-columns: 1fr;
    }

    .metrics {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .panel-head {
      display: grid;
    }
  }
</style>
