<script lang="ts">
  import { onMount } from 'svelte';
  import { listAnomalies, resolveProfiles, reviewAnomaly, shortLabel } from './rf-xrpc';
  import type { Anomaly, AnomalyAction, AnomalyReviewedFilter, AnomalySeverity, FlowClass } from './rf-xrpc';

  function readBearer(): string | undefined {
    if (typeof window === 'undefined') return undefined;
    const w = window as any;
    if (typeof w.__RF_BEARER__ === 'string' && w.__RF_BEARER__) return w.__RF_BEARER__;
    if (typeof localStorage !== 'undefined') {
      const v = localStorage.getItem('rf:bearer');
      if (v) return v;
    }
    return undefined;
  }

  let flowClass = $state<FlowClass | ''>('');
  let severity  = $state<AnomalySeverity | ''>('');
  let reviewed  = $state<AnomalyReviewedFilter>('open');
  let anomalies = $state<Anomaly[]>([]);
  let labels = $state<Record<string, string>>({});
  let loading = $state(false);
  let error = $state<string | null>(null);
  let pendingId = $state<string | null>(null);
  let toast = $state<string | null>(null);

  const SEVERITY_COLOR: Record<AnomalySeverity, string> = {
    critical: '#ff4d4f',
    high:     '#ff9f43',
    medium:   '#feca57',
    low:      '#5dade2',
  };

  function ratio(a: Anomaly): number {
    if (!(a.baseline_avg > 0)) return 0;
    return a.observed_value / a.baseline_avg;
  }

  function display(did: string | null): string {
    if (!did) return 'independent';
    return labels[did] ?? shortLabel(did);
  }

  async function load() {
    loading = true;
    error = null;
    try {
      const params: Record<string, string | number | undefined> = { limit: 50, reviewed };
      if (flowClass) params.flowClass = flowClass;
      if (severity)  params.severity  = severity;
      const out = await listAnomalies(params as any);
      anomalies = out.anomalies ?? [];
      // Resolve labels for every distinct DID in one call.
      const ids = new Set<string>();
      for (const a of anomalies) {
        if (a.source_did) ids.add(a.source_did);
        if (a.counterparty_did) ids.add(a.counterparty_did);
      }
      const map = await resolveProfiles(Array.from(ids));
      const next: Record<string, string> = {};
      for (const id of ids) {
        const p = map[id];
        next[id] = p?.displayName ?? p?.handle ?? shortLabel(id);
      }
      labels = next;
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
      anomalies = [];
    } finally {
      loading = false;
    }
  }

  async function review(a: Anomaly, action: AnomalyAction) {
    if (pendingId) return;
    pendingId = a.vertex_id;
    toast = null;
    try {
      const out = await reviewAnomaly(
        { anomalyId: a.vertex_id, action, post: true },
        readBearer(),
      );
      toast = `${action} recorded — ${out.reviewId}`;
      if (reviewed === 'open') {
        // Optimistically remove from the open queue; the canonical state
        // surfaces on next refresh through mv_resource_flow_anomaly_review_latest.
        anomalies = anomalies.filter((x) => x.vertex_id !== a.vertex_id);
      } else {
        // Tag the row as reviewed in-place (closed / any view).
        anomalies = anomalies.map((x) => x.vertex_id === a.vertex_id
          ? {
              ...x,
              review_count:        (x.review_count ?? 0) + 1,
              last_action:         action,
              last_reviewed_at:    new Date().toISOString(),
              last_reviewer_did:   x.last_reviewer_did ?? null,
              last_thread_post_uri: out.threadUri ?? x.last_thread_post_uri ?? null,
            }
          : x);
      }
    } catch (err) {
      toast = err instanceof Error ? err.message : String(err);
    } finally {
      pendingId = null;
    }
  }

  onMount(load);
</script>

<section style="background:#11141b;border:1px solid #232834;border-radius:6px;padding:14px">
  <form
    style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:end;margin-bottom:14px"
    onsubmit={(e) => { e.preventDefault(); load(); }}
  >
    <label style="display:flex;flex-direction:column;gap:4px;font-size:12px">
      Flow class
      <select bind:value={flowClass} style="padding:6px 8px;background:#161a22;color:#e6e6e6;border:1px solid #2a2f3a;border-radius:4px">
        <option value="">(any)</option>
        <option value="currency">currency</option>
        <option value="service">service</option>
        <option value="personnel">personnel</option>
      </select>
    </label>
    <label style="display:flex;flex-direction:column;gap:4px;font-size:12px">
      Severity
      <select bind:value={severity} style="padding:6px 8px;background:#161a22;color:#e6e6e6;border:1px solid #2a2f3a;border-radius:4px">
        <option value="">(any)</option>
        <option value="critical">critical</option>
        <option value="high">high</option>
        <option value="medium">medium</option>
        <option value="low">low</option>
      </select>
    </label>
    <label style="display:flex;flex-direction:column;gap:4px;font-size:12px">
      Reviewed
      <select bind:value={reviewed} style="padding:6px 8px;background:#161a22;color:#e6e6e6;border:1px solid #2a2f3a;border-radius:4px">
        <option value="open">open (queue)</option>
        <option value="closed">closed (reviewed)</option>
        <option value="any">any</option>
      </select>
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

  <p style="margin:0 0 10px;color:#9aa0aa;font-size:12px">{anomalies.length} anomaly(ies)</p>

  {#if toast}
    <div style="margin-bottom:10px;padding:6px 10px;background:#142031;color:#9ec1ff;border:1px solid #234063;border-radius:4px;font-size:12px">
      {toast}
    </div>
  {/if}

  {#if anomalies.length === 0 && !loading && !error}
    <p style="color:#9aa0aa;font-size:13px;margin:30px 0;text-align:center">
      No anomalies. The R/PT24H detector hasn't flagged anything yet — or
      the cluster baseline is still warming up (need at least 3 baseline
      periods per tuple).
    </p>
  {:else}
    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <thead>
        <tr style="text-align:left;color:#9aa0aa;border-bottom:1px solid #232834">
          <th style="padding:6px 4px">Severity</th>
          <th style="padding:6px 4px">Flow</th>
          <th style="padding:6px 4px">Source → Counterparty</th>
          <th style="padding:6px 4px">Period</th>
          <th style="padding:6px 4px;text-align:right">Observed</th>
          <th style="padding:6px 4px;text-align:right">Baseline</th>
          <th style="padding:6px 4px;text-align:right">Ratio</th>
          <th style="padding:6px 4px">When</th>
          <th style="padding:6px 4px">Status</th>
          <th style="padding:6px 4px">Review</th>
        </tr>
      </thead>
      <tbody>
        {#each anomalies as a (a.vertex_id)}
          {@const r = ratio(a)}
          {@const isReviewed = (a.review_count ?? 0) > 0}
          <tr style="border-bottom:1px solid #1a1d24;opacity:{isReviewed ? 0.55 : 1}">
            <td style="padding:8px 4px">
              <span style="display:inline-block;padding:2px 8px;border-radius:4px;background:{SEVERITY_COLOR[a.severity]}22;color:{SEVERITY_COLOR[a.severity]};font-weight:600;font-size:11px;text-transform:uppercase">
                {a.severity}
              </span>
            </td>
            <td style="padding:8px 4px;color:#9aa0aa">{a.flow_class}</td>
            <td style="padding:8px 4px">
              <span title={a.source_did}>{display(a.source_did)}</span>
              <span style="color:#5a6068"> → </span>
              <span title={a.counterparty_did ?? ''}>{display(a.counterparty_did)}</span>
            </td>
            <td style="padding:8px 4px;color:#9aa0aa">{a.fiscal_period}</td>
            <td style="padding:8px 4px;text-align:right;font-variant-numeric:tabular-nums">{a.observed_value.toFixed(0)}</td>
            <td style="padding:8px 4px;text-align:right;font-variant-numeric:tabular-nums;color:#9aa0aa">{a.baseline_avg.toFixed(2)}</td>
            <td style="padding:8px 4px;text-align:right;font-variant-numeric:tabular-nums;font-weight:600;color:{SEVERITY_COLOR[a.severity]}">{r.toFixed(2)}×</td>
            <td style="padding:8px 4px;color:#9aa0aa;font-size:11px;font-variant-numeric:tabular-nums">
              {new Date(a.observed_at).toISOString().slice(0, 16).replace('T', ' ')}
            </td>
            <td style="padding:8px 4px;font-size:11px">
              {#if isReviewed}
                <span style="display:inline-block;padding:2px 6px;border-radius:3px;background:#1f3a2c;color:#7bd6a3;text-transform:uppercase;font-weight:600">
                  {a.last_action ?? 'reviewed'}
                </span>
                {#if a.review_count && a.review_count > 1}
                  <span style="color:#5a6068">·{a.review_count}</span>
                {/if}
              {:else}
                <span style="color:#9aa0aa">open</span>
              {/if}
            </td>
            <td style="padding:8px 4px">
              <div style="display:flex;gap:4px">
                {#each (['acknowledge','dismiss','escalate'] as AnomalyAction[]) as act}
                  <button
                    onclick={() => review(a, act)}
                    disabled={pendingId === a.vertex_id}
                    title={act}
                    style="padding:3px 6px;font-size:10px;background:transparent;color:#9aa0aa;border:1px solid #2a2f3a;border-radius:3px;cursor:pointer;text-transform:uppercase;opacity:{pendingId === a.vertex_id ? 0.4 : 1}"
                  >{act === 'acknowledge' ? 'ACK' : act === 'dismiss' ? 'DIS' : 'ESC'}</button>
                {/each}
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}

  <p style="margin-top:14px;color:#6c7280;font-size:11px">
    Detector: <code>R/PT24H</code> BPMN cron · threshold 3.0× rolling 30-day avg ·
    written by <code>com.etzhayyim.apps.resourceFlow.detectAnomaly</code> · listed via
    <code>com.etzhayyim.apps.resourceFlow.listAnomalies</code>.
  </p>
</section>
