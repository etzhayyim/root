// org-members.ts — Org / member management (P9).
//
// Model:
//   1 tenant = 1 org_did = N API keys. The first key created at signup
//   is the org owner. Subsequent keys are minted by the owner (or any
//   active member) via /auth/v1/invite and inherit the same `owner_did`
//   = `org_did`. All keys see the same tenant schema, share the same
//   plan tier, and accumulate billing under the same org.
//
// Endpoints:
//   GET  /api/members                  list keys for caller's org
//   POST /auth/v1/invite { name }      mint a new key for the same org
//   POST /auth/v1/revoke { keyId }     status='revoked' on a key (owner-only
//                                      check is the same authenticated org)
//
// Roles (P9 MVP):
//   owner  = first key in vertex_api_key for this org_did (oldest created_at)
//   member = any subsequent key
// Real RBAC (admin / developer / viewer) is deferred — for MVP every active
// member can invite + revoke.

export interface OrgEnv {
  HYPERDRIVE?: unknown;
}

interface AnyKyselyDb {
  insertInto(table: string): {
    values(row: Record<string, unknown>): { execute(): Promise<unknown> };
  };
  updateTable(table: string): {
    set(values: Record<string, unknown>): {
      where(col: string, op: string, val: unknown): {
        where(col: string, op: string, val: unknown): {
          execute(): Promise<unknown>;
        };
      };
    };
  };
}

async function getDb(env: OrgEnv): Promise<AnyKyselyDb | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@etzhayyim/magatama-host-sdk");
    return sdk.createKyselyDb(env.HYPERDRIVE as never) as unknown as AnyKyselyDb;
  } catch {
    return null;
  }
}

function generateApiKey(): string {
  const buf = new Uint8Array(24);
  crypto.getRandomValues(buf);
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let out = "sk_live_yata_";
  for (const b of buf) out += chars[b % chars.length];
  return out;
}

function generateAwsAccessKey(): { id: string; secret: string } {
  const buf = new Uint8Array(20);
  crypto.getRandomValues(buf);
  const idChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  let id = "gftd_";
  for (const b of buf) id += idChars[b % idChars.length];
  const sbuf = new Uint8Array(40);
  crypto.getRandomValues(sbuf);
  const secret = Array.from(sbuf)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return { id, secret };
}

async function sha256Hex(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

interface MemberRow {
  keyId: string;
  name: string;
  keyPrefix: string;
  status: string;
  createdAt: string;
  role: "owner" | "member";
  awsAccessKeyId: string;
}

export async function listMembers(env: OrgEnv, orgDid: string): Promise<{ orgDid: string; members: MemberRow[] }> {
  // P94: KV-first read. The auth-cache module already maintains a
  // per-org key index at `org_keys:v1:{orgDid}` with the keyHash +
  // keyPrefix + mintedAt for every signup/invite. Use it so Studio's
  // Members pane is populated even when RW is degraded.
  try {
    const { listCachedKeysForOrg } = await import("./auth-cache");
    const cached = await listCachedKeysForOrg(env as never, orgDid);
    if (cached.length > 0) {
      return {
        orgDid,
        members: cached.map((k, idx) => ({
          keyId: `apikey:${k.keyHash.slice(0, 16)}`,
          name: idx === 0 ? "owner" : `member-${idx}`,
          keyPrefix: k.keyPrefix,
          status: "active",
          createdAt: k.mintedAt,
          role: idx === 0 ? "owner" : "member" as const,
          awsAccessKeyId: "",
        })),
      };
    }
  } catch (e) {
    console.warn("[yatabase][members] KV list failed:", e);
  }

  let sqlTag: ((strings: TemplateStringsArray, ...values: unknown[]) => unknown) | null = null;
  try {
    const sdk = await import("@etzhayyim/magatama-host-sdk");
    sqlTag = (sdk as unknown as { sql?: typeof sqlTag }).sql ?? null;
  } catch {
    return { orgDid, members: [] };
  }
  if (!sqlTag) return { orgDid, members: [] };
  const db = await getDb(env);
  if (!db) return { orgDid, members: [] };

  const q = sqlTag`
    SELECT vertex_id AS key_id,
           name,
           key_prefix,
           status,
           created_at,
           aws_access_key_id
    FROM vertex_api_key
    WHERE owner_did = ${orgDid}
    ORDER BY created_at ASC
  `;
  let rows: Array<Record<string, unknown>> = [];
  try {
    const exec = (q as unknown as { execute: (db: unknown) => Promise<{ rows: Array<Record<string, unknown>> }> }).execute;
    const result = await exec.call(q, db);
    rows = result.rows ?? [];
  } catch (e) {
    console.warn("[yatabase][members] list failed:", e);
    return { orgDid, members: [] };
  }

  const members: MemberRow[] = rows.map((r, idx) => ({
    keyId: String(r.key_id ?? ""),
    name: String(r.name ?? ""),
    keyPrefix: String(r.key_prefix ?? ""),
    status: String(r.status ?? ""),
    createdAt: String(r.created_at ?? ""),
    role: idx === 0 ? "owner" : "member",
    awsAccessKeyId: String(r.aws_access_key_id ?? ""),
  }));
  return { orgDid, members };
}

interface InviteRequestBody {
  name?: string;
}

export async function handleInvite(env: OrgEnv, orgDid: string, req: Request): Promise<Response> {
  let body: InviteRequestBody = {};
  try {
    body = await req.json();
  } catch {
    /* empty body acceptable */
  }
  const name = String(body.name ?? "").trim().slice(0, 256) || `member-${Date.now()}`;

  // P65: prefer the lg-yatabase pod forwarder (ADR-2605111200 — Worker
  // no longer touches RW directly). Falls back to Workers-KV mint when
  // the pod path is unavailable so customers can still create member
  // keys during RW outages.
  if ((env as { LG_YATABASE_URL?: string }).LG_YATABASE_URL) {
    try {
      const { forwardInvite } = await import("./auth-forward");
      const fwd = await forwardInvite(
        env as never,
        { name },
        { did: orgDid, orgDid, activeDid: orgDid },
      );
      if (fwd.ok && fwd.data) {
        const podBody = fwd.data as Record<string, unknown>;
        if (typeof podBody.apiKey === "string" && typeof podBody.orgDid === "string") {
          try {
            const { rememberApiKeyResolution } = await import("./auth-cache");
            await rememberApiKeyResolution(env as never, podBody.apiKey, podBody.orgDid);
          } catch (e) {
            console.warn("[yatabase][invite] auth-cache fill failed:", e);
          }
        }
        return new Response(
          JSON.stringify({
            ...podBody,
            welcome: "Save this key — yatabase does not show it again. Share it with the new member out of band (e.g. via your password manager).",
            note: "The new member shares the same tenant schema, plan, and billing as you.",
          }),
          {
            status: 200,
            headers: {
              "content-type": "application/json",
              "x-yatabase-surface": "invite",
              "x-yatabase-invite-path": "lg-yatabase-pod",
              "cache-control": "no-store",
            },
          },
        );
      }
      console.warn(`[yatabase][invite] pod forward returned ${fwd.status}: ${fwd.error}`);
    } catch (e) {
      console.warn("[yatabase][invite] pod forward threw:", e);
    }
  }

  // P65 fallback: mint the key in KV directly. The new member can still
  // authenticate and use Cypher/Storage; the durable vertex_api_key row
  // will be backfilled via the pod's invite-replay job when RW recovers.
  const rawKey = generateApiKey();
  const keyHash = await sha256Hex(rawKey);
  const keyId = `apikey:${keyHash.slice(0, 16)}`;
  const aws = generateAwsAccessKey();
  try {
    const { rememberApiKeyResolution } = await import("./auth-cache");
    await rememberApiKeyResolution(env as never, rawKey, orgDid);
  } catch (e) {
    console.warn("[yatabase][invite] KV mint failed:", e);
    return new Response(
      JSON.stringify({ error: "ServiceUnavailable", message: "auth cache unavailable" }),
      { status: 503, headers: { "content-type": "application/json" } },
    );
  }

  return new Response(
    JSON.stringify({
      ok: true,
      apiKey: rawKey,
      keyId,
      orgDid,
      name,
      awsAccessKeyId: aws.id,
      welcome: "Save this key — yatabase does not show it again. Share it with the new member out of band (e.g. via your password manager).",
      note: "The new member shares the same tenant schema, plan, and billing as you.",
      mode: "kv-fallback",
    }),
    {
      status: 200,
      headers: {
        "content-type": "application/json",
        "x-yatabase-surface": "invite",
        "x-yatabase-invite-path": "kv-fallback",
        "cache-control": "no-store",
      },
    },
  );
}

interface RevokeRequestBody {
  keyId?: string;
}

export async function handleRevoke(env: OrgEnv, orgDid: string, req: Request): Promise<Response> {
  let body: RevokeRequestBody = {};
  try {
    body = await req.json();
  } catch {
    return new Response(
      JSON.stringify({ error: "BadRequest", message: "request body must be JSON" }),
      { status: 400, headers: { "content-type": "application/json" } },
    );
  }
  const keyId = String(body.keyId ?? "").trim();
  if (!/^apikey:[0-9a-f]{16}$/.test(keyId)) {
    return new Response(
      JSON.stringify({ error: "BadRequest", message: "keyId must match `apikey:[16 hex]`" }),
      { status: 400, headers: { "content-type": "application/json" } },
    );
  }

  // P104: KV revocation. /auth/v1/revoke had been RW-only — blocked since
  // ADR-2605111200 — so customers reporting key leaks couldn't actually
  // invalidate the leaked key. The auth-cache's `org_keys:v1:{orgDid}`
  // index maps keyId prefix (`apikey:{first 16 hex of keyHash}`) → keyHash.
  // We resolve the requested keyId to its full keyHash, then delete the
  // `auth:v1:{keyHash}` row + remove from the index. Next request with
  // the revoked bearer = 401 within KV propagation (typically <5s same POP).
  const kv = (env as { YATABASE_AUTH_CACHE?: KVNamespace }).YATABASE_AUTH_CACHE;
  let kvRevoked = false;
  if (kv) {
    try {
      const idxKey = `org_keys:v1:${orgDid}`;
      const idxRaw = await kv.get(idxKey);
      if (idxRaw) {
        const idx = JSON.parse(idxRaw) as { keys?: Array<{ keyHash: string; keyPrefix: string; mintedAt: string }> };
        const target = (idx.keys ?? []).find((k) => `apikey:${k.keyHash.slice(0, 16)}` === keyId);
        if (target) {
          try { await kv.delete(`auth:v1:${target.keyHash}`); kvRevoked = true; } catch { /* ignore */ }
          const remaining = (idx.keys ?? []).filter((k) => k !== target);
          await kv.put(idxKey, JSON.stringify({ keys: remaining }));
        }
      }
    } catch (e) {
      console.warn("[yatabase][revoke] KV revoke failed:", e);
    }
  }

  const db = await getDb(env);
  if (!db) {
    if (kvRevoked) {
      return new Response(
        JSON.stringify({ ok: true, keyId, mode: "kv-revoked", message: "Key revoked from auth-cache; next request with this bearer returns 401 within KV propagation." }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    }
    return new Response(
      JSON.stringify({ error: "NotFound", message: "no matching apiKey in KV index for this orgDid" }),
      { status: 404, headers: { "content-type": "application/json" } },
    );
  }

  // RW status='revoked' write. RW does not support PG UPDATE on every
  // shape consistently, so we use the proven pattern from cypher SET:
  // delete the old row + INSERT a replacement with status='revoked'. PK
  // is `vertex_id`; the new row has the same PK so RW upserts.
  let realDb: unknown = null;
  let sqlTag: ((strings: TemplateStringsArray, ...values: unknown[]) => unknown) | null = null;
  try {
    const sdk = await import("@etzhayyim/magatama-host-sdk");
    realDb = (sdk as unknown as { createKyselyDb: (h: unknown) => unknown }).createKyselyDb(env.HYPERDRIVE as never);
    sqlTag = (sdk as unknown as { sql?: typeof sqlTag }).sql ?? null;
  } catch {
    realDb = null;
    sqlTag = null;
  }
  if (!realDb || !sqlTag) {
    return new Response(
      JSON.stringify({ error: "ServiceUnavailable", message: "Kysely SDK unavailable" }),
      { status: 503, headers: { "content-type": "application/json" } },
    );
  }
  try {
    // First read the existing row so we can re-INSERT with all fields
    // intact + status='revoked'. RW PK upsert overrides the prior row.
    const selectQ = sqlTag`
      SELECT key_hash, key_prefix, name, scopes, product_scope,
             aws_access_key_id, aws_secret_access_key, created_at
      FROM vertex_api_key
      WHERE vertex_id = ${keyId} AND owner_did = ${orgDid}
      LIMIT 1
    `;
    const selectExec = (selectQ as unknown as { execute: (db: unknown) => Promise<{ rows: Array<Record<string, unknown>> }> }).execute;
    const selectResult = await selectExec.call(selectQ, realDb);
    const row = selectResult.rows?.[0];
    if (!row) {
      return new Response(
        JSON.stringify({ error: "NotFound", message: "no key with that vertex_id owned by this org" }),
        { status: 404, headers: { "content-type": "application/json" } },
      );
    }
    const insertQ = sqlTag`
      INSERT INTO vertex_api_key
        (vertex_id, owner_did, key_hash, key_prefix, name, scopes,
         status, product_scope, aws_access_key_id, aws_secret_access_key,
         created_at)
      VALUES (${keyId}, ${orgDid}, ${String(row.key_hash ?? "")},
              ${String(row.key_prefix ?? "")}, ${String(row.name ?? "")},
              ${String(row.scopes ?? "")}, 'revoked',
              ${String(row.product_scope ?? "")},
              ${String(row.aws_access_key_id ?? "")},
              ${String(row.aws_secret_access_key ?? "")},
              ${String(row.created_at ?? new Date().toISOString())})
    `;
    const insertExec = (insertQ as unknown as { execute: (db: unknown) => Promise<unknown> }).execute;
    await insertExec.call(insertQ, realDb);
  } catch (e) {
    console.warn("[yatabase][revoke] revoke flow failed:", e);
    return new Response(
      JSON.stringify({ error: "RevokeFailed", message: e instanceof Error ? e.message.slice(0, 300) : "operation failed" }),
      { status: 500, headers: { "content-type": "application/json" } },
    );
  }
  return new Response(
    JSON.stringify({
      ok: true,
      keyId,
      orgDid,
      message: "Key revoked. Auth resolution will refuse this key on the next request (RW eventual consistency may grant ~10-30s of grace period).",
    }),
    { status: 200, headers: { "content-type": "application/json" } },
  );
}
