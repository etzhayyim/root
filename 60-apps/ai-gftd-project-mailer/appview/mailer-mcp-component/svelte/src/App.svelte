<script lang="ts">
  import { onMount } from 'svelte'

  // ── Types ────────────────────────────────────────────────────────────

  interface Email {
    messageId: string
    fromAddress: string
    toLocal: string
    subject: string
    bodyText: string
    receivedAtMs: number
    status: string
  }

  interface Stats {
    emails: number
    bindings: number
    ts: string
  }

  // ── State ─────────────────────────────────────────────────────────────

  let emails = $state<Email[]>([])
  let selected = $state<Email | null>(null)
  let stats = $state<Stats>({ emails: 0, bindings: 0, ts: '' })
  let loading = $state(true)
  let error = $state('')
  let tab = $state<'inbox' | 'bindings'>('inbox')

  // ── Helpers ───────────────────────────────────────────────────────────

  function formatDate(ms: number): string {
    if (!ms) return '—'
    const d = new Date(ms)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    if (diff < 60_000) return 'just now'
    if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
    return d.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' })
  }

  function initials(addr: string): string {
    const local = addr.split('@')[0] ?? addr
    return local.slice(0, 2).toUpperCase()
  }

  // ── Data fetching ─────────────────────────────────────────────────────

  async function loadEmails(): Promise<void> {
    loading = true
    error = ''
    try {
      const [emailsResp, statsResp] = await Promise.all([
        fetch('/api/emails?limit=50'),
        fetch('/api/stats'),
      ])
      if (!emailsResp.ok) throw new Error(`${emailsResp.status}`)
      const emailsData = await emailsResp.json() as { items: Email[] }
      emails = emailsData.items ?? []
      if (statsResp.ok) {
        const s = await statsResp.json() as Stats
        stats = s
      }
    } catch (e) {
      error = String(e)
    } finally {
      loading = false
    }
  }

  onMount(() => { void loadEmails() })
</script>

<div class="app">
  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="logo">
        <span class="logo-icon">✉</span>
        <span class="logo-text">Mailer</span>
      </div>
      <div class="stats-row">
        <span class="stat-badge">{stats.emails} emails</span>
        <span class="stat-badge">{stats.bindings} DIDs</span>
      </div>
    </div>

    <nav class="nav">
      <button
        class="nav-item"
        class:active={tab === 'inbox'}
        onclick={() => { tab = 'inbox'; selected = null }}
      >
        <span class="nav-icon">📥</span>
        <span>Inbox</span>
        {#if emails.length > 0}
          <span class="badge">{emails.length}</span>
        {/if}
      </button>
      <button
        class="nav-item"
        class:active={tab === 'bindings'}
        onclick={() => { tab = 'bindings'; selected = null }}
      >
        <span class="nav-icon">🔗</span>
        <span>DID Bindings</span>
      </button>
    </nav>

    <div class="sidebar-footer">
      <div class="domain-badge">*@gftd.ai</div>
      <div class="subtitle">DID email platform</div>
    </div>
  </aside>

  <!-- Main content -->
  <main class="main">
    {#if tab === 'inbox'}
      <!-- Email list -->
      <div class="list-pane" class:has-selected={selected !== null}>
        <div class="pane-header">
          <h2>Inbox</h2>
          <button class="refresh-btn" onclick={loadEmails} disabled={loading}>
            {loading ? '⟳' : '↻'}
          </button>
        </div>

        {#if loading}
          <div class="loading">
            {#each Array(5) as _, i (i)}
              <div class="skeleton-row"></div>
            {/each}
          </div>
        {:else if error}
          <div class="error-state">
            <span class="error-icon">⚠</span>
            <p>{error}</p>
            <button onclick={loadEmails}>Retry</button>
          </div>
        {:else if emails.length === 0}
          <div class="empty-state">
            <span class="empty-icon">📭</span>
            <p>No emails yet</p>
            <p class="hint">Send an email to <code>you@gftd.ai</code> to get started</p>
          </div>
        {:else}
          <ul class="email-list">
            {#each emails as email (email.messageId)}
              <li>
                <button
                  class="email-row"
                  class:selected={selected?.messageId === email.messageId}
                  onclick={() => { selected = email }}
                >
                  <div class="avatar">{initials(email.fromAddress)}</div>
                  <div class="email-meta">
                    <div class="email-from">{email.fromAddress}</div>
                    <div class="email-subject">{email.subject || '(no subject)'}</div>
                    <div class="email-preview">{(email.bodyText ?? '').slice(0, 80)}</div>
                  </div>
                  <div class="email-time">{formatDate(email.receivedAtMs)}</div>
                </button>
              </li>
            {/each}
          </ul>
        {/if}
      </div>

      <!-- Email detail -->
      {#if selected}
        <div class="detail-pane">
          <div class="detail-header">
            <button class="back-btn" onclick={() => { selected = null }}>←</button>
            <h3 class="detail-subject">{selected.subject || '(no subject)'}</h3>
          </div>
          <div class="detail-meta">
            <div class="meta-row">
              <span class="meta-label">From</span>
              <span class="meta-value">{selected.fromAddress}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">To</span>
              <span class="meta-value">{selected.toLocal}@gftd.ai</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">Received</span>
              <span class="meta-value">{new Date(selected.receivedAtMs).toLocaleString()}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">Status</span>
              <span class="status-pill">{selected.status}</span>
            </div>
          </div>
          <div class="detail-body">
            <pre>{selected.bodyText}</pre>
          </div>
        </div>
      {:else}
        <div class="detail-placeholder">
          <span>Select an email to read</span>
        </div>
      {/if}

    {:else}
      <!-- Bindings tab placeholder -->
      <div class="bindings-view">
        <div class="pane-header">
          <h2>DID Bindings</h2>
        </div>
        <div class="empty-state">
          <span class="empty-icon">🔗</span>
          <p>Email → DID mappings</p>
          <p class="hint">Each sender email is auto-mapped to a path-based DID under <code>ml1nb0nd.gftd.ai</code></p>
        </div>
      </div>
    {/if}
  </main>
</div>

<style>
  :global(*, *::before, *::after) { box-sizing: border-box; }
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0a0a0a;
    color: #e8e8e8;
    height: 100dvh;
    overflow: hidden;
  }

  .app {
    display: flex;
    height: 100dvh;
  }

  /* Sidebar */
  .sidebar {
    width: 220px;
    flex-shrink: 0;
    background: #111;
    border-right: 1px solid #222;
    display: flex;
    flex-direction: column;
    padding: 0;
  }

  .sidebar-header {
    padding: 20px 16px 12px;
    border-bottom: 1px solid #222;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
  }

  .logo-icon { font-size: 18px; }
  .logo-text { font-size: 16px; font-weight: 700; color: #fff; }

  .stats-row { display: flex; gap: 6px; flex-wrap: wrap; }

  .stat-badge {
    font-size: 11px;
    padding: 2px 8px;
    background: #1e1e1e;
    border: 1px solid #333;
    border-radius: 999px;
    color: #888;
  }

  .nav { padding: 8px 0; flex: 1; }

  .nav-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 16px;
    background: none;
    border: none;
    color: #aaa;
    font-size: 14px;
    cursor: pointer;
    text-align: left;
    border-radius: 0;
    transition: background 0.1s, color 0.1s;
    position: relative;
  }

  .nav-item:hover { background: #1a1a1a; color: #e8e8e8; }
  .nav-item.active { background: #1e2a3a; color: #60a5fa; }

  .nav-icon { font-size: 15px; }

  .badge {
    margin-left: auto;
    font-size: 11px;
    background: #1d4ed8;
    color: #93c5fd;
    padding: 1px 7px;
    border-radius: 999px;
  }

  .sidebar-footer {
    padding: 12px 16px;
    border-top: 1px solid #222;
  }

  .domain-badge {
    font-size: 12px;
    font-family: 'Menlo', 'Monaco', monospace;
    color: #60a5fa;
    margin-bottom: 2px;
  }

  .subtitle { font-size: 11px; color: #555; }

  /* Main */
  .main {
    flex: 1;
    display: flex;
    overflow: hidden;
  }

  /* List pane */
  .list-pane {
    width: 100%;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #222;
    overflow: hidden;
    transition: width 0.2s;
  }

  .list-pane.has-selected { width: 360px; flex-shrink: 0; }

  .pane-header {
    padding: 16px 20px;
    border-bottom: 1px solid #222;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .pane-header h2 { margin: 0; font-size: 15px; font-weight: 600; }

  .refresh-btn {
    background: none;
    border: 1px solid #333;
    color: #888;
    border-radius: 6px;
    width: 30px;
    height: 30px;
    cursor: pointer;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.1s;
  }

  .refresh-btn:hover { color: #60a5fa; border-color: #60a5fa; }
  .refresh-btn:disabled { opacity: 0.4; cursor: default; }

  /* Loading skeletons */
  .loading { padding: 8px; display: flex; flex-direction: column; gap: 4px; }

  .skeleton-row {
    height: 72px;
    background: linear-gradient(90deg, #1a1a1a 25%, #222 50%, #1a1a1a 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 8px;
  }

  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  /* Error / empty states */
  .error-state, .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    text-align: center;
    gap: 8px;
  }

  .error-icon, .empty-icon { font-size: 40px; margin-bottom: 8px; }
  .error-state p, .empty-state p { margin: 0; color: #888; font-size: 14px; }
  .empty-state .hint { font-size: 12px; color: #555; margin-top: 4px; }
  .empty-state code { font-family: monospace; color: #60a5fa; }

  .error-state button {
    margin-top: 12px;
    padding: 6px 16px;
    background: #1d4ed8;
    color: #fff;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
  }

  /* Email list */
  .email-list {
    list-style: none;
    margin: 0;
    padding: 0;
    overflow-y: auto;
    flex: 1;
  }

  .email-list li { list-style: none; }

  .email-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
    border-bottom: 1px solid #1a1a1a;
    cursor: pointer;
    transition: background 0.1s;
    width: 100%;
    background: none;
    border-left: none;
    border-right: none;
    border-top: none;
    color: inherit;
    text-align: left;
    font: inherit;
  }

  .email-row:hover { background: #141414; }
  .email-row.selected { background: #1e2a3a; }

  .avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #1d4ed8;
    color: #fff;
    font-size: 13px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .email-meta { flex: 1; min-width: 0; }
  .email-from { font-size: 13px; font-weight: 600; color: #e8e8e8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .email-subject { font-size: 13px; color: #ccc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px; }
  .email-preview { font-size: 12px; color: #666; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px; }
  .email-time { font-size: 11px; color: #555; flex-shrink: 0; margin-top: 2px; }

  /* Detail pane */
  .detail-pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .detail-placeholder {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #444;
    font-size: 14px;
  }

  .detail-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px;
    border-bottom: 1px solid #222;
  }

  .back-btn {
    background: none;
    border: 1px solid #333;
    color: #aaa;
    border-radius: 6px;
    width: 30px;
    height: 30px;
    cursor: pointer;
    font-size: 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .back-btn:hover { border-color: #60a5fa; color: #60a5fa; }

  .detail-subject { margin: 0; font-size: 15px; font-weight: 600; flex: 1; }

  .detail-meta {
    padding: 12px 20px;
    border-bottom: 1px solid #1a1a1a;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .meta-row { display: flex; gap: 12px; align-items: baseline; font-size: 13px; }
  .meta-label { color: #555; width: 60px; flex-shrink: 0; }
  .meta-value { color: #ccc; }

  .status-pill {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 999px;
    background: #14532d;
    color: #86efac;
  }

  .detail-body {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }

  .detail-body pre {
    margin: 0;
    font-family: 'Menlo', 'Monaco', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #ccc;
    white-space: pre-wrap;
    word-break: break-word;
  }

  /* Bindings view */
  .bindings-view { flex: 1; display: flex; flex-direction: column; }

  /* Responsive — narrow screens */
  @media (max-width: 640px) {
    .sidebar { width: 56px; }
    .logo-text, .stats-row, .sidebar-footer, .nav-item span:not(.nav-icon), .badge { display: none; }
    .nav-item { justify-content: center; padding: 12px; }
    .list-pane.has-selected { display: none; }
  }
</style>
