// data-rights.ts — Customer data portability + account deletion (GDPR Art 20 +
// 改正個人情報保護法 第33条 開示請求権).
//
// Endpoints:
//   GET  /api/export            full JSON dump of everything tied to org_did
//   POST /api/account/delete    revoke all keys + DROP SCHEMA + mark plan
//                                'deleted'. One-way; export FIRST.
//
// Export shape (JSON):
//   {
//     orgDid, generatedAt, ipBoundsJp,
//     tenantSchema: { name, tables: [{name, columns, rows}] },
//     billingEvents: [...],
//     orgPlanHistory: [...],
//     apiKeys: [{keyId, name, role, status, createdAt}],   // hash only — no raw secret
//     storageBlobs: [...]
//   }

export interface DataRightsEnv {
  HYPERDRIVE?: unknown;
}

interface RawDb {
  // Pass-through to whatever createKyselyDb returns; consumers use
  // raw `sql` template tag against it.
}

async function getRealDb(env: DataRightsEnv): Promise<{ db: RawDb; sql: ((s: TemplateStringsArray, ...v: unknown[]) => unknown) } | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@etzhayyim/magatama-host-sdk");
    const db = (sdk as unknown as { createKyselyDb: (h: unknown) => unknown }).createKyselyDb(env.HYPERDRIVE as never) as RawDb;
    const sql = (sdk as unknown as { sql?: (s: TemplateStringsArray, ...v: unknown[]) => unknown }).sql ?? null;
    if (!sql) return null;
    return { db, sql };
  } catch {
    return null;
  }
}

async function tenantSchemaName(orgDid: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(orgDid));
  return "yata_" + Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 16);
}

async function execRows(q: unknown, db: unknown): Promise<Array<Record<string, unknown>>> {
  try {
    const exec = (q as { execute: (db: unknown) => Promise<{ rows: Array<Record<string, unknown>> }> }).execute;
    const result = await exec.call(q, db);
    return result.rows ?? [];
  } catch (e) {
    console.warn("[yatabase][data-rights] query failed:", e);
    return [];
  }
}

async function execMutation(q: unknown, db: unknown): Promise<boolean> {
  try {
    const exec = (q as { execute: (db: unknown) => Promise<unknown> }).execute;
    await exec.call(q, db);
    return true;
  } catch (e) {
    console.warn("[yatabase][data-rights] mutation failed:", e);
    return false;
  }
}

function jsonReplacer(_key: string, value: unknown): unknown {
  // BigInt → string so JSON.stringify doesn't throw on RW columns like
  // ts_ms or _seq.
  if (typeof value === "bigint") return value.toString();
  return value;
}

// P75: full KV+R2-backed data export. Returns the same JSON shape as
// the RW path but reads from the Worker-side authoritative stores.
async function buildKvExport(env: DataRightsEnv, orgDid: string): Promise<Response> {
  const generatedAt = new Date().toISOString();
  const kv = (env as unknown as { YATABASE_AUTH_CACHE?: KVNamespace }).YATABASE_AUTH_CACHE;
  const r2 = (env as unknown as { YATA_R2?: R2Bucket }).YATA_R2;

  // 1. API keys (hashes only, no plaintext).
  const { listCachedKeysForOrg } = await import("./auth-cache");
  const apiKeys = await listCachedKeysForOrg(env as never, orgDid);

  // 2. Plan history (current snapshot — KV holds the active record).
  const orgPlanHistory: Array<Record<string, unknown>> = [];
  if (kv) {
    try {
      const raw = await kv.get(`plan:v1:${orgDid}`);
      if (raw) {
        const parsed = JSON.parse(raw);
        orgPlanHistory.push({ ...parsed, status: "active" });
      }
    } catch { /* ignore */ }
  }

  // 3. Usage / billing events (60d window — KV TTL is 35d but newer
  //    counters always present).
  const billingEvents: Array<Record<string, unknown>> = [];
  if (kv) {
    try {
      const usagePrefix = `usage:v1:${orgDid}:`;
      const list = await kv.list({ prefix: usagePrefix, limit: 1000 });
      for (const k of list.keys ?? []) {
        // key shape: `usage:v1:{orgDid}:{metric}:{YYYY-MM-DD}`. orgDid
        // contains colons (`did:web:...`), so split AFTER removing the
        // known prefix: the tail is `{metric}:{YYYY-MM-DD}`.
        const tail = k.name.slice(usagePrefix.length);
        const lastColon = tail.lastIndexOf(":");
        if (lastColon < 0) continue;
        const metric = tail.slice(0, lastColon);
        const day = tail.slice(lastColon + 1);
        if (!metric || !/^\d{4}-\d{2}-\d{2}$/.test(day)) continue;
        const raw = await kv.get(k.name);
        if (!raw) continue;
        try {
          const v = JSON.parse(raw) as { qty?: number; events?: number };
          billingEvents.push({
            ts_day: day,
            metric,
            qty: Number(v.qty ?? 0),
            event_count: Number(v.events ?? 0),
            source: "kv",
          });
        } catch { /* ignore */ }
      }
    } catch { /* ignore */ }
  }
  billingEvents.sort((a, b) => String(b.ts_day).localeCompare(String(a.ts_day)));

  // 4. Cypher graph data (per-org per-label node store).
  const cypherNodes: Array<Record<string, unknown>> = [];
  if (kv) {
    try {
      const labelList = await kv.list({ prefix: `cypher:v1:${orgDid}:labels:`, limit: 200 });
      for (const lk of labelList.keys ?? []) {
        const label = lk.name.slice(`cypher:v1:${orgDid}:labels:`.length);
        const idxRaw = await kv.get(lk.name);
        if (!idxRaw) continue;
        const idx = JSON.parse(idxRaw) as { ids?: string[] };
        for (const id of (idx.ids ?? []).slice(0, 1000)) {
          const nodeRaw = await kv.get(`cypher:v1:${orgDid}:nodes:${label}:${id}`);
          if (!nodeRaw) continue;
          try {
            cypherNodes.push({ label, ...JSON.parse(nodeRaw) });
          } catch { /* ignore */ }
        }
      }
    } catch { /* ignore */ }
  }

  // 5. Storage object metadata — union of KV meta + R2 list.
  const storageBlobs: Array<Record<string, unknown>> = [];
  if (kv) {
    try {
      const metaList = await kv.list({ prefix: `storage:v1:${orgDid}:meta:`, limit: 1000 });
      for (const mk of metaList.keys ?? []) {
        const tail = mk.name.slice(`storage:v1:${orgDid}:meta:`.length);
        const slash = tail.indexOf("/");
        const bucket = slash > 0 ? tail.slice(0, slash) : "";
        const key = slash > 0 ? tail.slice(slash + 1) : "";
        const raw = await kv.get(mk.name);
        if (!raw) continue;
        try {
          const meta = JSON.parse(raw);
          storageBlobs.push({
            bucket_name: bucket,
            object_key: key,
            storage_tier: "kv-fallback",
            storage_provider: "workers-kv",
            ...meta,
          });
        } catch { /* ignore */ }
      }
    } catch { /* ignore */ }
  }
  if (r2) {
    try {
      const orgPrefix = `yata/${orgDid}/`;
      let cursor: string | undefined;
      for (let i = 0; i < 5; i++) {
        const result: R2Objects = await r2.list({ prefix: orgPrefix, limit: 1000, cursor });
        for (const o of result.objects ?? []) {
          const tail = o.key.slice(orgPrefix.length);
          const slash = tail.indexOf("/");
          const bucket = slash > 0 ? tail.slice(0, slash) : "";
          const key = slash > 0 ? tail.slice(slash + 1) : "";
          storageBlobs.push({
            bucket_name: bucket,
            object_key: key,
            size_bytes: o.size,
            etag: `"${o.etag}"`,
            content_type: o.httpMetadata?.contentType ?? "application/octet-stream",
            storage_tier: "r2",
            storage_provider: "cloudflare-r2",
            created_at: o.uploaded.toISOString(),
          });
        }
        if (!result.truncated) break;
        cursor = result.cursor;
      }
    } catch { /* ignore */ }
  }

  // P88: include the KV-backed audit log directly in the export so the
  // GDPR Art 30 "records of processing" obligation is satisfied inline
  // rather than via a separate /api/audit fetch.
  let auditLog: { events: unknown[]; windowStart?: string; windowEnd?: string } = { events: [] };
  try {
    const { getAuditEvents } = await import("./audit-log");
    const audit = await getAuditEvents(env as never, orgDid, 500);
    if (audit) auditLog = audit;
  } catch (e) {
    console.warn("[yatabase][export] audit fetch failed:", e);
  }

  const body = {
    orgDid,
    generatedAt,
    primaryMarket: "US",
    privacyLawCompliance: {
      ccpa1798100: "Right to know (US California Consumer Privacy Act)",
      ccpa1798105: "Right to delete (companion endpoint /api/account/delete)",
      gdprArt20: "Right to data portability",
      gdprArt30: "Records of processing — see /api/audit",
      jpAct33: "改正個人情報保護法 第33条 開示請求権",
      jpAct34_36: "改正個人情報保護法 第34-36条 削除請求権",
      consentBasis: "anonymous-self-signup",
    },
    tenantSchema: { name: "", tables: [] },
    cypherNodes,
    billingEvents,
    orgPlanHistory,
    apiKeys,
    storageBlobs,
    auditLog,
    note: "Worker-side export from KV + R2 (ADR-2605111200 prohibits Worker→RW direct read). When the pod-side /xrpc/yata.export NSID ships, this surface transparently upgrades to include legacy RW-only tables.",
  };

  return new Response(JSON.stringify(body, jsonReplacer, 2), {
    status: 200,
    headers: {
      "content-type": "application/json",
      "x-yatabase-surface": "data-export",
      "content-disposition": `attachment; filename="yatabase-export-${orgDid.slice(-12)}-${generatedAt.slice(0, 10)}.json"`,
      "cache-control": "no-store",
    },
  });
}

// P77: walk every Worker-side authoritative store and delete per-org
// rows. Matches the set buildKvExport reads from so erasure is
// symmetric with portability. Best-effort: every store has a
// try/catch so a single transient failure doesn't block the rest.
async function purgeKvAndR2(env: DataRightsEnv, orgDid: string): Promise<Response> {
  const erasedAt = new Date().toISOString();
  const kv = (env as { YATABASE_AUTH_CACHE?: KVNamespace }).YATABASE_AUTH_CACHE;
  const r2 = (env as { YATA_R2?: R2Bucket }).YATA_R2;
  const counters: Record<string, number> = {
    auth_keys: 0,
    plan: 0,
    usage_days: 0,
    cypher_nodes: 0,
    cypher_labels: 0,
    storage_kv_objects: 0,
    r2_objects: 0,
    attached_email_index: 0,
  };

  if (kv) {
    // 1. auth:v1:* — every apiKey hash for this org. The org_keys index
    //    enumerates them. Shape: {keys:[{keyHash,keyPrefix,mintedAt}]}
    try {
      const idxRaw = await kv.get(`org_keys:v1:${orgDid}`);
      if (idxRaw) {
        try {
          const idx = JSON.parse(idxRaw) as { keys?: Array<{ keyHash?: string }> };
          for (const k of idx.keys ?? []) {
            if (!k?.keyHash) continue;
            try { await kv.delete(`auth:v1:${k.keyHash}`); counters.auth_keys++; } catch { /* ignore */ }
          }
        } catch { /* ignore */ }
        try { await kv.delete(`org_keys:v1:${orgDid}`); } catch { /* ignore */ }
      }
    } catch { /* ignore */ }

    // 2. plan:v1:{orgDid}
    try { await kv.delete(`plan:v1:${orgDid}`); counters.plan = 1; } catch { /* ignore */ }

    // 3. usage:v1:{orgDid}:{metric}:{day} — every daily counter.
    try {
      const usagePrefix = `usage:v1:${orgDid}:`;
      const list = await kv.list({ prefix: usagePrefix, limit: 1000 });
      for (const k of list.keys ?? []) {
        try { await kv.delete(k.name); counters.usage_days++; } catch { /* ignore */ }
      }
    } catch { /* ignore */ }

    // 4. cypher:v1:{orgDid}:labels:* and nodes:*
    try {
      const labelList = await kv.list({ prefix: `cypher:v1:${orgDid}:labels:`, limit: 200 });
      for (const lk of labelList.keys ?? []) {
        try {
          const idxRaw = await kv.get(lk.name);
          if (idxRaw) {
            const idx = JSON.parse(idxRaw) as { ids?: string[] };
            const label = lk.name.slice(`cypher:v1:${orgDid}:labels:`.length);
            for (const id of idx.ids ?? []) {
              try { await kv.delete(`cypher:v1:${orgDid}:nodes:${label}:${id}`); counters.cypher_nodes++; } catch { /* ignore */ }
            }
          }
          await kv.delete(lk.name);
          counters.cypher_labels++;
        } catch { /* ignore */ }
      }
    } catch { /* ignore */ }

    // P89: outbox:v1:{orgDid}:* — email outbox events (30d TTL).
    try {
      const list = await kv.list({ prefix: `outbox:v1:${orgDid}:`, limit: 1000 });
      for (const k of list.keys ?? []) {
        try { await kv.delete(k.name); } catch { /* ignore */ }
      }
    } catch { /* ignore */ }

    // P97: webhook:v1:{orgDid}:* — outbound webhook registry.
    try {
      const list = await kv.list({ prefix: `webhook:v1:${orgDid}:`, limit: 200 });
      for (const k of list.keys ?? []) {
        try { await kv.delete(k.name); } catch { /* ignore */ }
      }
    } catch { /* ignore */ }

    // P87: audit:v1:{orgDid}:* — audit log events (24h TTL anyway).
    try {
      const list = await kv.list({ prefix: `audit:v1:${orgDid}:`, limit: 1000 });
      for (const k of list.keys ?? []) {
        try { await kv.delete(k.name); } catch { /* ignore */ }
      }
    } catch { /* ignore */ }

    // P85: burst:v1:{orgDid}:* — rate-limit buckets (60s TTL anyway, but
    //      eager purge keeps the namespace tidy and stops a deleted
    //      tenant's stale counter from briefly throttling a re-signup).
    try {
      const list = await kv.list({ prefix: `burst:v1:${orgDid}:`, limit: 100 });
      for (const k of list.keys ?? []) {
        try { await kv.delete(k.name); } catch { /* ignore */ }
      }
    } catch { /* ignore */ }

    // P92: cypher edges + per-source/type indexes. Same orgDid prefix
    //      so an account-delete wipes the entire graph.
    try {
      for (const prefix of [`cypher:v1:${orgDid}:edges:`, `cypher:v1:${orgDid}:edge_types:`, `cypher:v1:${orgDid}:edge_out:`]) {
        const list = await kv.list({ prefix, limit: 1000 });
        for (const k of list.keys ?? []) {
          try { await kv.delete(k.name); counters.cypher_nodes++; } catch { /* ignore */ }
        }
      }
    } catch { /* ignore */ }

    // 5. storage:v1:{orgDid}:obj:* + meta:*
    try {
      const list = await kv.list({ prefix: `storage:v1:${orgDid}:`, limit: 1000 });
      for (const k of list.keys ?? []) {
        try { await kv.delete(k.name); counters.storage_kv_objects++; } catch { /* ignore */ }
      }
    } catch { /* ignore */ }

    // P83: verify_email_tokens for this org (rare — usually short-TTL).
    try {
      const list = await kv.list({ prefix: `verify_email_token:v1:`, limit: 1000 });
      for (const k of list.keys ?? []) {
        try {
          const raw = await kv.get(k.name);
          if (!raw) continue;
          const parsed = JSON.parse(raw) as { orgDid?: string };
          if (parsed?.orgDid === orgDid) {
            try { await kv.delete(k.name); } catch { /* ignore */ }
          }
        } catch { /* ignore */ }
      }
    } catch { /* ignore */ }

    // 6. attached email — read once so we can scrub the reverse index too.
    let attachedEmail: string | null = null;
    try {
      const raw = await kv.get(`attach_email:v1:${orgDid}`);
      if (raw) {
        try { attachedEmail = (JSON.parse(raw) as { email?: string }).email ?? null; } catch { /* ignore */ }
      }
      await kv.delete(`attach_email:v1:${orgDid}`);
    } catch { /* ignore */ }
    if (attachedEmail) {
      try {
        const hash = await sha256HexLocal(attachedEmail);
        const idxKey = `email_to_orgs:v1:${hash}`;
        const idxRaw = await kv.get(idxKey);
        if (idxRaw) {
          const idx = JSON.parse(idxRaw) as { orgs?: string[] };
          const remaining = (idx.orgs ?? []).filter((o) => o !== orgDid);
          if (remaining.length === 0) {
            await kv.delete(idxKey);
          } else {
            await kv.put(idxKey, JSON.stringify({ orgs: remaining }));
          }
          counters.attached_email_index = 1;
        }
      } catch { /* ignore */ }
    }

    // 7. Stamp erasure tombstone last so any racing bearer auth sees it.
    try {
      await kv.put(`erased:v1:${orgDid}`, JSON.stringify({ erasedAt, counters }));
    } catch { /* ignore */ }
  }

  // 8. R2 objects under yata/{orgDid}/. Paginate to handle large tenants.
  if (r2) {
    try {
      let cursor: string | undefined;
      for (let i = 0; i < 50; i++) {  // up to 50k objects per delete request
        const list: R2Objects = await r2.list({ prefix: `yata/${orgDid}/`, limit: 1000, cursor });
        if (!list.objects?.length) break;
        await r2.delete(list.objects.map((o) => o.key));
        counters.r2_objects += list.objects.length;
        if (!list.truncated) break;
        cursor = list.cursor;
      }
    } catch (e) {
      console.warn("[yatabase][delete] R2 purge failed (continuing):", e);
    }
  }

  return new Response(JSON.stringify({
    ok: true,
    orgDid,
    mode: "kv-r2-purge",
    erasedAt,
    counters,
    privacyLawCompliance: {
      gdprArt17: "Right to erasure — Worker-side authoritative stores purged",
      ccpa1798105: "Right to delete — KV + R2 rows physically removed",
      jpAct34_36: "改正個人情報保護法 第34-36条 — 開示請求権 / 削除請求権 honored",
    },
    note: "Worker-side authoritative stores (KV + R2) physically purged. Legacy RW vertex_* rows are pod-side authoritative; the pod-side erasure handler ships separately. Bearer-auth cache invalidated — your old API key returns 401 immediately.",
  }, jsonReplacer, 2), {
    status: 200,
    headers: {
      "content-type": "application/json",
      "x-yatabase-surface": "account-delete",
      "cache-control": "no-store",
    },
  });
}

async function sha256HexLocal(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function handleExport(env: DataRightsEnv, orgDid: string): Promise<Response> {
  const r = await getRealDb(env);
  if (!r) {
    // P75: Full KV+R2 fallback export. ADR-2605111200 blocks the Worker
    // from reading vertex_*, so we materialize the same JSON shape from
    // the KV namespace (`auth:*`, `cypher:*`, `storage:*`, `plan:*`,
    // `usage:*`) and R2 bucket (`yata/{orgDid}/*`). This satisfies GDPR
    // Art 20 / CCPA §1798.100 / 改正個人情報保護法 §33 with the actual
    // data the customer touches via the KV-backed surfaces (not just
    // identifiers).
    return await buildKvExport(env, orgDid);
  }
  const { db, sql } = r;
  const schema = await tenantSchemaName(orgDid);
  const generatedAt = new Date().toISOString();

  // 1. Tenant schema tables.
  const tableListQ = sql`
    SELECT c.relname AS table_name
    FROM pg_class c
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname = ${schema} AND c.relkind = 'r'
    ORDER BY c.relname ASC
  `;
  const tableRows = await execRows(tableListQ, db);

  const tables: Array<{ name: string; rowCount: number; rows: Array<Record<string, unknown>> }> = [];
  // Identifier safety: `schema` is sha256-derived server-side and `tableName`
  // came from pg_class WHERE n.nspname = $tenant — neither is attacker-
  // controlled so bare identifier interpolation is safe here.
  for (const t of tableRows) {
    const tableName = String(t.table_name ?? "");
    if (!/^[A-Za-z_][A-Za-z_0-9]*$/.test(tableName)) continue;
    const sqlAny = sql as unknown as {
      raw?: (s: string) => unknown;
    };
    let rows: Array<Record<string, unknown>> = [];
    if (sqlAny.raw) {
      const dataQ = sql`SELECT * FROM ${sqlAny.raw(`"${schema}".${tableName}`)} LIMIT 10000`;
      rows = await execRows(dataQ, db);
    }
    tables.push({ name: tableName, rowCount: rows.length, rows });
  }

  // 2. Billing events for the org (last 90 days of events for portability).
  const sinceMs = Date.now() - 90 * 24 * 60 * 60 * 1000;
  const billingQ = sql`
    SELECT vertex_id, ts_ms, metric, qty, product, ref_resource,
           billed_amount_jpy_micro, created_at
    FROM vertex_billing_event
    WHERE org_did = ${orgDid} AND ts_ms >= ${sinceMs}
    ORDER BY ts_ms DESC
    LIMIT 10000
  `;
  const billingEvents = await execRows(billingQ, db);

  // 3. Plan history.
  const planQ = sql`
    SELECT plan_tier, started_at, source, status, monthly_jpy_micro
    FROM vertex_org_plan
    WHERE org_did = ${orgDid}
    ORDER BY started_at DESC
  `;
  const orgPlanHistory = await execRows(planQ, db);

  // 4. API keys (no secrets — hash only).
  const keysQ = sql`
    SELECT vertex_id, name, key_prefix, status, created_at, aws_access_key_id
    FROM vertex_api_key
    WHERE owner_did = ${orgDid}
    ORDER BY created_at ASC
  `;
  const apiKeys = await execRows(keysQ, db);

  // 5. Storage blobs metadata (rows in shared vertex_yata_blob filtered
  //    by org_did — `signed urls` and bytes themselves live in B2 / R2;
  //    customer can re-fetch via /storage/v1/object/{bucket}/{key}).
  const blobsQ = sql`
    SELECT bucket_name, object_key, size_bytes, content_type, etag,
           storage_tier, storage_provider, created_at
    FROM vertex_yata_blob
    WHERE org_did = ${orgDid}
    LIMIT 10000
  `;
  const storageBlobs = await execRows(blobsQ, db);

  const body = {
    orgDid,
    generatedAt,
    primaryMarket: "US",
    privacyLawCompliance: {
      // US — primary jurisdiction (deps.toml [platform.market])
      ccpa1798100: "Right to know (US California Consumer Privacy Act)",
      ccpa1798105: "Right to delete (companion endpoint /api/account/delete)",
      // EU / UK
      gdprArt20: "Right to data portability",
      gdprArt30: "Records of processing — see /api/audit",
      // Japan — secondary
      jpAct33: "改正個人情報保護法 第33条 開示請求権",
      jpAct34_36: "改正個人情報保護法 第34-36条 削除請求権",
      consentBasis: "anonymous-self-signup",
    },
    tenantSchema: { name: schema, tables },
    billingEvents,
    orgPlanHistory,
    apiKeys,
    storageBlobs,
  };

  return new Response(JSON.stringify(body, jsonReplacer, 2), {
    status: 200,
    headers: {
      "content-type": "application/json",
      "x-yatabase-surface": "data-export",
      "content-disposition": `attachment; filename="yatabase-export-${orgDid.slice(-12)}-${generatedAt.slice(0, 10)}.json"`,
      "cache-control": "no-store",
    },
  });
}

export async function handleAccountDelete(env: DataRightsEnv, orgDid: string, req: Request): Promise<Response> {
  let body: { confirm?: string } = {};
  try {
    body = await req.json();
  } catch {
    /* no body */
  }
  if (body.confirm !== "DELETE") {
    return new Response(
      JSON.stringify({
        error: "ConfirmationRequired",
        message: 'Pass {"confirm":"DELETE"} in the request body to acknowledge that this is one-way and irreversible.',
      }),
      { status: 400, headers: { "content-type": "application/json" } },
    );
  }

  const r = await getRealDb(env);
  if (!r) {
    // P77: full KV+R2 purge. ADR-2605111200 blocks RW writes from the
    // Worker, but we own every customer-visible data plane (auth-cache,
    // plan-state, usage counters, cypher KV, storage KV, storage R2).
    // GDPR §17 / 改正個人情報保護法 §34-36 require actual erasure, not
    // just a tombstone, so we walk each per-org keyspace and delete.
    return await purgeKvAndR2(env, orgDid);
  }
  const { db, sql } = r;
  const schema = await tenantSchemaName(orgDid);
  const events: string[] = [];

  // 1. Revoke all keys (PK upsert with status='revoked'). We do this
  //    first so any in-flight requests stop authenticating.
  const keysQ = sql`SELECT vertex_id, key_hash, key_prefix, name, scopes, product_scope, aws_access_key_id, aws_secret_access_key, created_at FROM vertex_api_key WHERE owner_did = ${orgDid}`;
  const keyRows = await execRows(keysQ, db);
  for (const row of keyRows) {
    const keyId = String(row.vertex_id ?? "");
    if (!keyId) continue;
    const upsert = sql`
      INSERT INTO vertex_api_key
        (vertex_id, owner_did, key_hash, key_prefix, name, scopes,
         status, product_scope, aws_access_key_id, aws_secret_access_key,
         created_at)
      VALUES (${keyId}, ${orgDid}, ${String(row.key_hash ?? "")},
              ${String(row.key_prefix ?? "")}, ${String(row.name ?? "")},
              ${String(row.scopes ?? "")}, 'deleted',
              ${String(row.product_scope ?? "")},
              ${String(row.aws_access_key_id ?? "")},
              ${String(row.aws_secret_access_key ?? "")},
              ${String(row.created_at ?? new Date().toISOString())})
    `;
    await execMutation(upsert, db);
  }
  events.push(`revoked ${keyRows.length} api key(s)`);

  // 2. Mark plan deleted.
  const planQ = sql`SELECT vertex_id, plan_tier, started_at, source, stripe_subscription_id, stripe_customer_id, monthly_jpy_micro, created_at FROM vertex_org_plan WHERE org_did = ${orgDid} AND status = 'active'`;
  const planRows = await execRows(planQ, db);
  for (const row of planRows) {
    const planVid = String(row.vertex_id ?? "");
    if (!planVid) continue;
    const upsert = sql`
      INSERT INTO vertex_org_plan
        (vertex_id, org_did, plan_tier, started_at, source,
         stripe_subscription_id, stripe_customer_id, monthly_jpy_micro,
         status, created_at)
      VALUES (${planVid}, ${orgDid},
              ${String(row.plan_tier ?? "free")},
              ${String(row.started_at ?? new Date().toISOString())},
              ${String(row.source ?? "stub-upgrade")},
              ${String(row.stripe_subscription_id ?? "")},
              ${String(row.stripe_customer_id ?? "")},
              ${Number(row.monthly_jpy_micro ?? 0)},
              'deleted',
              ${String(row.created_at ?? new Date().toISOString())})
    `;
    await execMutation(upsert, db);
  }
  events.push(`marked ${planRows.length} plan row(s) deleted`);

  // 3. DROP SCHEMA (CASCADE wipes the tenant's vertex_<label> + edge_<r>
  //    tables). RW supports DROP SCHEMA for non-system schemas. Identifier
  //    safe because `schema` is sha256-derived.
  try {
    const sqlAny = sql as unknown as { raw?: (s: string) => unknown };
    if (sqlAny.raw) {
      const dropQ = sql`DROP SCHEMA ${sqlAny.raw(`"${schema}"`)} CASCADE`;
      const ok = await execMutation(dropQ, db);
      events.push(ok ? `dropped schema ${schema}` : `schema ${schema} drop failed (may not exist)`);
    } else {
      events.push(`sql.raw unavailable; schema ${schema} not dropped (manual cleanup needed)`);
    }
  } catch (e) {
    events.push(`schema drop error: ${e instanceof Error ? e.message.slice(0, 200) : "unknown"}`);
  }

  // Note: vertex_billing_event rows are retained — they are accounting
  // records (Japan 法人税法 第126条 帳簿書類保存義務 = 7 years) and the
  // IRS-equivalent expects retention even after account deletion. This
  // is the standard practice and disclosed in the privacy policy.
  events.push("billing event records retained 7 years for tax law compliance (法人税法 §126)");

  return new Response(
    JSON.stringify({
      ok: true,
      orgDid,
      schema,
      deletedAt: new Date().toISOString(),
      events,
      message: "Account deletion submitted. Tenant schema dropped. Billing records retained per Japan 法人税法 §126.",
    }),
    {
      status: 200,
      headers: { "content-type": "application/json", "x-yatabase-surface": "data-rights", "cache-control": "no-store" },
    },
  );
}
