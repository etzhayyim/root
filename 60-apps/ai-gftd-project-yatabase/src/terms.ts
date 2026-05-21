// terms.ts — public terms of service at /terms.
//
// Plain-language draft. Reflects what the service actually does and the
// real liability posture of a small operator. Not a substitute for
// counsel — but it's a real document that a customer can sign.

const EFFECTIVE_DATE = "2026-05-11";
const LAST_UPDATED = "2026-05-11";

export function termsResponse(): Response {
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Terms of service — Yatabase</title>
<meta name="description" content="The contract between you and the operator (etz hayim) when you use yatabase.gftd.ai." />
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
  code{background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:13px}
  a{color:#0ea5e9}
  .callout{background:#fef9c3;border:1px solid #fcd34d;padding:12px 16px;border-radius:8px;font-size:14px;margin:12px 0}
  footer{padding:36px 0 56px;color:#64748b;font-size:12px}
</style>
</head>
<body>

<header>
  <a class="logo" href="/">y<span>at</span>abase</a>
  <nav>
    <a href="/">Home</a>
    <a href="/docs">Docs</a>
    <a href="/privacy">Privacy</a>
    <a href="/status">Status</a>
  </nav>
</header>

<main>

<h1>Terms of service</h1>
<p class="meta">Effective ${EFFECTIVE_DATE} · Last updated ${LAST_UPDATED} · v0.1</p>

<p>
  These Terms govern your use of <strong>yatabase.gftd.ai</strong> (the "Service"), operated by <strong>etz hayim</strong>
  ("Operator"). By signing up — including the anonymous mint at <code>POST /auth/v1/signup</code> — you accept these Terms.
</p>

<div class="callout">
  This is a v0.1 plain-language draft suitable for self-service use. If your team requires a negotiated agreement
  (DPA, MSA, security questionnaire), email <a href="mailto:legal@gftd.ai">legal@gftd.ai</a> before deploying to production.
</div>

<h2>1. The Service</h2>
<p>
  Yatabase is a real-time graph database (Cypher / SPARQL) plus S3-compatible object storage plus an MCP tool surface,
  published at <code>yatabase.gftd.ai</code>. Surfaces and rate limits are documented at <a href="/docs">/docs</a>;
  pricing tiers at <a href="/#pricing">/#pricing</a>.
</p>

<h2>2. Your account</h2>
<ul>
  <li>You may sign up anonymously. The mint endpoint returns a <code>sk_live_yata_*</code> bearer token that
      represents your tenant. Treat it as a credential — anyone with the token can act as you.</li>
  <li>You are responsible for the security of your token. Revoke compromised tokens via
      <code>POST /auth/v1/revoke</code>.</li>
  <li>You may invite teammates by minting additional tokens with <code>POST /auth/v1/invite</code>. All keys minted
      under one <code>org_did</code> share the same plan, billing, and audit log.</li>
  <li>You may use the Service through automated agents, including LLMs and other AI systems, provided those agents
      respect the rate limits and acceptable-use rules below.</li>
</ul>

<h2>3. Acceptable use</h2>
<p>You may not use the Service to:</p>
<ul>
  <li>Violate any applicable law, including export-control, sanctions, telecommunications, copyright, or privacy law.</li>
  <li>Store, generate, or transmit material that depicts CSAM, non-consensual intimate imagery, or active threats of violence.</li>
  <li>Send unsolicited bulk email, SMS, or other "spam" using the email outbox surface or via Resend on your behalf.</li>
  <li>Mine cryptocurrency, run distributed compute attacks, or otherwise consume resources disproportionate to your plan.</li>
  <li>Reverse-engineer, attack, or attempt to bypass quota / authentication on Yatabase or the underlying infrastructure
      (RisingWave, Cloudflare, Backblaze, Vultr).</li>
  <li>Train a competitive graph-database / object-storage product against Yatabase's API responses with the intent of
      reproducing the Service.</li>
  <li>Exfiltrate other tenants' data. Per-tenant isolation is enforced by <code>actor_did</code> + <code>org_did</code>
      RLS. Discovering and reporting an isolation breach in good faith is welcomed and rewarded.</li>
</ul>

<h2>4. Plans, billing, taxes</h2>
<ul>
  <li>The current plan tiers and quotas are at <a href="/#pricing">/#pricing</a> and in
      <code>src/plan-quota.ts PLAN_RULES</code>. Tiers may change with 30 days' notice; existing customers will be
      grandfathered to the lower of (old, new) for the remainder of their billing month.</li>
  <li>Paid plans are charged via Stripe. Payment is in USD; JPY and other currency conversions are handled by
      Stripe at the time of charge.</li>
  <li>Japan customers receive a <strong>適格請求書</strong> (qualified invoice, T9007028460042 — etz hayim) for each
      paid month. Pull the HTML at <code>GET /api/invoice?month=YYYY-MM</code>.</li>
  <li>Sales tax / VAT / GST is handled by Stripe Tax where the Operator is registered for collection. Where it is
      not, you are responsible for self-assessment.</li>
  <li>Hitting your daily quota returns HTTP 429 with a <code>Retry-After</code> header. Your data is not deleted; the
      meter simply resets at 00:00 UTC.</li>
  <li>Subscriptions auto-renew until you cancel via Stripe. Cancellation downgrades you to Free at the next billing
      cycle; data is not deleted by cancellation alone — use <code>/api/account/delete</code> for that.</li>
</ul>

<h2>5. Service availability</h2>
<ul>
  <li><strong>Free tier</strong>: best-effort, no SLA, scheduled maintenance windows may interrupt service without
      notice.</li>
  <li><strong>Starter, Developer, Business</strong>: target 99.5 % monthly uptime measured against
      <a href="/status">/status</a>. No financial credits are offered; service credits may be issued at the Operator's
      discretion.</li>
  <li><strong>Enterprise</strong>: SLA, support hours, and credit schedule are negotiated in a separate written
      agreement.</li>
  <li>The Operator may add, change, or remove individual surfaces (e.g. roadmap items at
      <a href="/docs">/docs</a>) without notice, but will preserve documented behavior of paid-tier surfaces for at
      least 90 days.</li>
</ul>

<h2>6. Your data</h2>
<ul>
  <li>You retain ownership of all data you store in Yatabase. Operator's role is purely as data processor /
      custodian.</li>
  <li>You grant Operator a non-exclusive, royalty-free license to host, copy, transmit, and display your data
      strictly to the extent necessary to provide the Service to you and your authorized users.</li>
  <li>Aggregate, anonymized, statistics derived from Service-wide usage (e.g. "how many tenants use Cypher this
      week") may be shared without restriction. No tenant-identifiable data is included.</li>
  <li>The data-processing terms in <a href="/privacy">/privacy</a> are incorporated into this Agreement by reference.</li>
</ul>

<h2>7. Operator's data</h2>
<p>
  The Service software, schema, the AI-actor system (chikada / tanaka / nishino / sakamoto path-based DIDs), the
  Studio UI, and the documentation surface are owned by the Operator and licensed to you only for the purpose of
  using the Service. You may not redistribute or sublicense them.
</p>

<h2>8. Termination</h2>
<ul>
  <li>You may terminate at any time via <code>POST /api/account/delete</code> with the body <code>{"confirm":"DELETE"}</code>.
      The action is irreversible; the Operator preserves only the legally-required billing-event retention window.</li>
  <li>The Operator may suspend or terminate your account on written notice (or, for material acceptable-use
      violations, immediately) if you breach §3.</li>
  <li>Sections 3, 6, 9, 10, 11, 12 survive termination.</li>
</ul>

<h2>9. Disclaimers</h2>
<p>
  THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
  WITHOUT LIMITATION ANY WARRANTY OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT. THE
  OPERATOR DOES NOT WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED, ERROR-FREE, OR FREE OF MALICIOUS COMPONENTS.
</p>

<h2>10. Limitation of liability</h2>
<p>
  TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT WILL THE OPERATOR'S TOTAL AGGREGATE LIABILITY ARISING
  OUT OF OR RELATING TO THIS AGREEMENT EXCEED THE GREATER OF (i) USD 100 OR (ii) THE FEES YOU ACTUALLY PAID FOR THE
  SERVICE IN THE 12 MONTHS PRECEDING THE CLAIM.
</p>
<p>
  IN NO EVENT WILL THE OPERATOR BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE
  DAMAGES, INCLUDING LOST PROFITS, LOST DATA, OR BUSINESS INTERRUPTION, EVEN IF ADVISED OF THE POSSIBILITY.
</p>
<p>
  Some jurisdictions do not allow the exclusion or limitation of certain damages. In those jurisdictions, the
  Operator's liability is limited to the smallest amount permitted by applicable law.
</p>

<h2>11. Indemnity</h2>
<p>
  You will indemnify and hold the Operator harmless from any third-party claim arising from (a) your data, (b) your
  use of the Service in breach of §3, or (c) your violation of any law or third-party right.
</p>

<h2>12. Governing law &amp; dispute resolution</h2>
<ul>
  <li>This Agreement is governed by the laws of <strong>Japan</strong>, exclusive of conflict-of-law rules.</li>
  <li>Any dispute will be resolved in the <strong>Tokyo District Court</strong>, except either party may seek
      injunctive relief in any court of competent jurisdiction to protect intellectual property or confidential
      information.</li>
  <li>If you are a US-domiciled consumer, you may alternatively pursue claims under the law of your state of
      residence in your local small-claims court.</li>
</ul>

<h2>13. Changes to these Terms</h2>
<p>
  Material changes will be posted at this URL with a new effective date and a one-line note in the changelog. For
  paid plans, material changes that increase your obligations (price, scope, liability) take effect at the start of
  your next billing month and you may cancel before then without penalty.
</p>

<h2>14. Miscellaneous</h2>
<ul>
  <li><strong>Entire agreement.</strong> These Terms plus <a href="/privacy">/privacy</a> are the entire agreement.</li>
  <li><strong>No waiver.</strong> Failure to enforce a provision does not waive it.</li>
  <li><strong>Severability.</strong> If any provision is held unenforceable, the rest remain in effect.</li>
  <li><strong>Assignment.</strong> You may not assign without the Operator's consent (not unreasonably withheld);
      the Operator may assign to a successor entity in a corporate restructuring.</li>
  <li><strong>Notice.</strong> Notices to the Operator: <a href="mailto:legal@gftd.ai">legal@gftd.ai</a>. Notices to
      you: the email associated with your <code>org_did</code>, falling back to a banner on the Studio Console.</li>
  <li><strong>AI Agent disclaimer.</strong> Yatabase is operated end-to-end by an AI-actor system (chikada / tanaka
      / nishino / sakamoto, see <a href="/team">/team</a>). Their drafts and replies are provided for operational
      transparency and do not constitute legal, tax, or professional advice.</li>
</ul>

</main>

<footer>
  <p>© 2026 etz hayim · <a href="/">yatabase.gftd.ai</a> · <a href="/privacy">/privacy</a> · <a href="/status">/status</a></p>
</footer>

</body></html>`;

  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "x-yatabase-surface": "terms",
      "cache-control": "public, max-age=600, s-maxage=3600",
    },
  });
}
