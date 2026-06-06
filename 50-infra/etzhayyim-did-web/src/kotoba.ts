/**
 * kotoba pull path for actor records — tier-2 of resolveActorRecord.
 * Per ADR-2606013800 + ADR-2605312345 (Datom log = first-class canonical state).
 *
 * Reads a single actor entity from the public `actors-v1` kotoba graph over the
 * kotoba XRPC surface (`com.etzhayyim.apps.kotobase.kg.entity`). Public graph → no
 * auth / CACAO needed. Best-effort: ANY failure (endpoint unset, network error,
 * unexpected shape) returns null so the caller falls through to the compiled
 * INFRA_ACTORS fallback and did:web resolution never goes dark.
 *
 * The actor entity is ingested by the publisher with:
 *   id     = "actor.<handle>"
 *   claims = [{pred:"actor/<attr>", value:"..."}, ...]  (service[]/vm[] are
 *            carried as the JSON-encoded claims actor/service-json + actor/vm-json)
 */

import {
  coerceActorRecord,
  type ActorRecord,
} from "./registry/actor-profiles";

export interface KotobaEnv {
  readonly KOTOBA_ENDPOINT?: string;
  readonly KOTOBA_WRITE_ENDPOINT?: string;
  readonly AUTHZ_CONTRACT_ADDRESS?: string;
}

/** Outcome of a best-effort kotoba account publish. */
export type AccountWriteOutcome = "written" | "gated" | "error";

/**
 * Publish a member account record (handle alias + controller did:key + profile)
 * to the kotoba node (ADR-2606061800). CACAO control is verified by the caller;
 * this only relays the authorized write. No write endpoint configured → "gated"
 * (honest R0 — login still works, the alias just isn't published yet).
 */
export async function putKotobaAccount(
  env: KotobaEnv,
  did: string,
  handle: string,
  profile: Record<string, unknown>,
): Promise<AccountWriteOutcome> {
  const base = env.KOTOBA_WRITE_ENDPOINT;
  if (!base) return "gated";
  const url =
    `${base.replace(/\/$/, "")}/xrpc/com.etzhayyim.apps.kotobase.account.register`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ did, handle, profile }),
      signal: AbortSignal.timeout(KOTOBA_TIMEOUT_MS),
    });
    return res.ok ? "written" : "error";
  } catch {
    return "error";
  }
}

const KOTOBA_TIMEOUT_MS = 1200;

interface KgClaim {
  pred?: string;
  value?: unknown;
}

/** Flatten a kotoba entity's claims into the loosely-typed object that
 *  coerceActorRecord understands. */
function claimsToRecordObject(
  handle: string,
  claims: KgClaim[],
  labelEn?: string,
): Record<string, unknown> {
  const o: Record<string, unknown> = { handle };
  const adr: string[] = [];
  for (const c of claims) {
    if (!c || typeof c.pred !== "string") continue;
    const pred = c.pred.startsWith("actor/") ? c.pred.slice("actor/".length) : c.pred;
    const value = c.value;
    switch (pred) {
      case "adr":
        if (typeof value === "string") adr.push(value);
        else if (Array.isArray(value)) adr.push(...value.map(String));
        break;
      case "service-json":
        try {
          o.service = JSON.parse(String(value));
        } catch {
          /* leave service unset → coerce defaults to [] */
        }
        break;
      case "vm-json":
        try {
          o.vm = JSON.parse(String(value));
        } catch {
          /* leave vm unset → [] */
        }
        break;
      case "performer-type":
        o.performerType = String(value);
        break;
      case "ui-type":
        o.uiType = String(value);
        break;
      case "display-name-ja":
        o.displayNameJa = String(value);
        break;
      case "display-name-en":
        o.displayNameEn = String(value);
        break;
      case "primary-lexicon":
        o.primaryLexicon = String(value);
        break;
      case "primary-schema":
        o.primarySchema = String(value);
        break;
      case "created-at":
        o.createdAt = String(value);
        break;
      default:
        // handle, did, kind, tier, status, glyph, description, avatar, banner
        if (typeof value === "string") o[pred] = value;
    }
  }
  if (adr.length) o.adr = adr;
  if (labelEn && !o.displayNameEn) o.displayNameEn = labelEn;
  return o;
}

/** Fetch an actor record from kotoba. Returns null on any failure (best-effort). */
export async function fetchKotobaActorRecord(
  env: KotobaEnv,
  handle: string,
): Promise<ActorRecord | null> {
  const base = env.KOTOBA_ENDPOINT;
  if (!base) return null;
  const url =
    `${base.replace(/\/$/, "")}/xrpc/com.etzhayyim.apps.kotobase.kg.entity` +
    `?id=${encodeURIComponent(`actor.${handle}`)}`;
  try {
    const res = await fetch(url, {
      method: "GET",
      headers: { accept: "application/json" },
      signal: AbortSignal.timeout(KOTOBA_TIMEOUT_MS),
    });
    if (!res.ok) return null;
    const body = (await res.json()) as Record<string, unknown>;

    // Shape A: a dedicated endpoint already returns a flat actor record.
    if (typeof body.handle === "string") {
      return coerceActorRecord(body, "kotoba");
    }
    // Shape B: a kotoba entity { id, kind, label_en, claims: [{pred,value}] }.
    const entity = (
      typeof body.entity === "object" && body.entity !== null
        ? (body.entity as Record<string, unknown>)
        : body
    );
    const claims = Array.isArray(entity.claims)
      ? (entity.claims as KgClaim[])
      : [];
    if (claims.length === 0) return null;
    const labelEn =
      typeof entity.label_en === "string" ? entity.label_en : undefined;
    const obj = claimsToRecordObject(handle, claims, labelEn);
    return coerceActorRecord(obj, "kotoba");
  } catch {
    return null;
  }
}
