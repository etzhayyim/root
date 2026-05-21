// privacy.ts — public privacy policy at /privacy.
//
// Reflects what the service actually does, not boilerplate. Each
// retention window is sourced from a specific table + statute. Each
// "right" maps to a real endpoint already shipped on yatabase.
//
// Operator is `etz hayim`; Gftd Japan株式会社 (T9007028460042) is the
// Japan-side vendor of record for 適格請求書 invoicing only.

const EFFECTIVE_DATE = "2026-05-11";
const LAST_UPDATED = "2026-05-11";

export function privacyResponse(): Response {
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Privacy policy — Yatabase</title>
<meta name="description" content="What yatabase.gftd.ai collects, how long we keep it, who else sees it, and how you exercise your CCPA / GDPR / 改正個人情報保護法 rights." />
<style>
  body{margin:0;font:15px/1.65 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;background:#fafafa}
  header,main,footer{max-width:780px;margin:0 auto;padding:0 24px}
  header{padding:28px 24px 12px;display:flex;align-items:center;justify-content:space-between}
  .logo{font-weight:700;font-size:20px;color:inherit;text-decoration:none}
  .logo span{color:#0ea5e9}
  nav a{color:#334155;text-decoration:none;margin-left:18px;font-size:14px}
  nav a:hover{color:#0ea5e9}
  main{padding:8px 24px}
  h1{font-size:32px;letter-spacing:-.02em;margin:8px 0 4px}
  .meta{font-size:13px;color:#64748b;margin:0 0 24px}
  h2{font-size:20px;letter-spacing:-.01em;margin:32px 0 8px;padding-top:14px;border-top:1px solid #e2e8f0}
  h2:first-of-type{border-top:0;padding-top:0}
  h3{font-size:16px;margin:18px 0 6px}
  p{margin:8px 0}
  ul{padding-left:22px}
  li{margin:4px 0}
  table{width:100%;border-collapse:collapse;font-size:14px;margin:8px 0 16px;background:#fff;border-radius:8px;overflow:hidden}
  th,td{padding:8px 12px;text-align:left;border-bottom:1px solid #e2e8f0;vertical-align:top}
  th{font-weight:600;color:#475569;font-size:12px;text-transform:uppercase;letter-spacing:.05em;background:#f8fafc}
  tr:last-child td{border-bottom:0}
  code{background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:13px}
  a{color:#0ea5e9}
  footer{padding:36px 0 56px;color:#64748b;font-size:12px}
</style>
</head>
<body>

<header>
  <a class="logo" href="/">y<span>at</span>abase</a>
  <nav>
    <a href="/">Home</a>
    <a href="/docs">Docs</a>
    <a href="/terms">Terms</a>
    <a href="/status">Status</a>
  </nav>
</header>

<main>

<h1>Privacy policy</h1>
<p class="meta">Effective ${EFFECTIVE_DATE} · Last updated ${LAST_UPDATED}</p>

<h2>1. Who we are</h2>
<p>
  <strong>yatabase.gftd.ai</strong> ("Yatabase", "the service") is operated by <strong>etz hayim</strong>
  (運営法人), a religious organization / blockchain-registered entity. <strong>Gftd Japan株式会社</strong>
  (Japan corporate ID T9007028460042 — 適格請求書登録番号) is the Japan-side vendor of record for tax-invoice
  issuance only. This policy applies to the entire <code>yatabase.gftd.ai</code> domain and every
  endpoint listed in <a href="/_app/meta">/_app/meta</a>.
</p>

<h2>2. What we collect</h2>
<p>The service is opt-in and minimal. Concretely, when you use Yatabase we record the following:</p>
<table>
  <thead><tr><th>Field</th><th>Source</th><th>Where it lives</th></tr></thead>
  <tbody>
    <tr>
      <td><strong>orgDid</strong> (e.g. <code>did:web:t-xxxxx.yata-tenant.gftd.ai</code>)</td>
      <td>Generated server-side when you POST <code>/auth/v1/signup</code>.</td>
      <td><code>vertex_api_key.owner_did</code></td>
    </tr>
    <tr>
      <td>API key SHA-256 hash + first 13 chars (<code>sk_live_yata_</code>)</td>
      <td>Mint side-effect of signup. The raw key is shown to you once and never persisted in plaintext.</td>
      <td><code>vertex_api_key</code></td>
    </tr>
    <tr>
      <td>Email + display name <em>(optional)</em></td>
      <td>Whatever you choose to send in the signup body.</td>
      <td><code>vertex_email_outbox</code> (recipient_email, recipient_name)</td>
    </tr>
    <tr>
      <td>Billing events (per-API-call qty + metric)</td>
      <td>Every authenticated request emits one row.</td>
      <td><code>vertex_billing_event</code></td>
    </tr>
    <tr>
      <td>Audit log (org_did, surface, method, path, status, latency, hashed IP, UA hint)</td>
      <td>Recorded fire-and-forget after every authenticated call.</td>
      <td><code>vertex_audit_log</code></td>
    </tr>
    <tr>
      <td>Plan tier + Stripe customer/subscription IDs</td>
      <td>Set when you complete Stripe Checkout.</td>
      <td><code>vertex_org_plan</code></td>
    </tr>
    <tr>
      <td>Object storage data</td>
      <td>Whatever you PUT to <code>/storage/v1/object/{bucket}/{key}</code> or <code>/s3/...</code>.</td>
      <td>Backblaze B2 (content-addressed, SHA-256 keyed)</td>
    </tr>
    <tr>
      <td>Graph data</td>
      <td>Whatever you write via Cypher / SPARQL / XRPC.</td>
      <td>RisingWave Postgres on Vultr LAX (per-tenant schema <code>yata_*</code>)</td>
    </tr>
  </tbody>
</table>
<p>
  We do <strong>not</strong> collect: full IP addresses (we hash them with SHA-256 and keep only the first 16 hex chars
  for abuse-correlation), browser fingerprints, third-party tracking pixels, advertising IDs, or location data beyond
  Cloudflare's standard <code>cf-iata</code> hint. The service sets no first-party cookies. The Studio console uses
  <code>localStorage</code> on your device only.
</p>

<h2>3. Why we collect it (lawful basis)</h2>
<ul>
  <li><strong>Performance of contract</strong> (GDPR Art 6(1)(b)): orgDid, billing events, plan tier, audit log, your data.</li>
  <li><strong>Legal obligation</strong> (GDPR Art 6(1)(c)): retention of <code>vertex_billing_event</code> for 7 years per 法人税法 §126 / IRS §6001.</li>
  <li><strong>Legitimate interest</strong> (GDPR Art 6(1)(f)): hashed-IP audit log for abuse prevention, scoped to 90 days.</li>
  <li><strong>Consent</strong>: optional email + name on signup; you can omit them entirely.</li>
</ul>

<h2>4. Retention</h2>
<table>
  <thead><tr><th>Table</th><th>Retention</th><th>Why</th></tr></thead>
  <tbody>
    <tr><td><code>vertex_billing_event</code></td><td>7 years</td><td>法人税法 §126 (Japan corporate tax) / IRS §6001 (US)</td></tr>
    <tr><td><code>vertex_audit_log</code></td><td>90 days</td><td>GDPR Art 30 records-of-processing minimum + abuse forensics</td></tr>
    <tr><td><code>vertex_email_outbox</code></td><td>1 year</td><td>Delivery troubleshooting; CAN-SPAM record-keeping</td></tr>
    <tr><td><code>vertex_api_key</code></td><td>Until you revoke (<code>POST /auth/v1/revoke</code>)</td><td>Authentication state</td></tr>
    <tr><td><code>vertex_org_plan</code></td><td>3 years after last subscription</td><td>Stripe dispute window + tax</td></tr>
    <tr><td>Tenant schema <code>yata_*</code></td><td>Until you call <code>/api/account/delete</code></td><td>Active account state</td></tr>
    <tr><td>Studio <code>localStorage</code> (your API key, admin key)</td><td>Your device only; we never see it</td><td>—</td></tr>
  </tbody>
</table>

<h2>5. Your rights</h2>
<p>Each right maps to an authenticated endpoint you already have access to with your <code>sk_live_yata_*</code> key.</p>
<table>
  <thead><tr><th>Right</th><th>Statute</th><th>Endpoint</th></tr></thead>
  <tbody>
    <tr><td>Right to know / access / portability</td><td>CCPA §1798.100, GDPR Art 15+20, 改正個人情報保護法 §33</td><td><code>GET /api/export</code></td></tr>
    <tr><td>Right to delete / erasure (irreversible)</td><td>CCPA §1798.105, GDPR Art 17, 改正個人情報保護法 §34-36</td><td><code>POST /api/account/delete</code> with <code>{confirm:"DELETE"}</code></td></tr>
    <tr><td>Right to restrict processing</td><td>GDPR Art 18</td><td>Revoke all keys via <code>/auth/v1/revoke</code>; account stays read-only until renewed.</td></tr>
    <tr><td>Right to object to direct marketing</td><td>CCPA §1798.120, GDPR Art 21, 改正個人情報保護法 §17</td><td>We send no marketing unless you opt in by giving us an email at signup. Reply with "stop" to any operator email.</td></tr>
    <tr><td>Right to lodge a complaint</td><td>GDPR Art 77</td><td>Your local supervisory authority. We will cooperate.</td></tr>
    <tr><td>Records-of-processing inspection</td><td>GDPR Art 30</td><td><code>GET /api/audit</code> returns the last 90 days for your org.</td></tr>
  </tbody>
</table>
<p>
  <strong>Account deletion is irreversible.</strong> The endpoint immediately revokes all keys, marks the plan tier
  <code>deleted</code>, and runs <code>DROP SCHEMA "yata_&lt;hash&gt;" CASCADE</code> on the tenant schema. The 7-year
  billing-event retention is preserved (we are legally required to) but those rows are not associated with any active
  account state and contain no PII beyond <code>org_did</code>.
</p>

<h2>6. Who else sees the data</h2>
<p>We use the following sub-processors. None of them receive plaintext object-storage payloads or graph data beyond what
   their service technically requires:</p>
<table>
  <thead><tr><th>Sub-processor</th><th>Purpose</th><th>Region</th></tr></thead>
  <tbody>
    <tr><td>Cloudflare Inc. (Workers, Hyperdrive, R2 cache)</td><td>Edge HTTP termination, regional cache, durable-object state.</td><td>Global anycast; data flows mostly via PoPs nearest the user.</td></tr>
    <tr><td>Vultr Holdings, LLC (VKE LAX)</td><td>Primary RisingWave Postgres tenancy; runs the per-tenant <code>yata_*</code> schemas.</td><td>Los Angeles, USA.</td></tr>
    <tr><td>Backblaze, Inc. (B2)</td><td>Content-addressed object storage. Files keyed by SHA-256 of payload.</td><td>USA (us-west / us-east).</td></tr>
    <tr><td>Stripe, Inc.</td><td>Payment processing, subscription state, invoice generation. Card data is handled entirely by Stripe — we never see PAN or CVC.</td><td>USA (with EU/JP routing where applicable).</td></tr>
    <tr><td>Resend, Inc. <em>(when configured)</em></td><td>Transactional email delivery (<code>signup-welcome</code>, <code>plan-upgrade</code>, etc.). Operator-side wiring; until then, email rows queue locally and never leave Yatabase.</td><td>USA.</td></tr>
    <tr><td>RunPod, Inc. <em>(via LangGraph)</em></td><td>LLM inference for marketing graph, when active. Receives only the lead's domain + signal text — no tenant data.</td><td>USA.</td></tr>
  </tbody>
</table>
<p>We sign data-processing agreements (DPA) with each sub-processor where the law requires it (GDPR Art 28). We do
  not sell, rent, or share your data with third-party data brokers. The service has no advertising surface.</p>

<h2>7. International transfers</h2>
<p>
  If you access the service from outside the United States, your data will be transferred to the United States for
  processing. We rely on <strong>Standard Contractual Clauses</strong> (EU 2021/914) for EU/EEA transfers and on the
  recipient's compliance with the JP-US APEC CBPR for transfers from Japan. The hashed-IP audit log uses an
  irreversible SHA-256 truncation, so it is not transferable PII under most regimes.
</p>

<h2>8. Security</h2>
<ul>
  <li>All HTTP traffic is TLS 1.3 (Cloudflare-managed certs, automatic rotation).</li>
  <li>API keys are stored as SHA-256 hashes; the raw <code>sk_live_yata_*</code> string is shown once at mint and never persisted.</li>
  <li>Stripe webhook signatures are verified by HMAC SHA-256 with constant-time compare.</li>
  <li>Inter-service trust uses <code>x-internal-trust</code> on a private mesh.</li>
  <li>Tenant isolation is enforced at the SQL layer: every tenant gets a unique RW schema <code>yata_&lt;sha256(orgDid)[:16]&gt;</code> with RLS by <code>actor_did</code> + <code>org_did</code> per ADR-0095.</li>
</ul>

<h2>9. Children</h2>
<p>The service is not directed at children under 16. We do not knowingly collect data from children; if you believe a
  child has signed up, contact us and we will delete the account.</p>

<h2>10. Changes to this policy</h2>
<p>We will post material changes to this URL with a new "Last updated" date and a one-line note in the changelog.
   Material changes that expand the categories of data we collect will require renewed consent for paid plans.</p>

<h2>11. Contact</h2>
<p>
  Privacy requests, DPA requests, supervisory-authority cooperation: reach out to
  <a href="mailto:privacy@gftd.ai">privacy@gftd.ai</a>. We aim to respond within 30 calendar days, the GDPR Art 12(3)
  default.
</p>

</main>

<footer>
  <p>© 2026 etz hayim · <a href="/">yatabase.gftd.ai</a> · <a href="/terms">/terms</a> · <a href="/status">/status</a> · <a href="/.well-known/agent.json">/.well-known/agent.json</a></p>
</footer>

</body></html>`;

  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "x-yatabase-surface": "privacy",
      "cache-control": "public, max-age=600, s-maxage=3600",
    },
  });
}
