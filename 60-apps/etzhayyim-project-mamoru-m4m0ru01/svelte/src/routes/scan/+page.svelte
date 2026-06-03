<script lang="ts">
  import { api } from "$lib/api";

  let repoId = "";
  let commitSha = "";
  let diff = "";
  let scanId = "";
  let loading = false;
  let error = "";

  async function submit() {
    if (!repoId.trim() || !commitSha.trim()) return;
    loading = true; error = ""; scanId = "";
    try {
      const res = await api.scanCommit(repoId.trim(), commitSha.trim(), diff);
      scanId = res.scanId;
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head><title>Manual Scan — mamoru</title></svelte:head>

<div class="page">
  <h1>Manual commit scan</h1>
  <p class="desc">
    Trigger a secret scan for a specific commit. The pod fetches the real diff
    from GitHub API using the installed GitHub App credentials.
  </p>

  <form on:submit|preventDefault={submit}>
    <div class="field">
      <label for="repo">Repository <span class="req">*</span></label>
      <input id="repo" type="text" placeholder="owner/repo-name" bind:value={repoId} />
    </div>
    <div class="field">
      <label for="sha">Commit SHA <span class="req">*</span></label>
      <input id="sha" type="text" placeholder="abc123def456..." bind:value={commitSha} class="mono" />
    </div>
    <div class="field">
      <label for="diff">
        Diff payload <span class="optional">(optional — pod fetches from GitHub if empty)</span>
      </label>
      <textarea id="diff" rows="8" placeholder="Paste raw git diff here…" bind:value={diff}></textarea>
    </div>

    <div class="actions">
      <button type="submit" class="btn-primary" disabled={loading || !repoId || !commitSha}>
        {loading ? "Scanning…" : "Scan commit"}
      </button>
    </div>
  </form>

  {#if error}
    <div class="alert-error">{error}</div>
  {/if}

  {#if scanId}
    <div class="alert-success">
      <strong>Scan started</strong>
      <p>Scan ID: <span class="mono">{scanId}</span></p>
      <p>Results will appear in <a href="/">Incidents</a> once the pipeline completes.</p>
    </div>
  {/if}
</div>

<style>
  h1 { font-size: 20px; font-weight: 600; margin-bottom: 8px; }
  .desc { color: var(--muted); font-size: 13px; margin-bottom: 24px; max-width: 560px; }

  form { display: flex; flex-direction: column; gap: 20px; max-width: 600px; }
  .field { display: flex; flex-direction: column; gap: 6px; }
  label { font-size: 13px; font-weight: 500; }
  .req { color: var(--red); }
  .optional { color: var(--muted); font-weight: 400; font-size: 12px; }

  input, textarea {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 8px 12px;
    color: var(--text); font-size: 13px; font-family: inherit;
    transition: border-color 0.15s;
  }
  input:focus, textarea:focus { outline: none; border-color: var(--blue); }
  textarea { resize: vertical; }
  .mono { font-family: "SFMono-Regular", Consolas, monospace; }

  .actions { margin-top: 4px; }
  .btn-primary {
    background: var(--red); color: #fff; border: none;
    padding: 8px 20px; border-radius: 6px; font-size: 14px; font-weight: 500;
    transition: opacity 0.15s;
  }
  .btn-primary:disabled { opacity: 0.5; cursor: default; }
  .btn-primary:not(:disabled):hover { opacity: 0.85; }

  .alert-error {
    margin-top: 20px;
    background: rgba(248,81,73,0.12); border: 1px solid rgba(248,81,73,0.3);
    border-radius: 8px; padding: 14px; color: var(--red); font-size: 13px;
  }
  .alert-success {
    margin-top: 20px;
    background: rgba(63,185,80,0.10); border: 1px solid rgba(63,185,80,0.3);
    border-radius: 8px; padding: 16px; font-size: 13px;
  }
  .alert-success strong { display: block; margin-bottom: 8px; color: var(--green); }
  .alert-success p { color: var(--muted); margin-bottom: 4px; }
  .alert-success a { color: var(--blue); }
  .alert-success a:hover { text-decoration: underline; }
</style>
