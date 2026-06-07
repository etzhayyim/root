// Public Malak thin edge facade. Ad-library intelligence logic runs in AgentGateway MCP + pod-side LangServer.

interface SecretBinding {
  get(): Promise<string>;
}

interface AssetsBinding {
  fetch(req: Request): Promise<Response>;
}

interface R2ObjectBody {
  body: ReadableStream | null;
  httpMetadata?: { contentType?: string };
  customMetadata?: Record<string, string>;
}

interface R2Bucket {
  get(key: string): Promise<R2ObjectBody | null>;
}

interface Env {
  ASSETS?: AssetsBinding;
  YATA_R2?: R2Bucket;
  CACHE_R2?: R2Bucket;
  DISPATCHER_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string | SecretBinding;
  APP_NANOID?: string;
  PUBLIC_MALAK_ARTIFACT_BUCKET?: string;
  PUBLIC_MALAK_ARTIFACT_S3_ENDPOINT?: string;
  PUBLIC_MALAK_ARTIFACT_S3_REGION?: string;
  SS_PUBLIC_MALAK_B2_KEY_ID?: string | SecretBinding;
  SS_PUBLIC_MALAK_B2_APPLICATION_KEY?: string | SecretBinding;
}

interface ExportedHandler<E> {
  fetch(req: Request, env: E): Promise<Response>;
}

const APP = "public-malak";
const NSID_PREFIX = "com.etzhayyim.apps.publicMalak.";

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/campaigns")) {
      return html(dashboardHtml());
    }

    if (url.pathname === "/health" || url.pathname === "/healthz" || url.pathname === "/readyz" || url.pathname === "/_app/meta") {
      return json({
        ok: true,
        actor: "did:web:public-malak.etzhayyim.com",
        nanoid: env.APP_NANOID ?? "pb1ml4k0",
        execution: "edge-proxy+agentgateway-mcp+langserver",
        businessLogic: "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/public_malak_ads.py",
        bpmn: "etzhayyim-root/00-contracts/bpmn/com/etzhayyim/public-malak",
      });
    }

    if (req.method === "GET" && url.pathname.startsWith("/artifacts/")) {
      return artifact(req, env, url);
    }

    const nsid = url.pathname.startsWith("/xrpc/") ? url.pathname.slice("/xrpc/".length) : "";
    if (nsid.startsWith(NSID_PREFIX) && (req.method === "POST" || req.method === "GET")) {
      const body = await bodyWithQuery(req, url);
      if (body.__invalidJson) return json({ error: "InvalidJson" }, 400);
      return proxyToDispatcher(env, nsid, body);
    }

    if (env.ASSETS) return env.ASSETS.fetch(req);
    return json({ error: "NotFound", message: `${APP} not found` }, 404);
  },
} satisfies ExportedHandler<Env>;

async function bodyWithQuery(req: Request, url: URL): Promise<Record<string, unknown>> {
  let body: Record<string, unknown> = {};
  if (req.method === "POST") {
    const text = await req.text();
    try {
      body = text ? (JSON.parse(text) as Record<string, unknown>) : {};
    } catch {
      return { __invalidJson: true };
    }
  }
  url.searchParams.forEach((v, k) => {
    if (!(k in body)) body[k] = v;
  });
  return body;
}

async function artifact(_req: Request, env: Env, url: URL): Promise<Response> {
  const parts = url.pathname.split("/").filter(Boolean);
  const kind = sanitizePathPart(parts[1] ?? "");
  const cid = sanitizePathPart(parts[2] ?? "");
  if (!kind || !cid) return json({ error: "ArtifactPathRequired" }, 400);
  const buckets = [env.CACHE_R2, env.YATA_R2].filter(Boolean) as R2Bucket[];
  const keys = artifactKeys(kind, cid);
  for (const bucket of buckets) {
    for (const key of keys) {
      const obj = await bucket.get(key);
      if (!obj || !obj.body) continue;
      return new Response(obj.body, {
        headers: {
          "content-type": obj.httpMetadata?.contentType || artifactContentType(kind),
          "cache-control": "public, max-age=3600",
          "x-artifact-cid": cid,
          "x-artifact-key": key,
        },
      });
    }
  }

  const b2Resp = await artifactFromS3(env, kind, cid, keys);
  if (b2Resp) return b2Resp;

  return json({ error: "ArtifactNotFound", kind, cid, tried: keys }, 404);
}

function sanitizePathPart(value: string): string {
  return value.replace(/[^a-zA-Z0-9._:-]/g, "").slice(0, 256);
}

function artifactContentType(kind: string): string {
  if (kind === "html") return "text/html; charset=utf-8";
  if (kind === "screenshot") return "image/png";
  if (kind === "har") return "application/json; charset=utf-8";
  return "application/octet-stream";
}

function artifactKeys(kind: string, cid: string): string[] {
  const ext = kind === "html" ? ".html" : kind === "screenshot" ? ".png" : kind === "har" ? ".har" : "";
  return [
    cid,
    `${cid}${ext}`,
    `public-malak/${cid}`,
    `public-malak/${cid}${ext}`,
    `public-malak/${kind}/${cid}`,
    `public-malak/${kind}/${cid}${ext}`,
    `artifacts/${cid}`,
    `artifacts/${cid}${ext}`,
    `artifacts/public-malak/${kind}/${cid}`,
    `artifacts/public-malak/${kind}/${cid}${ext}`,
  ];
}

async function artifactFromS3(env: Env, kind: string, cid: string, keys: string[]): Promise<Response | null> {
  const bucket = (env.PUBLIC_MALAK_ARTIFACT_BUCKET ?? "").trim();
  const endpoint = (env.PUBLIC_MALAK_ARTIFACT_S3_ENDPOINT ?? "").trim().replace(/\/+$/, "");
  const region = (env.PUBLIC_MALAK_ARTIFACT_S3_REGION ?? "us-west-004").trim() || "us-west-004";
  const accessKeyId = await secretValue(env.SS_PUBLIC_MALAK_B2_KEY_ID);
  const secretAccessKey = await secretValue(env.SS_PUBLIC_MALAK_B2_APPLICATION_KEY);
  if (!bucket || !endpoint || !accessKeyId || !secretAccessKey) return null;

  for (const key of keys) {
    const signed = await signedS3GetUrl({ endpoint, bucket, key, region, accessKeyId, secretAccessKey });
    const resp = await fetch(signed, { method: "GET" });
    if (resp.status === 404 || resp.status === 403) continue;
    if (!resp.ok || !resp.body) continue;
    return new Response(resp.body, {
      headers: {
        "content-type": resp.headers.get("content-type") || artifactContentType(kind),
        "cache-control": "public, max-age=3600",
        "x-artifact-cid": cid,
        "x-artifact-key": key,
        "x-artifact-store": "s3",
      },
    });
  }
  return null;
}

async function signedS3GetUrl(opts: {
  endpoint: string;
  bucket: string;
  key: string;
  region: string;
  accessKeyId: string;
  secretAccessKey: string;
}): Promise<string> {
  const base = new URL(opts.endpoint);
  const keyPath = opts.key.split("/").map(encodeURIComponent).join("/");
  const pathname = `/${encodeURIComponent(opts.bucket)}/${keyPath}`;
  const now = amzDate(new Date());
  const date = now.slice(0, 8);
  const credentialScope = `${date}/${opts.region}/s3/aws4_request`;
  const signedHeaders = "host";
  const query = new URLSearchParams({
    "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
    "X-Amz-Credential": `${opts.accessKeyId}/${credentialScope}`,
    "X-Amz-Date": now,
    "X-Amz-Expires": "300",
    "X-Amz-SignedHeaders": signedHeaders,
  });
  const canonicalQuery = [...query.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&");
  const canonicalRequest = [
    "GET",
    pathname,
    canonicalQuery,
    `host:${base.host}\n`,
    signedHeaders,
    "UNSIGNED-PAYLOAD",
  ].join("\n");
  const stringToSign = [
    "AWS4-HMAC-SHA256",
    now,
    credentialScope,
    await sha256Hex(canonicalRequest),
  ].join("\n");
  const signingKey = await awsSigningKey(opts.secretAccessKey, date, opts.region);
  const signature = await hmacHex(signingKey, stringToSign);
  query.set("X-Amz-Signature", signature);
  return `${base.origin}${pathname}?${query.toString()}`;
}

function amzDate(date: Date): string {
  return date.toISOString().replace(/[:-]|\.\d{3}/g, "");
}

async function awsSigningKey(secret: string, date: string, region: string): Promise<ArrayBuffer> {
  const kDate = await hmacBytes(utf8(`AWS4${secret}`), date);
  const kRegion = await hmacBytes(kDate, region);
  const kService = await hmacBytes(kRegion, "s3");
  return hmacBytes(kService, "aws4_request");
}

async function hmacBytes(key: ArrayBuffer | Uint8Array, message: string): Promise<ArrayBuffer> {
  const cryptoKey = await crypto.subtle.importKey("raw", key, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return crypto.subtle.sign("HMAC", cryptoKey, utf8(message));
}

async function hmacHex(key: ArrayBuffer | Uint8Array, message: string): Promise<string> {
  return hex(await hmacBytes(key, message));
}

async function sha256Hex(message: string): Promise<string> {
  return hex(await crypto.subtle.digest("SHA-256", utf8(message)));
}

function utf8(value: string): Uint8Array {
  return new TextEncoder().encode(value);
}

function hex(buf: ArrayBuffer): string {
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function proxyToDispatcher(env: Env, nsid: string, body: Record<string, unknown>): Promise<Response> {
  const base = (env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com").replace(/\/+$/, "");
  const headers: Record<string, string> = { "content-type": "application/json" };
  const trust = await internalTrustSecret(env);
  if (trust) headers["x-internal-trust"] = trust;
  const resp = await fetch(`${base}/xrpc/${nsid}`, { method: "POST", headers, body: JSON.stringify(body) });
  const text = await resp.text();
  return new Response(text, {
    status: resp.status,
    headers: {
      "content-type": resp.headers.get("content-type") ?? "application/json",
      "cache-control": "no-store",
    },
  });
}

async function internalTrustSecret(env: Env): Promise<string> {
  return secretValue(env.DISPATCHER_INTERNAL_SECRET);
}

async function secretValue(binding: string | SecretBinding | undefined): Promise<string> {
  if (!binding) return "";
  try {
    return typeof binding === "string" ? binding : await binding.get();
  } catch {
    return "";
  }
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}

function html(body: string, status = 200): Response {
  return new Response(body, {
    status,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
      "referrer-policy": "same-origin",
    },
  });
}

function dashboardHtml(): string {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Public Malak</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --line: #d9dee7;
      --line-strong: #b7c0ce;
      --ink: #18202b;
      --muted: #687386;
      --soft: #eef2f6;
      --teal: #0f766e;
      --amber: #b7791f;
      --red: #b42318;
      --blue: #2563eb;
      --shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-width: 320px;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.45 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }
    button, input, select {
      font: inherit;
      letter-spacing: 0;
    }
    .shell {
      display: grid;
      min-height: 100vh;
      grid-template-rows: auto auto 1fr;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 20px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    h1 {
      margin: 0;
      font-size: 18px;
      font-weight: 700;
    }
    .subhead {
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }
    .toolbar {
      display: grid;
      grid-template-columns: repeat(5, minmax(120px, 1fr)) auto;
      gap: 10px;
      padding: 12px 20px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfd;
    }
    label {
      display: grid;
      gap: 4px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 650;
      text-transform: uppercase;
    }
    input, select {
      min-height: 34px;
      width: 100%;
      border: 1px solid var(--line-strong);
      border-radius: 6px;
      background: var(--panel);
      color: var(--ink);
      padding: 6px 9px;
    }
    button {
      min-height: 34px;
      align-self: end;
      border: 1px solid #0b625b;
      border-radius: 6px;
      background: var(--teal);
      color: #ffffff;
      cursor: pointer;
      padding: 7px 12px;
      font-weight: 700;
    }
    button:disabled { cursor: wait; opacity: 0.68; }
    .metrics {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 1px;
      border-bottom: 1px solid var(--line);
      background: var(--line);
    }
    .metric {
      min-height: 72px;
      padding: 12px 20px;
      background: var(--panel);
    }
    .metric span {
      display: block;
      color: var(--muted);
      font-size: 11px;
      font-weight: 650;
      text-transform: uppercase;
    }
    .metric strong {
      display: block;
      margin-top: 6px;
      font-size: 22px;
      line-height: 1;
    }
    .ops {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(320px, 0.55fr);
      gap: 16px;
      padding: 16px 20px;
      border-bottom: 1px solid var(--line);
      background: #ffffff;
    }
    .ops-panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .ops-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      background: #f2f5f8;
    }
    .ops-grid {
      display: grid;
      grid-template-columns: repeat(6, minmax(96px, 1fr));
      gap: 10px;
      padding: 12px;
    }
    .ops-grid label:nth-child(1) { grid-column: span 2; }
    .ops-grid label:nth-child(2) { grid-column: span 2; }
    .ops-grid label:nth-child(3) { grid-column: span 2; }
    .ops-grid label:nth-child(4),
    .ops-grid label:nth-child(5),
    .ops-grid label:nth-child(6),
    .ops-grid label:nth-child(7) { grid-column: span 1; }
    .ops-grid button { grid-column: span 1; }
    .secondary {
      border-color: var(--line-strong);
      background: #ffffff;
      color: var(--ink);
    }
    .danger {
      border-color: #8f1d14;
      background: var(--red);
    }
    .log {
      max-height: 214px;
      overflow: auto;
      margin: 0;
      padding: 12px;
      background: #111827;
      color: #d5dde8;
      font: 12px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      white-space: pre-wrap;
    }
    .runs {
      padding: 16px 20px;
      border-bottom: 1px solid var(--line);
      background: var(--bg);
    }
    .runs table { min-width: 940px; }
    .evidence {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 16px;
      margin-top: 16px;
    }
    .evidence table { min-width: 720px; }
    .analysis-panel { grid-column: 1 / -1; }
    .analysis-panel table { min-width: 980px; }
    .status-pill {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 12px;
      font-weight: 750;
      background: var(--soft);
      color: #384456;
      white-space: nowrap;
    }
    .status-queued { background: #fff7ed; color: #9a3412; }
    .status-running { background: #eff6ff; color: #1d4ed8; }
    .status-completed { background: #ecfdf5; color: #047857; }
    .status-failed, .status-rate_limited { background: #fef2f2; color: #b42318; }
    main {
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(360px, 0.65fr);
      min-height: 0;
    }
    .list, .detail {
      min-width: 0;
      padding: 16px 20px 24px;
    }
    .list { border-right: 1px solid var(--line); }
    .section-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }
    h2 {
      margin: 0;
      font-size: 14px;
      font-weight: 750;
    }
    .status {
      color: var(--muted);
      font-size: 12px;
      min-height: 18px;
      text-align: right;
    }
    .table-wrap {
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
    }
    table {
      width: 100%;
      min-width: 820px;
      border-collapse: collapse;
    }
    th, td {
      padding: 9px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }
    th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: #f2f5f8;
      color: #465365;
      font-size: 11px;
      text-transform: uppercase;
    }
    tr { cursor: pointer; }
    tr:hover td { background: #f8fbfb; }
    tr.selected td { background: #edf8f6; }
    .mono {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
    }
    .muted { color: var(--muted); }
    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      max-width: 100%;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--soft);
      color: #384456;
      padding: 2px 8px;
      font-size: 12px;
      white-space: nowrap;
    }
    .risk-low { color: var(--teal); font-weight: 750; }
    .risk-mid { color: var(--amber); font-weight: 750; }
    .risk-high { color: var(--red); font-weight: 750; }
    .detail-panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .detail-head {
      display: grid;
      gap: 8px;
      padding: 14px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfd;
    }
    .kv {
      display: grid;
      grid-template-columns: 126px minmax(0, 1fr);
      gap: 8px;
      padding: 10px 14px;
      border-bottom: 1px solid var(--line);
    }
    .kv dt { color: var(--muted); font-size: 12px; }
    .kv dd { margin: 0; min-width: 0; overflow-wrap: anywhere; }
    .creative {
      display: grid;
      gap: 6px;
      padding: 12px 14px;
      border-top: 1px solid var(--line);
    }
    .creative:first-child { border-top: 0; }
    .creative-title {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      font-weight: 750;
    }
    .analysis-mini {
      margin-top: 8px;
      padding: 8px 10px;
      border-left: 3px solid var(--teal);
      background: #f1f8f6;
      font-size: 12px;
      line-height: 1.45;
    }
    .analysis-mini strong { margin-right: 8px; }
    .empty {
      padding: 28px;
      border: 1px dashed var(--line-strong);
      border-radius: 8px;
      background: var(--panel);
      color: var(--muted);
      text-align: center;
    }
    a { color: var(--blue); text-decoration: none; }
    a:hover { text-decoration: underline; }
    @media (max-width: 980px) {
      header { align-items: flex-start; flex-direction: column; }
      .subhead { white-space: normal; }
      .toolbar { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .toolbar button { grid-column: span 2; }
      .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .ops { grid-template-columns: 1fr; }
      .evidence { grid-template-columns: 1fr; }
      .ops-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .ops-grid label,
      .ops-grid label:nth-child(1),
      .ops-grid label:nth-child(2),
      .ops-grid label:nth-child(3),
      .ops-grid label:nth-child(4),
      .ops-grid label:nth-child(5),
      .ops-grid label:nth-child(6),
      .ops-grid label:nth-child(7),
      .ops-grid button { grid-column: span 1; }
      main { grid-template-columns: 1fr; }
      .list { border-right: 0; border-bottom: 1px solid var(--line); }
    }
    @media (max-width: 560px) {
      header, .toolbar, .ops, .runs, .list, .detail { padding-left: 12px; padding-right: 12px; }
      .toolbar, .metrics { grid-template-columns: 1fr; }
      .toolbar button { grid-column: auto; }
      .ops-grid { grid-template-columns: 1fr; }
      .metric { min-height: 62px; padding: 10px 12px; }
      .kv { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div>
        <h1>Public Malak</h1>
        <div class="subhead">Campaign clusters from social ad ingest and intelligence jobs</div>
      </div>
      <div class="subhead" id="updated">Not loaded</div>
    </header>

    <form class="toolbar" id="filters">
      <label>Scope
        <select id="platformScope">
          <option value="">All</option>
          <option value="cross_platform">Cross platform</option>
          <option value="platform">Single platform</option>
        </select>
      </label>
      <label>Landing domain
        <input id="landingDomain" placeholder="example.com" autocomplete="off">
      </label>
      <label>Min creatives
        <input id="minCreativeCount" type="number" min="1" max="999" placeholder="1">
      </label>
      <label>Limit
        <select id="limit">
          <option>25</option>
          <option selected>50</option>
          <option>100</option>
        </select>
      </label>
      <label>Search
        <input id="search" placeholder="cluster, domain, platform" autocomplete="off">
      </label>
      <button id="refresh" type="submit">Refresh</button>
    </form>

    <section class="metrics" aria-label="Campaign metrics">
      <div class="metric"><span>Clusters</span><strong id="mClusters">0</strong></div>
      <div class="metric"><span>Creatives</span><strong id="mCreatives">0</strong></div>
      <div class="metric"><span>Platforms</span><strong id="mPlatforms">0</strong></div>
      <div class="metric"><span>Max risk</span><strong id="mRisk">0</strong></div>
    </section>

    <section class="ops" aria-label="Operator controls">
      <div class="ops-panel">
        <div class="ops-head">
          <h2>Run Jobs</h2>
          <div class="status" id="opsStatus">Idle</div>
        </div>
        <form class="ops-grid" id="opsForm">
          <label>Platform
            <select id="opPlatform">
              <option value="line">line</option>
              <option value="x">x</option>
              <option value="facebook">facebook</option>
              <option value="instagram">instagram</option>
              <option value="whatsapp">whatsapp</option>
              <option value="linkedin">linkedin</option>
              <option value="telegram">telegram</option>
              <option value="meta">meta</option>
              <option value="google">google</option>
              <option value="tiktok">tiktok</option>
            </select>
          </label>
          <label>Search terms
            <input id="opSearchTerms" placeholder="brand, domain, claim" autocomplete="off">
          </label>
          <label>Country
            <input id="opCountry" maxlength="2" placeholder="JP" value="JP" autocomplete="off">
          </label>
          <label>Crawl limit
            <input id="opCrawlLimit" type="number" min="1" max="500" value="25">
          </label>
          <label>Intel limit
            <input id="opIntelLimit" type="number" min="1" max="100" value="10">
          </label>
          <label>Analysis
            <select id="opAnalysisKind">
              <option value="competitive">competitive</option>
              <option value="adversarial">adversarial</option>
              <option value="claim">claim</option>
              <option value="sentiment">sentiment</option>
              <option value="targeting">targeting</option>
            </select>
          </label>
          <label>Cluster scope
            <select id="opClusterScope">
              <option value="platform">platform</option>
              <option value="cross_platform">cross_platform</option>
            </select>
          </label>
          <button id="runCrawl" type="button">Queue crawl</button>
          <button id="runProcessQueue" class="secondary" type="button">Process queue</button>
          <button id="runAnalyze" class="secondary" type="button">Analyze recent</button>
          <button id="runCluster" class="secondary" type="button">Cluster recent</button>
          <button id="runPipeline" class="danger" type="button">Run all</button>
        </form>
      </div>
      <div class="ops-panel">
        <div class="ops-head">
          <h2>Job Log</h2>
          <button id="clearLog" class="secondary" type="button">Clear</button>
        </div>
        <pre class="log" id="jobLog">No jobs run from this session.</pre>
      </div>
    </section>

    <section class="runs" aria-label="Scraper runs">
      <div class="section-title">
        <h2>Recent Scraper Runs</h2>
        <div class="status" id="runsStatus">Not loaded</div>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Run</th>
              <th>Status</th>
              <th>Platform</th>
              <th>Query</th>
              <th>Country</th>
              <th>Ads</th>
              <th>Started</th>
              <th>Finished</th>
            </tr>
          </thead>
          <tbody id="runRows"></tbody>
        </table>
      </div>
      <div class="evidence">
        <div>
          <div class="section-title">
            <h2>Run Snapshots</h2>
            <div class="status" id="snapshotsStatus">Select a run</div>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Snapshot</th>
                  <th>Creative</th>
                  <th>HTTP</th>
                  <th>Parse</th>
                  <th>Artifacts</th>
                  <th>Scraped</th>
                </tr>
              </thead>
              <tbody id="snapshotRows"></tbody>
            </table>
          </div>
        </div>
        <div>
          <div class="section-title">
            <h2>Recent Creatives</h2>
            <div class="status" id="adsStatus">Not loaded</div>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Creative</th>
                  <th>Advertiser</th>
                  <th>Headline</th>
                  <th>Active</th>
                  <th>Seen</th>
                </tr>
              </thead>
              <tbody id="adRows"></tbody>
            </table>
          </div>
        </div>
        <div class="analysis-panel">
          <div class="section-title">
            <h2>Recent Analyses</h2>
            <div class="status" id="analysesStatus">Not loaded</div>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Analysis</th>
                  <th>Creative</th>
                  <th>Kind</th>
                  <th>Status</th>
                  <th>Risk</th>
                  <th>Summary</th>
                  <th>Analyzed</th>
                </tr>
              </thead>
              <tbody id="analysisRows"></tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <main>
      <section class="list">
        <div class="section-title">
          <h2>Campaign Clusters</h2>
          <div class="status" id="status"></div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Campaign</th>
                <th>Scope</th>
                <th>Platforms</th>
                <th>Domain</th>
                <th>Creatives</th>
                <th>Risk</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody id="clusterRows"></tbody>
          </table>
        </div>
      </section>

      <section class="detail">
        <div class="section-title">
          <h2>Cluster Detail</h2>
          <div class="status" id="detailStatus"></div>
        </div>
        <div id="detailBody" class="empty">Select a cluster.</div>
      </section>
    </main>
  </div>

  <script>
    const state = {
      clusters: [],
      runs: [],
      selectedVertexId: new URL(location.href).searchParams.get("cluster") || "",
      selectedRunId: "",
      loading: false,
    };

    const els = {
      filters: document.getElementById("filters"),
      platformScope: document.getElementById("platformScope"),
      landingDomain: document.getElementById("landingDomain"),
      minCreativeCount: document.getElementById("minCreativeCount"),
      limit: document.getElementById("limit"),
      search: document.getElementById("search"),
      refresh: document.getElementById("refresh"),
      rows: document.getElementById("clusterRows"),
      status: document.getElementById("status"),
      detailStatus: document.getElementById("detailStatus"),
      detailBody: document.getElementById("detailBody"),
      updated: document.getElementById("updated"),
      mClusters: document.getElementById("mClusters"),
      mCreatives: document.getElementById("mCreatives"),
      mPlatforms: document.getElementById("mPlatforms"),
      mRisk: document.getElementById("mRisk"),
      opsStatus: document.getElementById("opsStatus"),
      opPlatform: document.getElementById("opPlatform"),
      opSearchTerms: document.getElementById("opSearchTerms"),
      opCountry: document.getElementById("opCountry"),
      opCrawlLimit: document.getElementById("opCrawlLimit"),
      opIntelLimit: document.getElementById("opIntelLimit"),
      opAnalysisKind: document.getElementById("opAnalysisKind"),
      opClusterScope: document.getElementById("opClusterScope"),
      runCrawl: document.getElementById("runCrawl"),
      runProcessQueue: document.getElementById("runProcessQueue"),
      runAnalyze: document.getElementById("runAnalyze"),
      runCluster: document.getElementById("runCluster"),
      runPipeline: document.getElementById("runPipeline"),
      clearLog: document.getElementById("clearLog"),
      jobLog: document.getElementById("jobLog"),
      runsStatus: document.getElementById("runsStatus"),
      runRows: document.getElementById("runRows"),
      snapshotsStatus: document.getElementById("snapshotsStatus"),
      snapshotRows: document.getElementById("snapshotRows"),
      adsStatus: document.getElementById("adsStatus"),
      adRows: document.getElementById("adRows"),
      analysesStatus: document.getElementById("analysesStatus"),
      analysisRows: document.getElementById("analysisRows"),
    };

    els.filters.addEventListener("submit", (event) => {
      event.preventDefault();
      loadClusters();
    });
    els.search.addEventListener("input", () => renderClusters());
    els.runCrawl.addEventListener("click", () => runCrawl());
    els.runProcessQueue.addEventListener("click", () => runProcessQueue());
    els.runAnalyze.addEventListener("click", () => runAnalyze());
    els.runCluster.addEventListener("click", () => runCluster());
    els.runPipeline.addEventListener("click", () => runPipeline());
    els.clearLog.addEventListener("click", () => {
      els.jobLog.textContent = "No jobs run from this session.";
    });

    function valueOf(obj, keys, fallback = "") {
      for (const key of keys) {
        if (obj && obj[key] !== undefined && obj[key] !== null && obj[key] !== "") return obj[key];
      }
      return fallback;
    }

    function arrayOf(value) {
      if (Array.isArray(value)) return value.filter(Boolean);
      if (typeof value === "string" && value.trim()) return value.split(",").map((v) => v.trim()).filter(Boolean);
      return [];
    }

    function numberOf(value) {
      const n = Number(value);
      return Number.isFinite(n) ? n : 0;
    }

    function fmtDate(value) {
      if (!value) return "";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return String(value);
      return date.toLocaleString(undefined, { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
    }

    function riskClass(value) {
      const risk = numberOf(value);
      if (risk >= 700) return "risk-high";
      if (risk >= 350) return "risk-mid";
      return "risk-low";
    }

    function riskLabel(value) {
      const risk = numberOf(value);
      return risk ? String(risk) : "0";
    }

    function platformLabels(cluster) {
      const platforms = arrayOf(valueOf(cluster, ["platforms", "platformList"]));
      if (platforms.length) return platforms;
      const count = numberOf(valueOf(cluster, ["platformCount", "platformsCount"]));
      if (count > 0) return [count + (count === 1 ? " platform" : " platforms")];
      return [];
    }

    function statusClass(status) {
      return "status-pill status-" + String(status || "").toLowerCase().replace(/[^a-z0-9_]+/g, "_");
    }

    function text(value, fallback = "-") {
      if (value === undefined || value === null || value === "") return fallback;
      return String(value);
    }

    function setText(node, value) {
      node.textContent = value;
    }

    function clear(node) {
      while (node.firstChild) node.removeChild(node.firstChild);
    }

    function appendPills(parent, values) {
      const row = document.createElement("div");
      row.className = "pill-row";
      for (const value of values.slice(0, 5)) {
        const pill = document.createElement("span");
        pill.className = "pill";
        pill.textContent = value;
        row.appendChild(pill);
      }
      if (!values.length) {
        const pill = document.createElement("span");
        pill.className = "pill";
        pill.textContent = "-";
        row.appendChild(pill);
      }
      parent.appendChild(row);
    }

    function opPayload() {
      return {
        platform: els.opPlatform.value,
        country: els.opCountry.value.trim().toUpperCase(),
        searchTerms: els.opSearchTerms.value.split(",").map((term) => term.trim()).filter(Boolean),
        crawlLimit: els.opCrawlLimit.value,
        intelLimit: els.opIntelLimit.value,
        analysisKind: els.opAnalysisKind.value,
        platformScope: els.opClusterScope.value,
      };
    }

    function appendLog(title, data) {
      const time = new Date().toLocaleTimeString();
      const entry = "[" + time + "] " + title + "\\n" + JSON.stringify(data, null, 2);
      els.jobLog.textContent = els.jobLog.textContent === "No jobs run from this session." ? entry : entry + "\\n\\n" + els.jobLog.textContent;
    }

    function setOpsBusy(busy, label) {
      setText(els.opsStatus, label || (busy ? "Running" : "Idle"));
      for (const button of [els.runCrawl, els.runProcessQueue, els.runAnalyze, els.runCluster, els.runPipeline]) button.disabled = busy;
    }

    async function xrpc(nsid, params, method = "GET") {
      const url = new URL("/xrpc/" + nsid, location.origin);
      const clean = {};
      for (const [key, value] of Object.entries(params || {})) {
        if (value !== undefined && value !== null && value !== "" && !(Array.isArray(value) && value.length === 0)) clean[key] = value;
      }
      const init = { headers: { accept: "application/json" } };
      if (method === "POST") {
        init.method = "POST";
        init.headers["content-type"] = "application/json";
        init.body = JSON.stringify(clean);
      } else {
        for (const [key, value] of Object.entries(clean)) url.searchParams.set(key, value);
      }
      const resp = await fetch(url, init);
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(data.message || data.error || "Request failed");
      return data;
    }

    async function runCrawl() {
      const payload = opPayload();
      return runJob("crawlAds", "Queue crawl", {
        platform: payload.platform,
        country: payload.country,
        searchTerms: payload.searchTerms,
        queryKind: "search",
        limit: payload.crawlLimit,
      });
    }

    async function runAnalyze() {
      const payload = opPayload();
      return runJob("analyzeRecentAds", "Analyze recent", {
        platform: payload.platform,
        analysisKind: payload.analysisKind,
        limit: payload.intelLimit,
      });
    }

    async function runProcessQueue() {
      const payload = opPayload();
      return runJob("processScraperQueue", "Process queue", {
        platform: payload.platform,
        max: payload.intelLimit,
        reclaimAfterSec: 60,
      });
    }

    async function runCluster() {
      const payload = opPayload();
      return runJob("clusterRecentAds", "Cluster recent", {
        platform: payload.platform,
        platformScope: payload.platformScope,
        limit: payload.intelLimit,
      });
    }

    async function runPipeline() {
      setOpsBusy(true, "Running pipeline");
      try {
        await runCrawl();
        await runProcessQueue();
        await runAnalyze();
        await runCluster();
        await loadClusters();
      } finally {
        setOpsBusy(false, "Idle");
      }
    }

    async function runJob(shortName, title, payload) {
      const wasPipeline = els.runPipeline.disabled;
      if (!wasPipeline) setOpsBusy(true, title);
      try {
        const data = await xrpc("com.etzhayyim.apps.publicMalak." + shortName, payload, "POST");
        appendLog(title, data);
        setText(els.opsStatus, "Done");
        await loadRuns();
        if (shortName === "clusterRecentAds") await loadClusters();
        return data;
      } catch (err) {
        appendLog(title + " failed", { error: err.message || String(err) });
        setText(els.opsStatus, "Failed");
        throw err;
      } finally {
        if (!wasPipeline) setOpsBusy(false, "Idle");
      }
    }

    async function loadClusters() {
      state.loading = true;
      els.refresh.disabled = true;
      setText(els.status, "Loading");
      try {
        const data = await xrpc("com.etzhayyim.apps.publicMalak.listCampaignClusters", {
          platformScope: els.platformScope.value,
          landingDomain: els.landingDomain.value.trim(),
          minCreativeCount: els.minCreativeCount.value,
          limit: els.limit.value,
        });
        state.clusters = Array.isArray(data.clusters) ? data.clusters : [];
        if (!state.selectedVertexId && state.clusters[0]) {
          state.selectedVertexId = String(valueOf(state.clusters[0], ["vertexId", "uri", "id"]));
        }
        renderClusters();
        renderMetrics();
        setText(els.updated, "Updated " + new Date().toLocaleTimeString());
        loadRuns();
        if (state.selectedVertexId) loadDetail(state.selectedVertexId);
      } catch (err) {
        setText(els.status, err.message || String(err));
        state.clusters = [];
        renderClusters();
        renderMetrics();
      } finally {
        state.loading = false;
        els.refresh.disabled = false;
      }
    }

    async function loadRuns() {
      setText(els.runsStatus, "Loading");
      try {
        const data = await xrpc("com.etzhayyim.apps.publicMalak.listScraperRuns", {
          platform: els.opPlatform.value,
          limit: 12,
        });
        state.runs = Array.isArray(data.runs) ? data.runs : [];
        renderRuns(state.runs);
      } catch (err) {
        clear(els.runRows);
        setText(els.runsStatus, err.message || String(err));
      }
    }

    function renderRuns(runs) {
      clear(els.runRows);
      setText(els.runsStatus, runs.length ? runs.length + " shown" : "No runs");
      for (const run of runs) {
        const tr = document.createElement("tr");
        const runVertexId = text(valueOf(run, ["vertexId", "uri", "id"]));
        if (runVertexId === state.selectedRunId) tr.className = "selected";
        tr.addEventListener("click", () => selectRun(run));
        const runCell = document.createElement("td");
        const runId = document.createElement("div");
        runId.className = "mono";
        runId.textContent = runVertexId;
        runCell.appendChild(runId);

        const status = document.createElement("td");
        const statusPill = document.createElement("span");
        statusPill.className = statusClass(valueOf(run, ["status"]));
        statusPill.textContent = text(valueOf(run, ["status"]));
        status.appendChild(statusPill);

        const platform = document.createElement("td");
        platform.textContent = text(valueOf(run, ["platform"]));
        const query = document.createElement("td");
        query.textContent = text(valueOf(run, ["queryValue", "query"]));
        const country = document.createElement("td");
        country.textContent = text(valueOf(run, ["country"]));
        const ads = document.createElement("td");
        ads.textContent = [
          numberOf(valueOf(run, ["adsSeen"])),
          numberOf(valueOf(run, ["adsNew"])),
          numberOf(valueOf(run, ["adsUpdated"])),
        ].join(" / ");
        const started = document.createElement("td");
        started.textContent = fmtDate(valueOf(run, ["startedAt", "createdAt"]));
        const finished = document.createElement("td");
        finished.textContent = fmtDate(valueOf(run, ["finishedAt"]));

        tr.append(runCell, status, platform, query, country, ads, started, finished);
        els.runRows.appendChild(tr);
      }
      if (!state.selectedRunId && runs[0]) selectRun(runs[0]);
    }

    function selectRun(run) {
      state.selectedRunId = text(valueOf(run, ["vertexId", "uri", "id"]), "");
      renderRuns(state.runs);
      loadRunSnapshots(state.selectedRunId);
      loadAds(valueOf(run, ["platform"], els.opPlatform.value));
      loadAnalyses({ platform: valueOf(run, ["platform"], els.opPlatform.value) });
    }

    async function loadRunSnapshots(runId) {
      if (!runId) return;
      setText(els.snapshotsStatus, "Loading");
      try {
        const data = await xrpc("com.etzhayyim.apps.publicMalak.listSnapshots", {
          scraperRunId: runId,
          limit: 12,
        });
        renderSnapshots(Array.isArray(data.snapshots) ? data.snapshots : []);
      } catch (err) {
        clear(els.snapshotRows);
        setText(els.snapshotsStatus, err.message || String(err));
      }
    }

    async function loadAds(platform) {
      setText(els.adsStatus, "Loading");
      try {
        const data = await xrpc("com.etzhayyim.apps.publicMalak.listAds", {
          platform: platform || els.opPlatform.value,
          limit: 12,
        });
        renderAds(Array.isArray(data.ads) ? data.ads : []);
      } catch (err) {
        clear(els.adRows);
        setText(els.adsStatus, err.message || String(err));
      }
    }

    async function loadAnalyses(filters) {
      setText(els.analysesStatus, "Loading");
      try {
        const data = await xrpc("com.etzhayyim.apps.publicMalak.listAnalyses", {
          platform: filters && filters.platform ? filters.platform : els.opPlatform.value,
          creativeVertexId: filters && filters.creativeVertexId ? filters.creativeVertexId : "",
          analysisKind: filters && filters.analysisKind ? filters.analysisKind : "",
          limit: 12,
        });
        renderAnalyses(Array.isArray(data.analyses) ? data.analyses : []);
      } catch (err) {
        clear(els.analysisRows);
        setText(els.analysesStatus, err.message || String(err));
      }
    }

    function renderSnapshots(snapshots) {
      clear(els.snapshotRows);
      setText(els.snapshotsStatus, snapshots.length ? snapshots.length + " shown" : "No snapshots");
      for (const snapshot of snapshots) {
        const tr = document.createElement("tr");
        const id = document.createElement("td");
        id.className = "mono";
        id.textContent = text(valueOf(snapshot, ["vertexId"]));
        const creative = document.createElement("td");
        creative.className = "mono";
        creative.textContent = text(valueOf(snapshot, ["creativeVertexId"]));
        const http = document.createElement("td");
        http.textContent = text(valueOf(snapshot, ["httpStatus"]));
        const parse = document.createElement("td");
        parse.textContent = valueOf(snapshot, ["parseOk"]) === true ? "ok" : text(valueOf(snapshot, ["parseError"], "failed"));
        const artifacts = document.createElement("td");
        appendArtifactLinks(artifacts, snapshot);
        const scraped = document.createElement("td");
        scraped.textContent = fmtDate(valueOf(snapshot, ["scrapedAt"]));
        tr.append(id, creative, http, parse, artifacts, scraped);
        els.snapshotRows.appendChild(tr);
      }
    }

    function appendArtifactLinks(parent, snapshot) {
      const links = [
        ["html", valueOf(snapshot, ["htmlCid"])],
        ["screenshot", valueOf(snapshot, ["screenshotCid"])],
        ["har", valueOf(snapshot, ["harCid"])],
      ].filter((entry) => entry[1]);
      if (!links.length) {
        parent.textContent = "-";
        return;
      }
      const row = document.createElement("div");
      row.className = "pill-row";
      for (const [kind, cid] of links) {
        const link = document.createElement("a");
        link.className = "pill";
        link.href = "/artifacts/" + encodeURIComponent(kind) + "/" + encodeURIComponent(String(cid));
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = kind;
        row.appendChild(link);
      }
      parent.appendChild(row);
    }

    function renderAds(ads) {
      clear(els.adRows);
      setText(els.adsStatus, ads.length ? ads.length + " shown" : "No creatives");
      for (const ad of ads) {
        const tr = document.createElement("tr");
        const creativeVertexId = text(valueOf(ad, ["vertexId"]));
        tr.addEventListener("click", () => loadAnalyses({ creativeVertexId }));
        const id = document.createElement("td");
        id.className = "mono";
        id.textContent = creativeVertexId;
        const advertiser = document.createElement("td");
        advertiser.textContent = text(valueOf(ad, ["advertiserName"]));
        const headline = document.createElement("td");
        headline.textContent = text(valueOf(ad, ["headline", "bodyText"]));
        const active = document.createElement("td");
        active.textContent = valueOf(ad, ["isActive"]) === true ? "yes" : valueOf(ad, ["isActive"]) === false ? "no" : "-";
        const seen = document.createElement("td");
        seen.textContent = fmtDate(valueOf(ad, ["lastSeenAt"]));
        tr.append(id, advertiser, headline, active, seen);
        els.adRows.appendChild(tr);
      }
    }

    function renderAnalyses(analyses) {
      clear(els.analysisRows);
      setText(els.analysesStatus, analyses.length ? analyses.length + " shown" : "No analyses");
      for (const analysis of analyses) {
        const tr = document.createElement("tr");
        const id = document.createElement("td");
        id.className = "mono";
        id.textContent = text(valueOf(analysis, ["vertexId"]));
        const creative = document.createElement("td");
        creative.className = "mono";
        creative.textContent = text(valueOf(analysis, ["creativeVertexId"]));
        const kind = document.createElement("td");
        kind.textContent = text(valueOf(analysis, ["analysisKind"]));
        const status = document.createElement("td");
        const statusPill = document.createElement("span");
        statusPill.className = statusClass(valueOf(analysis, ["status"]));
        statusPill.textContent = text(valueOf(analysis, ["status"]));
        status.appendChild(statusPill);
        const risk = document.createElement("td");
        risk.className = riskClass(valueOf(analysis, ["riskScorePermille"], 0));
        risk.textContent = riskLabel(valueOf(analysis, ["riskScorePermille"], 0));
        const summary = document.createElement("td");
        summary.textContent = text(valueOf(analysis, ["summary"]));
        const analyzed = document.createElement("td");
        analyzed.textContent = fmtDate(valueOf(analysis, ["analyzedAt"]));
        tr.append(id, creative, kind, status, risk, summary, analyzed);
        els.analysisRows.appendChild(tr);
      }
    }

    function filteredClusters() {
      const q = els.search.value.trim().toLowerCase();
      if (!q) return state.clusters;
      return state.clusters.filter((cluster) => {
        const haystack = [
          valueOf(cluster, ["campaignKey", "clusterKey", "vertexId", "uri"]),
          valueOf(cluster, ["landingDomain", "domain"]),
          valueOf(cluster, ["platformScope"]),
          arrayOf(valueOf(cluster, ["platforms", "platformList"])).join(" "),
        ].join(" ").toLowerCase();
        return haystack.includes(q);
      });
    }

    function renderMetrics() {
      const clusters = filteredClusters();
      const platformSet = new Set();
      let platformCountFallback = 0;
      let creatives = 0;
      let maxRisk = 0;
      for (const cluster of clusters) {
        creatives += numberOf(valueOf(cluster, ["creativeCount", "creativesCount", "adCount"]));
        maxRisk = Math.max(maxRisk, numberOf(valueOf(cluster, ["maxRiskScorePermille", "riskScorePermille", "riskPermille"])));
        const platforms = arrayOf(valueOf(cluster, ["platforms", "platformList"]));
        if (platforms.length) {
          for (const platform of platforms) platformSet.add(platform);
        } else {
          platformCountFallback += numberOf(valueOf(cluster, ["platformCount", "platformsCount"]));
        }
      }
      setText(els.mClusters, String(clusters.length));
      setText(els.mCreatives, String(creatives));
      setText(els.mPlatforms, String(platformSet.size || platformCountFallback));
      setText(els.mRisk, String(maxRisk));
    }

    function renderClusters() {
      const clusters = filteredClusters();
      clear(els.rows);
      setText(els.status, clusters.length ? clusters.length + " shown" : "No clusters");
      for (const cluster of clusters) {
        const vertexId = String(valueOf(cluster, ["vertexId", "uri", "id"]));
        const tr = document.createElement("tr");
        if (vertexId === state.selectedVertexId) tr.className = "selected";
        tr.addEventListener("click", () => selectCluster(vertexId));

        const campaign = document.createElement("td");
        const strong = document.createElement("div");
        strong.textContent = text(valueOf(cluster, ["campaignKey", "clusterKey"], vertexId));
        const id = document.createElement("div");
        id.className = "mono muted";
        id.textContent = vertexId;
        campaign.append(strong, id);

        const scope = document.createElement("td");
        scope.textContent = text(valueOf(cluster, ["platformScope", "scope"]));

        const platforms = document.createElement("td");
        appendPills(platforms, platformLabels(cluster));

        const domain = document.createElement("td");
        domain.textContent = text(valueOf(cluster, ["landingDomain", "domain"]));

        const count = document.createElement("td");
        count.textContent = String(numberOf(valueOf(cluster, ["creativeCount", "creativesCount", "adCount"])));

        const risk = document.createElement("td");
        const riskValue = valueOf(cluster, ["maxRiskScorePermille", "riskScorePermille", "riskPermille"], 0);
        risk.className = riskClass(riskValue);
        risk.textContent = riskLabel(riskValue);

        const updated = document.createElement("td");
        updated.textContent = fmtDate(valueOf(cluster, ["updatedAt", "lastSeenAt", "createdAt"]));

        tr.append(campaign, scope, platforms, domain, count, risk, updated);
        els.rows.appendChild(tr);
      }
      renderMetrics();
    }

    function selectCluster(vertexId) {
      state.selectedVertexId = vertexId;
      const next = new URL(location.href);
      next.searchParams.set("cluster", vertexId);
      history.replaceState(null, "", next);
      renderClusters();
      loadDetail(vertexId);
    }

    async function loadDetail(vertexId) {
      setText(els.detailStatus, "Loading");
      els.detailBody.className = "empty";
      els.detailBody.textContent = "Loading cluster.";
      try {
        const data = await xrpc("com.etzhayyim.apps.publicMalak.getCampaignCluster", {
          vertexId,
          creativeLimit: 20,
          analysisLimit: 100,
        });
        renderDetail(
          data.cluster || {},
          Array.isArray(data.creatives) ? data.creatives : [],
          Array.isArray(data.analyses) ? data.analyses : [],
        );
        setText(els.detailStatus, "");
      } catch (err) {
        els.detailBody.className = "empty";
        els.detailBody.textContent = err.message || String(err);
        setText(els.detailStatus, "Failed");
      }
    }

    function renderDetail(cluster, creatives, analyses) {
      clear(els.detailBody);
      els.detailBody.className = "detail-panel";
      const analysesByCreative = new Map();
      for (const analysis of analyses) {
        const creativeVertexId = text(valueOf(analysis, ["creativeVertexId"]), "");
        if (!creativeVertexId) continue;
        if (!analysesByCreative.has(creativeVertexId)) analysesByCreative.set(creativeVertexId, []);
        analysesByCreative.get(creativeVertexId).push(analysis);
      }

      const head = document.createElement("div");
      head.className = "detail-head";
      const title = document.createElement("strong");
      title.textContent = text(valueOf(cluster, ["campaignKey", "clusterKey"], state.selectedVertexId));
      const meta = document.createElement("div");
      meta.className = "mono muted";
      meta.textContent = text(valueOf(cluster, ["vertexId", "uri", "id"], state.selectedVertexId));
      head.append(title, meta);
      els.detailBody.appendChild(head);

      addKv("Scope", text(valueOf(cluster, ["platformScope", "scope"])));
      addKv("Landing domain", text(valueOf(cluster, ["landingDomain", "domain"])));
      addKv("Creatives", String(numberOf(valueOf(cluster, ["creativeCount", "creativesCount", "adCount"]))));
      addKv("Platforms", platformLabels(cluster).join(", ") || "-");
      addKv("Risk", riskLabel(valueOf(cluster, ["maxRiskScorePermille", "riskScorePermille", "riskPermille"], 0)));
      addKv("Summary", text(valueOf(cluster, ["summary", "sampleHeadline", "sampleBodyText"])));

      const creativeWrap = document.createElement("div");
      for (const creative of creatives) {
        const item = document.createElement("div");
        item.className = "creative";
        const top = document.createElement("div");
        top.className = "creative-title";
        const left = document.createElement("span");
        left.textContent = text(valueOf(creative, ["headline", "title", "platformAdId", "adId", "vertexId"]));
        const right = document.createElement("span");
        right.className = "muted";
        right.textContent = text(valueOf(creative, ["platform"]));
        top.append(left, right);

        const body = document.createElement("div");
        body.textContent = text(valueOf(creative, ["bodyText", "body", "text", "description", "summary"]), "");
        if (!body.textContent) body.className = "muted";
        if (!body.textContent) body.textContent = "No creative text";

        const foot = document.createElement("div");
        foot.className = "mono muted";
        const creativeVertexId = text(valueOf(creative, ["vertexId", "uri", "id"]));
        foot.textContent = creativeVertexId;
        item.append(top, body, foot);

        const linkedAnalyses = analysesByCreative.get(creativeVertexId) || [];
        for (const analysis of linkedAnalyses.slice(0, 2)) {
          const mini = document.createElement("div");
          mini.className = "analysis-mini";
          const kind = document.createElement("strong");
          kind.textContent = text(valueOf(analysis, ["analysisKind"]));
          const risk = document.createElement("span");
          risk.className = riskClass(valueOf(analysis, ["riskScorePermille"], 0));
          risk.textContent = "risk " + riskLabel(valueOf(analysis, ["riskScorePermille"], 0));
          const summary = document.createElement("div");
          summary.textContent = text(valueOf(analysis, ["summary"]));
          mini.append(kind, risk, summary);
          item.appendChild(mini);
        }

        const url = text(valueOf(creative, ["adSnapshotUrl", "archiveUrl", "landingUrl", "url"]), "");
        if (url && /^https?:\\/\\//.test(url)) {
          const link = document.createElement("a");
          link.href = url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          link.textContent = "Open source";
          item.appendChild(link);
        }
        creativeWrap.appendChild(item);
      }
      if (!creatives.length) {
        const empty = document.createElement("div");
        empty.className = "creative muted";
        empty.textContent = "No linked creatives returned.";
        creativeWrap.appendChild(empty);
      }
      els.detailBody.appendChild(creativeWrap);
    }

    function addKv(key, value) {
      const dl = document.createElement("dl");
      dl.className = "kv";
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = key;
      dd.textContent = value;
      dl.append(dt, dd);
      els.detailBody.appendChild(dl);
    }

    loadClusters();
  </script>
</body>
</html>`;
}
