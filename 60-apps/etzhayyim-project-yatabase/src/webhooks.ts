// webhooks.ts — outbound webhook registry + dispatch (P97).
//
// Customers register a URL + secret + filter; yatabase POSTs JSON
// events to it when matching Cypher mutations happen. Per-org KV
// storage; HMAC signing for integrity.
//
// Endpoints:
//   POST   /api/webhooks          register { url, secret?, label?, types[]? }
//   GET    /api/webhooks          list registered webhooks
//   DELETE /api/webhooks/{id}     remove a webhook
//
// Dispatch fires from cypher-kv.ts on CREATE / SET / DELETE /
// CREATE_EDGE / DELETE_EDGE (whichever the customer subscribed to).
// Each delivery includes:
//   - X-Yatabase-Event: cypher.create | cypher.set | cypher.delete |
//                       cypher.create_edge | cypher.delete_edge
//   - X-Yatabase-Signature: hex(hmac-sha256(secret, body))
//   - X-Yatabase-Delivery: random nanoid for tracing
//   - Body: { event, orgDid, label?, type?, props?, srcProps?,
//             dstProps?, ts }
//
// Delivery is fire-and-forget via waitUntil — the cypher write
// returns 200 to the customer regardless of webhook reachability.
// Failed deliveries are NOT retried in v1 (the next mutation would
// re-fire). Per-org cap: 10 webhooks.

export type WebhookEvent =
  | "cypher.create"
  | "cypher.set"
  | "cypher.delete"
  | "cypher.create_edge"
  | "cypher.delete_edge";

export interface WebhookRow {
  id: string;
  url: string;
  secret: string;       // 32 hex chars; never returned in GET responses
  label?: string;       // filter — fire only when label matches
  types: WebhookEvent[];
  createdAt: string;
}

const WEBHOOK_PREFIX = "webhook:v1:";
const PER_ORG_MAX = 10;

function indexKey(orgDid: string): string {
  return `${WEBHOOK_PREFIX}${orgDid}:index`;
}
function webhookKey(orgDid: string, id: string): string {
  return `${WEBHOOK_PREFIX}${orgDid}:${id}`;
}

function randomHex(byteCount: number): string {
  const buf = new Uint8Array(byteCount);
  crypto.getRandomValues(buf);
  return Array.from(buf).map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function hmacHex(secret: string, body: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(body));
  return Array.from(new Uint8Array(sig)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

const ALL_EVENTS: WebhookEvent[] = [
  "cypher.create", "cypher.set", "cypher.delete",
  "cypher.create_edge", "cypher.delete_edge",
];

export async function listWebhooks(
  kv: KVNamespace,
  orgDid: string,
): Promise<WebhookRow[]> {
  try {
    const raw = await kv.get(indexKey(orgDid));
    if (!raw) return [];
    const idx = JSON.parse(raw) as { ids?: string[] };
    const rows: WebhookRow[] = [];
    for (const id of idx.ids ?? []) {
      const rowRaw = await kv.get(webhookKey(orgDid, id));
      if (!rowRaw) continue;
      try { rows.push(JSON.parse(rowRaw) as WebhookRow); } catch { /* ignore */ }
    }
    return rows;
  } catch {
    return [];
  }
}

export async function registerWebhook(
  kv: KVNamespace,
  orgDid: string,
  input: { url: string; secret?: string; label?: string; types?: WebhookEvent[] },
): Promise<{ ok: true; webhook: WebhookRow } | { ok: false; status: number; error: string; message: string }> {
  try {
    const u = new URL(input.url);
    if (u.protocol !== "https:") {
      return { ok: false, status: 400, error: "BadRequest", message: "url must be https://" };
    }
  } catch {
    return { ok: false, status: 400, error: "BadRequest", message: "url is not a valid URL" };
  }
  const existing = await listWebhooks(kv, orgDid);
  if (existing.length >= PER_ORG_MAX) {
    return {
      ok: false, status: 409, error: "WebhookCapExceeded",
      message: `Per-org webhook cap: ${PER_ORG_MAX}. DELETE one before adding another.`,
    };
  }
  const id = `whk_${randomHex(8)}`;
  const types = (input.types && input.types.length > 0)
    ? input.types.filter((t) => ALL_EVENTS.includes(t))
    : [...ALL_EVENTS];
  const row: WebhookRow = {
    id,
    url: input.url,
    secret: input.secret && input.secret.length >= 8 ? input.secret : randomHex(16),
    label: input.label,
    types,
    createdAt: new Date().toISOString(),
  };
  await kv.put(webhookKey(orgDid, id), JSON.stringify(row));
  const idxRaw = await kv.get(indexKey(orgDid));
  const idx = idxRaw ? JSON.parse(idxRaw) as { ids?: string[] } : { ids: [] };
  idx.ids = [...(idx.ids ?? []), id];
  await kv.put(indexKey(orgDid), JSON.stringify(idx));
  return { ok: true, webhook: row };
}

export async function deleteWebhook(
  kv: KVNamespace,
  orgDid: string,
  id: string,
): Promise<{ ok: boolean }> {
  try {
    await kv.delete(webhookKey(orgDid, id));
    const idxRaw = await kv.get(indexKey(orgDid));
    if (idxRaw) {
      const idx = JSON.parse(idxRaw) as { ids?: string[] };
      idx.ids = (idx.ids ?? []).filter((x) => x !== id);
      await kv.put(indexKey(orgDid), JSON.stringify(idx));
    }
    return { ok: true };
  } catch {
    return { ok: false };
  }
}

// P97: dispatchEvent — fire any matching registered webhooks for the
// given event. Caller is expected to wrap in waitUntil so the request
// hot path isn't blocked.
export async function dispatchWebhookEvent(
  kv: KVNamespace,
  orgDid: string,
  event: WebhookEvent,
  payload: Record<string, unknown>,
): Promise<void> {
  try {
    const hooks = await listWebhooks(kv, orgDid);
    if (hooks.length === 0) return;
    const targeted = hooks.filter((h) => {
      if (!h.types.includes(event)) return false;
      if (h.label) {
        const label = String(payload.label ?? payload.srcLabel ?? "");
        if (label !== h.label) return false;
      }
      return true;
    });
    if (targeted.length === 0) return;
    const body = JSON.stringify({ event, orgDid, ...payload, ts: new Date().toISOString() });
    await Promise.all(targeted.map(async (h) => {
      try {
        const sig = await hmacHex(h.secret, body);
        const deliveryId = `dlv_${randomHex(8)}`;
        await fetch(h.url, {
          method: "POST",
          headers: {
            "content-type": "application/json",
            "x-yatabase-event": event,
            "x-yatabase-signature": sig,
            "x-yatabase-delivery": deliveryId,
          },
          body,
        });
      } catch (e) {
        console.warn(`[yatabase][webhook] delivery failed id=${h.id}:`, e);
      }
    }));
  } catch (e) {
    console.warn("[yatabase][webhook] dispatch failed:", e);
  }
}

// Strip the secret before returning to /api/webhooks GET. Customer
// gets one chance to see the secret — in the POST /api/webhooks
// register response.
export function redactWebhook(row: WebhookRow): Omit<WebhookRow, "secret"> & { secretPrefix: string } {
  return {
    id: row.id,
    url: row.url,
    label: row.label,
    types: row.types,
    createdAt: row.createdAt,
    secretPrefix: row.secret.slice(0, 8) + "…",
  };
}
