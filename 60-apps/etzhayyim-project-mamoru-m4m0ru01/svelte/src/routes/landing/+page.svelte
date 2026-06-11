<svelte:head><title>mamoru — git secret guardian</title></svelte:head>

<div class="lp">
  <!-- Hero -->
  <section class="hero">
    <div class="hero-badge">GitHub Secret Scanning Partner</div>
    <h1 class="hero-title">
      <span class="kanji">守</span><br />
      Git Secret Guardian
    </h1>
    <p class="hero-sub">
      Finds leaked API keys and credentials in public GitHub repositories
      before attackers can use them.
    </p>
    <div class="hero-cta">
      <a href="/" class="btn-primary">Open Dashboard</a>
      <a href="#how-it-works" class="btn-ghost">How it works</a>
    </div>
  </section>

  <!-- Stats row -->
  <div class="stats-row">
    <div class="stat">
      <span class="stat-num">All</span>
      <span class="stat-label">Public GitHub repos scanned</span>
    </div>
    <div class="stat-divider"></div>
    <div class="stat">
      <span class="stat-num">Real-time</span>
      <span class="stat-label">Alerts on push &amp; publicize</span>
    </div>
    <div class="stat-divider"></div>
    <div class="stat">
      <span class="stat-num">ECDSA-P256</span>
      <span class="stat-label">GitHub Partner verification</span>
    </div>
    <div class="stat-divider"></div>
    <div class="stat">
      <span class="stat-num">SHA-256</span>
      <span class="stat-label">Raw tokens never stored</span>
    </div>
  </div>

  <!-- How it works -->
  <section class="section" id="how-it-works">
    <h2 class="section-title">Three coverage layers</h2>
    <div class="cards">
      <div class="card">
        <div class="card-icon push-icon">⚡</div>
        <h3>Push webhooks</h3>
        <p>
          Every <code>git push</code> to repositories with the mamoru GitHub App
          triggers an incremental diff scan. New secrets are detected within
          seconds of being committed.
        </p>
        <div class="card-tag">Installed repos</div>
      </div>

      <div class="card">
        <div class="card-icon pub-icon">🌐</div>
        <h3>Repository publicized</h3>
        <p>
          When a previously private repository is made public, mamoru fires a
          full commit-history scan — catching secrets that were committed while
          the repo was private.
        </p>
        <div class="card-tag">All repos going public</div>
      </div>

      <div class="card highlight-card">
        <div class="card-badge">GitHub Partner</div>
        <div class="card-icon partner-icon">🔐</div>
        <h3>Secret Scanning Partner Program</h3>
        <p>
          GitHub scans every public push across all of GitHub and notifies
          registered partners when their token patterns are found. mamoru
          verifies each alert with ECDSA-NIST-P256V1-SHA256 and runs a
          live validity probe.
        </p>
        <div class="card-tag">All public GitHub repos</div>
      </div>
    </div>
  </section>

  <!-- Pipeline -->
  <section class="section">
    <h2 class="section-title">Detection pipeline</h2>
    <div class="pipeline">
      <div class="pipe-step">
        <div class="pipe-num">1</div>
        <div class="pipe-body">
          <h4>Receive alert</h4>
          <p>Webhook or Partner Program POST. HMAC / ECDSA verified at edge.</p>
        </div>
      </div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step">
        <div class="pipe-num">2</div>
        <div class="pipe-body">
          <h4>Hash &amp; forward</h4>
          <p>Raw token SHA-256 hashed by CF Worker. Raw value forwarded over internal HMAC channel only.</p>
        </div>
      </div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step">
        <div class="pipe-num">3</div>
        <div class="pipe-body">
          <h4>Validity probe</h4>
          <p>LangGraph pod probes AWS STS / GitHub API. Scores: valid 900, indeterminate 600, invalid 100 permille.</p>
        </div>
      </div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step">
        <div class="pipe-num">4</div>
        <div class="pipe-body">
          <h4>Persist &amp; notify</h4>
          <p>Incident written to RisingWave. Slack notification on severity ≥ 600 permille.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Detectors -->
  <section class="section">
    <h2 class="section-title">Secret detectors</h2>
    <div class="detectors">
      {#each detectors as d}
        <div class="detector">
          <span class="detector-dot" style="background:{d.color}"></span>
          <div>
            <div class="detector-name">{d.name}</div>
            <code class="detector-pattern">{d.pattern}</code>
          </div>
          <span class="detector-sev" style="color:{d.color}">{d.sev}</span>
        </div>
      {/each}
    </div>
  </section>

  <!-- Architecture -->
  <section class="section">
    <h2 class="section-title">Architecture</h2>
    <div class="arch-box">
      <pre class="arch-diagram">GitHub (all public repos)
  ├─ push webhook              → POST /webhook/github
  ├─ repository.publicized     → POST /webhook/github  (action=publicized)
  └─ Secret Scanning Partner   → POST /webhook/github-secret-scanning
          ↓
CF Worker  mamoru.etzhayyim.com  (L3 Dispatcher, stateless)
          ↓  x-internal-trust HMAC
bpmn-dispatcher  (K8s ClusterIP)
          ↓  NSID routing
mamoru LangGraph pod  (Granian ASGI, mitama-udf)
          ↓
RisingWave  (vertex_mamoru_incident / occurrence)
          ↓
Slack webhook</pre>
    </div>
    <div class="arch-notes">
      <div class="note">
        <span class="note-title">Edge</span>
        Cloudflare Worker — stateless, zero DB writes, HMAC/ECDSA auth.
      </div>
      <div class="note">
        <span class="note-title">Pod</span>
        Python LangGraph 9-node pipeline on K8s (Vultr VKE, namespace <code>mitama-udf</code>).
      </div>
      <div class="note">
        <span class="note-title">Storage</span>
        RisingWave streaming DB on Vultr + Backblaze B2. Tokens stored as SHA-256 hash only.
      </div>
    </div>
  </section>

  <!-- CTA -->
  <section class="cta-section">
    <h2>Secure your secrets now</h2>
    <p>Open the dashboard to view incidents, scan commits, and manage resolutions.</p>
    <a href="/" class="btn-primary btn-large">Open Dashboard →</a>
  </section>
</div>

<script lang="ts">
  const detectors = [
    { name: "etzhayyim API Key",       pattern: "sk_live_[A-Za-z0-9]{32,}", sev: "900‰", color: "var(--red)" },
    { name: "AWS Access Key ID",  pattern: "AKIA[0-9A-Z]{16}",         sev: "900‰", color: "var(--red)" },
    { name: "AWS Secret Key",     pattern: "aws_secret_access_key",     sev: "900‰", color: "var(--red)" },
    { name: "GitHub Token",       pattern: "gh[pouse]_[A-Za-z0-9]{36}", sev: "800‰", color: "var(--orange)" },
    { name: "High-Entropy String",pattern: "Shannon entropy ≥ 4.5",     sev: "500‰", color: "var(--yellow)" },
  ];
</script>

<style>
  .lp {
    max-width: 900px;
    margin: 0 auto;
  }

  /* Hero */
  .hero {
    text-align: center;
    padding: 72px 24px 56px;
  }
  .hero-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    border: 1px solid var(--border);
    background: rgba(56, 139, 253, 0.1);
    color: var(--blue);
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.3px;
    margin-bottom: 24px;
  }
  .hero-title {
    font-size: clamp(40px, 8vw, 72px);
    font-weight: 700;
    line-height: 1.05;
    letter-spacing: -1.5px;
    margin-bottom: 20px;
  }
  .kanji {
    color: var(--red);
    font-size: 1.2em;
  }
  .hero-sub {
    font-size: 18px;
    color: var(--muted);
    max-width: 500px;
    margin: 0 auto 36px;
    line-height: 1.6;
  }
  .hero-cta {
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
  }
  .btn-primary {
    display: inline-block;
    background: var(--red);
    color: #fff;
    border: none;
    padding: 10px 22px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    transition: opacity 0.15s;
    text-decoration: none;
  }
  .btn-primary:hover { opacity: 0.85; }
  .btn-primary.btn-large { padding: 13px 28px; font-size: 15px; }
  .btn-ghost {
    display: inline-block;
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
    padding: 10px 22px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    transition: color 0.15s, border-color 0.15s;
    text-decoration: none;
  }
  .btn-ghost:hover { color: var(--text); border-color: var(--text); }

  /* Stats */
  .stats-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    flex-wrap: wrap;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 72px;
  }
  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0 28px;
    text-align: center;
  }
  .stat-num {
    font-size: 20px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 4px;
  }
  .stat-label {
    font-size: 12px;
    color: var(--muted);
  }
  .stat-divider {
    width: 1px;
    height: 40px;
    background: var(--border);
  }

  /* Sections */
  .section {
    margin-bottom: 72px;
  }
  .section-title {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 28px;
    letter-spacing: -0.3px;
  }

  /* Cards */
  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    position: relative;
  }
  .highlight-card {
    border-color: rgba(56, 139, 253, 0.4);
    background: linear-gradient(135deg, rgba(56,139,253,0.06) 0%, var(--surface) 60%);
  }
  .card-badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    background: rgba(56,139,253,0.15);
    color: var(--blue);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 12px;
  }
  .card-icon {
    font-size: 28px;
    margin-bottom: 14px;
  }
  .card h3 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 10px;
  }
  .card p {
    font-size: 13px;
    color: var(--muted);
    line-height: 1.6;
    margin-bottom: 16px;
  }
  .card-tag {
    display: inline-block;
    font-size: 11px;
    color: var(--muted);
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 2px 8px;
  }

  /* Pipeline */
  .pipeline {
    display: flex;
    align-items: flex-start;
    gap: 0;
    flex-wrap: wrap;
  }
  .pipe-step {
    display: flex;
    gap: 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px;
    flex: 1;
    min-width: 160px;
  }
  .pipe-num {
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: rgba(248,81,73,0.15);
    border: 1px solid rgba(248,81,73,0.3);
    color: var(--red);
    font-size: 13px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .pipe-body h4 {
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 6px;
  }
  .pipe-body p {
    font-size: 12px;
    color: var(--muted);
    line-height: 1.5;
  }
  .pipe-arrow {
    align-self: center;
    color: var(--border);
    font-size: 20px;
    padding: 0 6px;
    flex-shrink: 0;
  }

  /* Detectors */
  .detectors {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .detector {
    display: flex;
    align-items: center;
    gap: 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
  }
  .detector-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .detector-name {
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 3px;
  }
  .detector-pattern {
    font-size: 11px;
    color: var(--muted);
    font-family: "SFMono-Regular", Consolas, monospace;
  }
  .detector-sev {
    margin-left: auto;
    font-size: 13px;
    font-weight: 700;
    font-family: monospace;
  }

  /* Architecture */
  .arch-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 24px;
    margin-bottom: 20px;
    overflow-x: auto;
  }
  .arch-diagram {
    font-family: "SFMono-Regular", Consolas, monospace;
    font-size: 12px;
    color: var(--muted);
    line-height: 1.7;
    white-space: pre;
  }
  .arch-notes {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }
  .note {
    flex: 1;
    min-width: 200px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 16px;
    font-size: 12px;
    color: var(--muted);
    line-height: 1.5;
  }
  .note-title {
    font-weight: 600;
    color: var(--text);
    display: block;
    margin-bottom: 4px;
    font-size: 13px;
  }
  .note code {
    font-family: monospace;
    font-size: 11px;
    color: var(--blue);
  }

  /* CTA section */
  .cta-section {
    text-align: center;
    padding: 64px 24px;
    border-top: 1px solid var(--border);
    margin-top: 32px;
  }
  .cta-section h2 {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 12px;
  }
  .cta-section p {
    color: var(--muted);
    font-size: 15px;
    margin-bottom: 28px;
  }
</style>
