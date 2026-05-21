<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { api, severityLabel, type IncidentSummary, type IncidentStatus, type ValidityStatus } from "$lib/api";

  let incidents: IncidentSummary[] = [];
  let total = 0;
  let loading = true;
  let error = "";

  // filters
  let filterStatus: IncidentStatus | "" = "open";
  let filterValidity: ValidityStatus | "" = "";
  let filterRepo = "";
  let limit = 25;
  let offset = 0;

  async function load() {
    loading = true; error = "";
    try {
      const res = await api.listIncidents({
        status: filterStatus || undefined,
        validity: filterValidity || undefined,
        repoId: filterRepo.trim() || undefined,
        limit,
        offset,
      });
      incidents = res.incidents;
      total = res.total;
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  onMount(load);

  function applyFilters() { offset = 0; load(); }

  const SEV_COLOR: Record<string, string> = {
    critical: "var(--red)",
    high:     "var(--orange)",
    medium:   "var(--yellow)",
    low:      "var(--blue)",
    info:     "var(--muted)",
  };

  const STATUS_LABEL: Record<string, string> = {
    open:           "Open",
    resolved:       "Resolved",
    false_positive: "False Positive",
    accepted_risk:  "Accepted Risk",
  };

  const VALIDITY_COLOR: Record<string, string> = {
    valid:   "var(--red)",
    invalid: "var(--green)",
    unknown: "var(--muted)",
  };

  function fmtDate(iso: string) {
    return new Date(iso).toLocaleDateString("en", { month: "short", day: "numeric", year: "numeric" });
  }

  function secretLabel(t: string) {
    return t.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  function permilleBar(p: number) {
    return Math.round(p / 10);
  }
</script>

<svelte:head><title>Incidents — mamoru</title></svelte:head>

<div class="page">
  <div class="page-header">
    <div>
      <h1>Incidents</h1>
      {#if !loading}<span class="count">{total} total</span>{/if}
    </div>
    <a href="/scan" class="btn-primary">+ Scan commit</a>
  </div>

  <!-- Filters -->
  <div class="filters">
    <select bind:value={filterStatus} on:change={applyFilters}>
      <option value="">All statuses</option>
      <option value="open">Open</option>
      <option value="resolved">Resolved</option>
      <option value="false_positive">False Positive</option>
      <option value="accepted_risk">Accepted Risk</option>
    </select>
    <select bind:value={filterValidity} on:change={applyFilters}>
      <option value="">All validity</option>
      <option value="valid">Valid (active leak)</option>
      <option value="invalid">Invalid (revoked)</option>
      <option value="unknown">Unknown</option>
    </select>
    <input
      type="text"
      placeholder="Filter by repo (owner/name)"
      bind:value={filterRepo}
      on:keydown={(e) => e.key === "Enter" && applyFilters()}
    />
    <button class="btn-secondary" on:click={applyFilters}>Filter</button>
  </div>

  {#if error}
    <div class="alert-error">
      {#if error === "AuthRequired"}
        Enter your API key (🔑 button above) to view incidents.
      {:else}
        {error}
      {/if}
    </div>
  {:else if loading}
    <div class="loading">
      <div class="spinner"></div>
      <span>Loading incidents…</span>
    </div>
  {:else if incidents.length === 0}
    <div class="empty">
      <div class="empty-icon">🛡</div>
      <p>No incidents found</p>
      <span>Either there are no secrets detected, or try adjusting your filters.</span>
    </div>
  {:else}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Severity</th>
            <th>Secret type</th>
            <th>Repository</th>
            <th>Validity</th>
            <th>Status</th>
            <th>Occurrences</th>
            <th>First seen</th>
          </tr>
        </thead>
        <tbody>
          {#each incidents as inc (inc.incidentId)}
            {@const sev = severityLabel(inc.severityPermille)}
            <tr on:click={() => goto(`/incident/${inc.incidentId}`)} class="row-link">
              <td>
                <div class="sev-cell">
                  <div class="sev-bar-wrap">
                    <div
                      class="sev-bar"
                      style="width:{permilleBar(inc.severityPermille)}%; background:{SEV_COLOR[sev]}"
                    ></div>
                  </div>
                  <span class="sev-badge" style="color:{SEV_COLOR[sev]}">{sev}</span>
                </div>
              </td>
              <td class="mono">{secretLabel(inc.secretType)}</td>
              <td class="repo">{inc.repoId}</td>
              <td>
                <span class="validity-dot" style="color:{VALIDITY_COLOR[inc.validity]}">●</span>
                {inc.validity}
              </td>
              <td>
                <span class="status-chip" class:open={inc.status === "open"}>
                  {STATUS_LABEL[inc.status] ?? inc.status}
                </span>
              </td>
              <td class="num">{inc.occurrenceCount}</td>
              <td class="date">{fmtDate(inc.firstSeenAt)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    {#if total > limit}
      <div class="pagination">
        <button disabled={offset === 0} on:click={() => { offset = Math.max(0, offset - limit); load(); }}>
          ← Prev
        </button>
        <span>{offset + 1}–{Math.min(offset + limit, total)} of {total}</span>
        <button disabled={offset + limit >= total} on:click={() => { offset += limit; load(); }}>
          Next →
        </button>
      </div>
    {/if}
  {/if}
</div>

<style>
  .page-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 20px;
  }
  h1 { font-size: 20px; font-weight: 600; }
  .count { margin-left: 10px; font-size: 13px; color: var(--muted); }

  .btn-primary {
    background: var(--red); color: #fff; border: none;
    padding: 7px 14px; border-radius: 6px; font-size: 13px; font-weight: 500;
    transition: opacity 0.15s;
  }
  .btn-primary:hover { opacity: 0.85; }

  .filters {
    display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px;
  }
  .filters select, .filters input {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 6px 10px;
    color: var(--text); font-size: 13px;
  }
  .filters input { min-width: 220px; }
  .filters select:focus, .filters input:focus { outline: none; border-color: var(--blue); }
  .btn-secondary {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 6px 12px; color: var(--text); font-size: 13px;
    transition: border-color 0.15s;
  }
  .btn-secondary:hover { border-color: var(--blue); }

  .alert-error {
    background: rgba(248, 81, 73, 0.12);
    border: 1px solid rgba(248, 81, 73, 0.3);
    border-radius: 8px; padding: 14px 18px;
    color: var(--red); font-size: 13px;
  }

  .loading {
    display: flex; align-items: center; gap: 12px;
    padding: 48px; justify-content: center; color: var(--muted);
  }
  .spinner {
    width: 18px; height: 18px;
    border: 2px solid var(--border);
    border-top-color: var(--blue);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .empty {
    text-align: center; padding: 72px 24px;
    color: var(--muted);
  }
  .empty-icon { font-size: 48px; margin-bottom: 16px; }
  .empty p { font-size: 16px; color: var(--text); margin-bottom: 6px; }
  .empty span { font-size: 13px; }

  .table-wrap {
    border: 1px solid var(--border); border-radius: 8px; overflow: hidden;
  }
  table { width: 100%; border-collapse: collapse; }
  thead { background: var(--surface); }
  th {
    padding: 10px 14px; text-align: left;
    font-size: 12px; font-weight: 600; color: var(--muted);
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }
  td { padding: 12px 14px; border-bottom: 1px solid rgba(48,54,61,0.6); font-size: 13px; }
  tr:last-child td { border-bottom: none; }
  .row-link { cursor: pointer; transition: background 0.1s; }
  .row-link:hover { background: rgba(255,255,255,0.03); }

  .sev-cell { display: flex; align-items: center; gap: 8px; }
  .sev-bar-wrap {
    width: 60px; height: 4px;
    background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden;
  }
  .sev-bar { height: 100%; border-radius: 2px; transition: width 0.3s; }
  .sev-badge { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }

  .mono { font-family: "SFMono-Regular", Consolas, monospace; font-size: 12px; }
  .repo { color: var(--blue); font-size: 12px; font-family: monospace; }
  .validity-dot { margin-right: 4px; }
  .num { text-align: right; color: var(--muted); }
  .date { color: var(--muted); white-space: nowrap; }

  .status-chip {
    display: inline-block;
    padding: 2px 8px; border-radius: 12px;
    font-size: 11px; font-weight: 500;
    background: rgba(255,255,255,0.06);
    color: var(--muted);
  }
  .status-chip.open {
    background: rgba(248, 81, 73, 0.12);
    color: var(--red);
  }

  .pagination {
    display: flex; align-items: center; justify-content: center;
    gap: 16px; margin-top: 20px;
  }
  .pagination button {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 6px 12px; color: var(--text); font-size: 13px;
  }
  .pagination button:disabled { opacity: 0.4; cursor: default; }
  .pagination span { color: var(--muted); font-size: 13px; }
</style>
