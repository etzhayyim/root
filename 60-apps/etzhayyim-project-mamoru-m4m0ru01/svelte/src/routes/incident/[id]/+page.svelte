<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { api, severityLabel, type IncidentDetail } from "$lib/api";

  let incident: IncidentDetail | null = null;
  let loading = true;
  let error = "";
  let resolving = false;
  let resolveNote = "";
  let showResolve = false;

  $: incidentId = $page.params.id;

  onMount(async () => {
    try {
      incident = await api.getIncident(incidentId);
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  });

  const SEV_COLOR: Record<string, string> = {
    critical: "var(--red)",
    high:     "var(--orange)",
    medium:   "var(--yellow)",
    low:      "var(--blue)",
    info:     "var(--muted)",
  };

  const VALIDITY_COLOR: Record<string, string> = {
    valid:   "var(--red)",
    invalid: "var(--green)",
    unknown: "var(--muted)",
  };

  function fmtDate(iso: string) {
    return new Date(iso).toLocaleString("en", {
      month: "short", day: "numeric", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  }

  async function resolve(resolution: "revoked" | "false_positive" | "accepted_risk") {
    if (!incident) return;
    resolving = true;
    try {
      await api.resolveIncident(incident.incidentId, resolution, resolveNote || undefined);
      await goto("/");
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
      resolving = false;
    }
  }
</script>

<svelte:head><title>{incident ? incident.secretType : "Incident"} — mamoru</title></svelte:head>

<div class="page">
  <nav class="breadcrumb">
    <a href="/">Incidents</a>
    <span>/</span>
    <span>{incidentId.slice(0, 8)}…</span>
  </nav>

  {#if error}
    <div class="alert-error">{error}</div>
  {:else if loading}
    <div class="loading"><div class="spinner"></div> Loading…</div>
  {:else if incident}
    {@const sev = severityLabel(incident.severityPermille)}
    <div class="detail-header">
      <div class="title-row">
        <span class="sev-badge" style="color:{SEV_COLOR[sev]};border-color:{SEV_COLOR[sev]}">{sev}</span>
        <h1>{incident.secretType.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</h1>
      </div>
      <div class="meta-row">
        <span class="meta-item">
          <span class="meta-label">Repo</span>
          <span class="mono">{incident.repoId}</span>
        </span>
        <span class="meta-item">
          <span class="meta-label">Status</span>
          <span class="status-chip" class:open={incident.status === "open"}>{incident.status}</span>
        </span>
        <span class="meta-item">
          <span class="meta-label">Validity</span>
          <span style="color:{VALIDITY_COLOR[incident.validity]}">● {incident.validity}</span>
        </span>
        <span class="meta-item">
          <span class="meta-label">Occurrences</span>
          <span>{incident.occurrenceCount} in {incident.commitCount} commits</span>
        </span>
        <span class="meta-item">
          <span class="meta-label">First seen</span>
          <span>{fmtDate(incident.firstSeenAt)}</span>
        </span>
        <span class="meta-item">
          <span class="meta-label">Last seen</span>
          <span>{fmtDate(incident.lastSeenAt)}</span>
        </span>
      </div>
    </div>

    <!-- Severity bar -->
    <div class="sev-section">
      <div class="sev-header">
        <span>Severity score</span>
        <span style="color:{SEV_COLOR[sev]};font-weight:600">{(incident.severityPermille / 10).toFixed(0)}/100</span>
      </div>
      <div class="sev-track">
        <div
          class="sev-fill"
          style="width:{incident.severityPermille / 10}%;background:{SEV_COLOR[sev]}"
        ></div>
      </div>
    </div>

    <!-- Occurrences -->
    <section class="section">
      <h2>Occurrences ({incident.occurrences.length})</h2>
      <div class="occurrences">
        {#each incident.occurrences as occ (occ.occurrenceId)}
          <div class="occurrence-card">
            <div class="occ-row">
              <span class="occ-label">Commit</span>
              <span class="mono hash">{occ.commitSha.slice(0, 12)}</span>
            </div>
            <div class="occ-row">
              <span class="occ-label">File</span>
              <span class="mono path">{occ.filePath}{occ.lineNumber != null ? `:${occ.lineNumber}` : ""}</span>
            </div>
            <div class="occ-row">
              <span class="occ-label">Secret hash</span>
              <span class="mono muted">{occ.secretHash.slice(0, 16)}…</span>
            </div>
            <div class="occ-row">
              <span class="occ-label">Detected</span>
              <span class="muted">{fmtDate(occ.detectedAt)}</span>
            </div>
          </div>
        {/each}
      </div>
    </section>

    <!-- Actions -->
    {#if incident.status === "open"}
      <section class="section">
        <h2>Resolve incident</h2>
        <div class="resolve-area">
          <textarea
            placeholder="Optional note (e.g. revocation PR link, reason)…"
            bind:value={resolveNote}
            rows="3"
          ></textarea>
          <div class="resolve-buttons">
            <button
              class="resolve-btn revoked"
              disabled={resolving}
              on:click={() => resolve("revoked")}
            >
              ✓ Secret revoked
            </button>
            <button
              class="resolve-btn fp"
              disabled={resolving}
              on:click={() => resolve("false_positive")}
            >
              ✕ False positive
            </button>
            <button
              class="resolve-btn risk"
              disabled={resolving}
              on:click={() => resolve("accepted_risk")}
            >
              ⚡ Accept risk
            </button>
          </div>
        </div>
      </section>
    {/if}
  {/if}
</div>

<style>
  .breadcrumb {
    display: flex; gap: 8px; align-items: center;
    color: var(--muted); font-size: 13px; margin-bottom: 20px;
  }
  .breadcrumb a { color: var(--blue); }
  .breadcrumb a:hover { text-decoration: underline; }

  .alert-error {
    background: rgba(248,81,73,0.12); border: 1px solid rgba(248,81,73,0.3);
    border-radius: 8px; padding: 14px; color: var(--red); font-size: 13px;
  }
  .loading { display: flex; align-items: center; gap: 10px; padding: 48px; color: var(--muted); }
  .spinner {
    width: 16px; height: 16px;
    border: 2px solid var(--border); border-top-color: var(--blue);
    border-radius: 50%; animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .detail-header {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 20px; margin-bottom: 16px;
  }
  .title-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
  h1 { font-size: 18px; font-weight: 600; }
  .sev-badge {
    padding: 3px 10px; border-radius: 12px; border: 1px solid;
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;
  }
  .meta-row { display: flex; flex-wrap: wrap; gap: 20px; }
  .meta-item { display: flex; flex-direction: column; gap: 2px; }
  .meta-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }

  .mono { font-family: "SFMono-Regular", Consolas, monospace; font-size: 12px; }
  .muted { color: var(--muted); }
  .status-chip {
    display: inline-block; padding: 2px 8px; border-radius: 12px;
    font-size: 11px; font-weight: 500; background: rgba(255,255,255,0.06); color: var(--muted);
  }
  .status-chip.open { background: rgba(248,81,73,0.12); color: var(--red); }

  .sev-section {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 16px; margin-bottom: 16px;
  }
  .sev-header { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 10px; }
  .sev-track {
    height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden;
  }
  .sev-fill { height: 100%; border-radius: 3px; transition: width 0.4s; }

  .section { margin-bottom: 24px; }
  h2 { font-size: 14px; font-weight: 600; color: var(--muted); margin-bottom: 12px;
       text-transform: uppercase; letter-spacing: 0.5px; }

  .occurrences { display: flex; flex-direction: column; gap: 10px; }
  .occurrence-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 14px;
    display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
  }
  .occ-row { display: flex; flex-direction: column; gap: 2px; }
  .occ-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.4px; }
  .hash { color: var(--blue); }
  .path { color: var(--text); word-break: break-all; }

  .resolve-area { display: flex; flex-direction: column; gap: 12px; }
  textarea {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 10px; color: var(--text); font-size: 13px;
    resize: vertical; font-family: inherit;
  }
  textarea:focus { outline: none; border-color: var(--blue); }
  .resolve-buttons { display: flex; gap: 10px; flex-wrap: wrap; }
  .resolve-btn {
    padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 500;
    border: 1px solid; transition: opacity 0.15s;
  }
  .resolve-btn:disabled { opacity: 0.5; cursor: default; }
  .resolve-btn.revoked { background: rgba(63,185,80,0.12); color: var(--green); border-color: var(--green); }
  .resolve-btn.fp { background: rgba(139,148,158,0.12); color: var(--muted); border-color: var(--border); }
  .resolve-btn.risk { background: rgba(210,153,34,0.12); color: var(--yellow); border-color: var(--yellow); }
  .resolve-btn:not(:disabled):hover { opacity: 0.8; }
</style>
