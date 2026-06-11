<script lang="ts">
  import { onMount } from 'svelte';
  import { getSankey, type FlowClass, type SankeyEdge } from './lib/rf-xrpc';
  import Sankey from './lib/Sankey.svelte';
  import AnomalyPanel from './lib/AnomalyPanel.svelte';

  type Tab = 'sankey' | 'anomaly';

  function readInitialTab(): Tab {
    if (typeof window === 'undefined') return 'sankey';
    const v = new URLSearchParams(window.location.search).get('tab');
    return v === 'anomaly' ? 'anomaly' : 'sankey';
  }

  let tab = $state<Tab>(readInitialTab());
  let flowClass = $state<FlowClass>('currency');
  let domain = $state('hospitality');
  let fiscalPeriod = $state('');
  let edges = $state<SankeyEdge[]>([]);
  let loading = $state(false);
  let error = $state<string | null>(null);
  let lastUpdated = $state<string | null>(null);

  const VALUE_KEY = $derived(
    flowClass === 'currency'  ? 'amount_sum'  :
    flowClass === 'service'   ? 'total_count' :
    flowClass === 'personnel' ? 'headcount_sum' : 'event_count'
  );

  function setTab(next: Tab) {
    tab = next;
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.set('tab', next);
      window.history.replaceState({}, '', url);
    }
  }

  async function load() {
    if (tab !== 'sankey') return;
    loading = true;
    error = null;
    try {
      const out = await getSankey({
        flowClass,
        domain: domain || undefined,
        fiscalPeriod: fiscalPeriod || undefined,
        limit: 200,
      });
      edges = out.edges ?? [];
      lastUpdated = new Date().toISOString();
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
      edges = [];
    } finally {
      loading = false;
    }
  }

  onMount(load);
</script>

<main style="max-width:1100px;margin:0 auto;padding:24px">
  <header style="margin-bottom:18px">
    <h1 style="margin:0 0 6px;font-size:22px">resource-flow.etzhayyim.com</h1>
    <p style="margin:0;color:#9aa0aa;font-size:13px">
      ADR-0028 cluster · ADR-0074 root-keyed · ADR-0046 anomaly cron · pipethrough
      <code>atproto.etzhayyim.com/xrpc/com.etzhayyim.apps.resourceFlow.*</code>
    </p>
  </header>

  <nav style="display:flex;gap:4px;margin-bottom:18px;border-bottom:1px solid #232834">
    <button
      onclick={() => setTab('sankey')}
      style="padding:8px 16px;background:transparent;color:{tab === 'sankey' ? '#e6e6e6' : '#9aa0aa'};border:0;border-bottom:2px solid {tab === 'sankey' ? '#2d6cdf' : 'transparent'};cursor:pointer;font-size:14px"
    >Sankey</button>
    <button
      onclick={() => setTab('anomaly')}
      style="padding:8px 16px;background:transparent;color:{tab === 'anomaly' ? '#e6e6e6' : '#9aa0aa'};border:0;border-bottom:2px solid {tab === 'anomaly' ? '#2d6cdf' : 'transparent'};cursor:pointer;font-size:14px"
    >Anomalies</button>
  </nav>

  {#if tab === 'sankey'}
    <form
      style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:end;margin-bottom:18px"
      onsubmit={(e) => { e.preventDefault(); load(); }}
    >
      <label style="display:flex;flex-direction:column;gap:4px;font-size:12px">
        Flow class
        <select bind:value={flowClass} style="padding:6px 8px;background:#161a22;color:#e6e6e6;border:1px solid #2a2f3a;border-radius:4px">
          <option value="currency">currency</option>
          <option value="service">service</option>
          <option value="personnel">personnel</option>
        </select>
      </label>
      <label style="display:flex;flex-direction:column;gap:4px;font-size:12px">
        Domain
        <select bind:value={domain} style="padding:6px 8px;background:#161a22;color:#e6e6e6;border:1px solid #2a2f3a;border-radius:4px">
          <option value="">(any)</option>
          <option value="hospitality">hospitality</option>
          <option value="transport">transport</option>
          <option value="manufacturing">manufacturing</option>
        </select>
      </label>
      <label style="display:flex;flex-direction:column;gap:4px;font-size:12px">
        Fiscal period
        <input
          bind:value={fiscalPeriod}
          placeholder="YYYY-MM / YYYY-Qn / YYYY"
          style="padding:6px 8px;background:#161a22;color:#e6e6e6;border:1px solid #2a2f3a;border-radius:4px"
        />
      </label>
      <button
        type="submit"
        disabled={loading}
        style="padding:8px 12px;background:#2d6cdf;color:white;border:0;border-radius:4px;cursor:pointer;opacity:{loading ? 0.6 : 1}"
      >
        {loading ? 'Loading…' : 'Refresh'}
      </button>
    </form>

    {#if error}
      <div style="margin-bottom:14px;padding:10px 12px;background:#3a1a1a;color:#ffb3b3;border:1px solid #5a2c2c;border-radius:4px;font-size:13px">
        {error}
      </div>
    {/if}

    <section style="background:#11141b;border:1px solid #232834;border-radius:6px;padding:12px">
      <p style="margin:0 0 10px;color:#9aa0aa;font-size:12px">
        {edges.length} edge(s) · value key <code>{VALUE_KEY}</code>
        {#if lastUpdated}· updated {new Date(lastUpdated).toLocaleTimeString()}{/if}
      </p>
      {#if edges.length === 0 && !loading && !error}
        <p style="color:#9aa0aa;font-size:13px;margin:30px 0;text-align:center">
          No edges yet. Confirm a yadoya reservation (or wait for the firehose
          consumer to ingest legalEntity{`{`}Currency,Service,Personnel{`}`}Flow records).
        </p>
      {:else}
        <Sankey {edges} valueKey={VALUE_KEY} width={1050} height={540} />
      {/if}
    </section>
  {:else}
    <AnomalyPanel />
  {/if}

  <p style="margin-top:14px;color:#6c7280;font-size:11px">
    PII tier 1 — aggregate only, no individual DID. ADR-0018 cohort_size ≥ 5
    enforced upstream. Counterparty labels resolved via
    <code>getActorLabels</code> (single round-trip).
  </p>
</main>
