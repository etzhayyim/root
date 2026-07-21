/**
 * Actor profile record — the canonical shape that backs BOTH the per-actor
 * did:web DID Document AND the app.bsky.actor.getProfile view. Per ADR-2606013800.
 *
 * SSoT layering (runtime resolution order, see worker.ts resolveActorRecord):
 *   1. CF KV (`actor:<handle>`)   — materialized by the publisher from kotoba
 *   2. kotoba `actors-v1` graph    — first-class canonical state (ADR-2605312345)
 *   3. compiled INFRA_ACTORS        — last-resort FALLBACK so did:web never goes
 *                                     dark (identity-live invariant)
 *
 * This module owns (a) the `ActorRecord` type, (b) `compiledActorRecord()` —
 * the tier-3 fallback derived from INFRA_ACTORS — and (c) the two pure mappers
 * `toDidDoc()` / `toGetProfileView()`. Both the worker and the publisher use
 * the SAME mappers so KV / kotoba / compiled all render byte-identical docs.
 */

import { INFRA_ACTORS, getInfraActor } from "./infra-actors";
import { cidV1Raw } from "../cid";
import { isRawCidV1 } from "../cid";

export interface ActorServiceEntry {
  readonly id: string;
  readonly type: string;
  readonly serviceEndpoint: string;
  readonly [k: string]: unknown;
}

/** verificationMethod entry — a MIRROR of the on-chain ERC725 key, never
 *  minted server-side (ADR-2605231525). Empty until chain wiring lands. */
export interface ActorVerificationMethod {
  readonly id: string;
  readonly type: string;
  readonly controller: string;
  readonly publicKeyJwk?: unknown;
  readonly [k: string]: unknown;
}

export type ActorSource = "kv" | "kotoba" | "compiled";

export interface ActorRecord {
  readonly handle: string;
  readonly did: string; // did:web:etzhayyim.com:actor:<handle>
  readonly kind: string; // tier-b | substrate-service | infra | agent | member
  readonly tier?: string;
  readonly status: string; // r0 | landed | shipped | retired
  readonly glyph?: string;
  readonly displayNameJa?: string;
  readonly displayNameEn?: string;
  readonly description: string;
  readonly avatar?: string;
  readonly banner?: string;
  readonly performerType?: string; // person | service | organization | system
  readonly uiType?: string; // appview | baminiku | iframe | none
  readonly primaryLexicon?: string;
  readonly primarySchema?: string;
  readonly adr: readonly string[];
  readonly service: readonly ActorServiceEntry[];
  readonly vm: readonly ActorVerificationMethod[];
  /** IPFS CID of the actor's content-addressed WASM component (kotoba WASM).
   *  When present, the DID doc carries an `EtzhayyimWasmComponent` service and
   *  the browser (ameno) / donated mesh node fetches + executes it locally —
   *  NO per-actor server. Per ADR-2606014500. */
  readonly wasmCid?: string;
  readonly createdAt?: string;
  readonly source: ActorSource;
}

/** did→handle: `did:web:etzhayyim.com:actor:tsumugi` → `tsumugi`.
 *  Also accepts the subdomain handle form `tsumugi.etzhayyim.com` and a bare
 *  handle. Returns null if the value is not an etzhayyim actor reference. */
export function actorHandleFromParam(value: string): string | null {
  const v = value.trim();
  if (!v) return null;
  const ACTOR_DID_PREFIX = "did:web:etzhayyim.com:actor:";
  if (v.startsWith(ACTOR_DID_PREFIX)) {
    const h = v.slice(ACTOR_DID_PREFIX.length).split(/[/#?]/)[0];
    return h.toLowerCase() || null;
  }
  // subdomain form: <handle>.etzhayyim.com (NOT atproto.etzhayyim.com etc. —
  // those are service hosts, not actor handles; the caller gates on isInfraActor)
  if (v.endsWith(".etzhayyim.com")) {
    return v.slice(0, -".etzhayyim.com".length).toLowerCase() || null;
  }
  // bare handle
  if (/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(v.toLowerCase())) {
    return v.toLowerCase();
  }
  return null;
}

/** Tier-3 fallback: derive an ActorRecord from the compiled INFRA_ACTORS. */
export function compiledActorRecord(handle: string): ActorRecord | null {
  const e = getInfraActor(handle);
  if (!e) return null;
  const named = Boolean(e.glyph);
  return {
    handle,
    did: `did:web:etzhayyim.com:actor:${handle}`,
    kind: named ? "tier-b" : "substrate-service",
    tier: named ? "B" : undefined,
    status: named ? "r0" : "landed",
    glyph: e.glyph,
    displayNameEn: e.displayName,
    description: e.description,
    performerType: named ? "system" : "service",
    uiType: named ? "appview" : "none",
    primaryLexicon: e.primaryLexicon,
    primarySchema: e.primarySchema,
    adr: [...e.adrs],
    service: e.service as readonly ActorServiceEntry[],
    vm: [],
    wasmCid: e.wasmCid,
    source: "compiled",
  };
}

/** Coerce a loosely-typed object (from KV JSON or a kotoba entity mapper) into
 *  an ActorRecord, filling derived defaults. Returns null if it lacks a handle. */
export function coerceActorRecord(
  o: Record<string, unknown>,
  source: ActorSource,
): ActorRecord | null {
  const handle = typeof o.handle === "string" ? o.handle.toLowerCase() : "";
  if (!handle) return null;
  const glyph = typeof o.glyph === "string" ? o.glyph : undefined;
  const named = Boolean(glyph);
  const str = (k: string): string | undefined =>
    typeof o[k] === "string" ? (o[k] as string) : undefined;
  return {
    handle,
    did: str("did") ?? `did:web:etzhayyim.com:actor:${handle}`,
    kind: str("kind") ?? (named ? "tier-b" : "substrate-service"),
    tier: str("tier"),
    status: str("status") ?? (named ? "r0" : "landed"),
    glyph,
    displayNameJa: str("displayNameJa"),
    displayNameEn: str("displayNameEn"),
    description: str("description") ?? "",
    avatar: str("avatar"),
    banner: str("banner"),
    performerType: str("performerType") ?? (named ? "system" : "service"),
    uiType: str("uiType") ?? (named ? "appview" : "none"),
    primaryLexicon: str("primaryLexicon"),
    primarySchema: str("primarySchema"),
    adr: Array.isArray(o.adr) ? (o.adr as string[]) : [],
    service: Array.isArray(o.service)
      ? (o.service as ActorServiceEntry[])
      : [],
    vm: Array.isArray(o.vm) ? (o.vm as ActorVerificationMethod[]) : [],
    wasmCid: str("wasmCid"),
    createdAt: str("createdAt"),
    source,
  };
}

export interface DidDocEnv {
  readonly AUTHZ_CONTRACT_ADDRESS?: string;
}

/** ActorRecord → W3C DID Document (did:web). Mirror-only verificationMethod:
 *  never minted here — `rec.vm` already carries the on-chain ERC725 key (or is
 *  empty, in which case the doc validates with an empty verificationMethod and
 *  did:web trust falls back to TLS). */
export function toDidDoc(
  rec: ActorRecord,
  env: DidDocEnv,
): Record<string, unknown> {
  const pathBasedDid = `did:web:etzhayyim.com:actor:${rec.handle}`;
  // NOTE: alsoKnownAs previously asserted an unconditional
  // `did:web:<handle>.etzhayyim.com` subdomain claim here. That subdomain has
  // no DNS record for any actor (verified 2026-07-21) and no ADR documents it
  // as a planned resolution address — it was a fabricated alias, not a real
  // one. Do not resurrect it without provisioning the DNS/route it claims.
  const alsoKnownAs: string[] = [];
  // chain-ref comes from the vm mirror when present; otherwise the scaffold
  // placeholder (same behaviour as the legacy buildPerActorDidDoc).
  const chainRef = rec.vm.find((v) => typeof v["chainRef"] === "string")?.[
    "chainRef"
  ] as string | undefined;
  if (chainRef) {
    alsoKnownAs.push(chainRef);
  } else if (env.AUTHZ_CONTRACT_ADDRESS) {
    alsoKnownAs.push(
      `did:erc725:base:${env.AUTHZ_CONTRACT_ADDRESS}#__rootId-pending-chain-lookup__`,
    );
  }
  // Self-certifying alias: if the actor has registered an Ed25519 key, expose it
  // as a `did:key` in alsoKnownAs (the key IS the identifier). This cross-links
  // the did:web handle to the key that signs the DID-doc attestation, completing
  // the trustless chain key → attestation → did.json CID (ADR-2606015600).
  for (const v of rec.vm) {
    if (v.type === "Ed25519VerificationKey2020" && typeof v["publicKeyMultibase"] === "string") {
      alsoKnownAs.push(`did:key:${v["publicKeyMultibase"]}`);
    }
  }
  // The actor's executable face: a content-addressed WASM component on IPFS.
  // Listed FIRST so a resolver prefers local execution (browser/donated mesh)
  // over any network transport — the "one Worker, many WASM actors" model
  // (ADR-2606014500). NO per-actor server.
  const service: Record<string, unknown>[] = [];
  if (rec.wasmCid) {
    // raw single-block CID (compact Rust/AS actor) → browser-local + mesh;
    // multi-block dag-pb CID (large componentize-py actor) → mesh only (a full
    // IPFS node verifies/loads it; not browser-local). Per ADR-2606014600/700.
    const raw = isRawCidV1(rec.wasmCid);
    service.push({
      id: `${pathBasedDid}#wasm`,
      type: "EtzhayyimWasmComponent",
      serviceEndpoint: `ipfs://${rec.wasmCid}`,
      "x-exec": raw ? "browser-local|donated-mesh" : "donated-mesh",
      "x-cid-codec": raw ? "raw" : "dag-pb",
      "x-runtime": "kotoba-wasm",
    });
  }
  service.push(...rec.service.map((s) => ({ ...s })));
  return {
    "@context": [
      "https://www.w3.org/ns/did/v1",
      "https://w3id.org/security/suites/jws-2020/v1",
    ],
    id: pathBasedDid,
    alsoKnownAs,
    verificationMethod: rec.vm.map((v) => ({ ...v })),
    service,
    _meta: {
      adr: ["2605212030", "2605241800", "2606013800", "2606014500", ...rec.adr],
      source: rec.source,
      kind: rec.kind,
      status: rec.status,
      glyph: rec.glyph,
      wasmCid: rec.wasmCid ?? null,
      execModel: rec.wasmCid ? "wasm-local (browser/donated-mesh)" : "service",
      primaryLexicon: rec.primaryLexicon,
      primarySchema: rec.primarySchema,
      note:
        rec.vm.length === 0
          ? "verificationMethod empty — on-chain ERC725 mirror pending; did:web trust root = TLS (no server-minted key, ADR-2605231525)"
          : "verificationMethod mirrors on-chain ERC725 Root.activeKey",
    },
  };
}

/** Canonical (content-addressable) DID document — `toDidDoc` with the one
 *  request-tier-volatile field (`_meta.source`) normalized to "ipfs", so the
 *  bytes (and therefore the CID) are identical no matter which tier (KV / kotoba
 *  / compiled) served the actor record. This is the form that gets pinned to
 *  IPFS and content-addressed for IPFS-based DID retrieval (ADR-2606015400).
 *  Trust: the handle→CID binding is still anchored by `etzhayyim.com` (TLS) /
 *  Base L2; IPFS makes the bytes tamper-evident, mirrorable, offline-verifiable. */
export function canonicalDidDoc(
  rec: ActorRecord,
  env: DidDocEnv = {},
): Record<string, unknown> {
  const doc = toDidDoc(rec, env);
  const meta = { ...(doc._meta as Record<string, unknown>), source: "ipfs" };
  return { ...doc, _meta: meta };
}

/** Deterministic JSON serialization of the canonical DID document (the exact
 *  bytes that get pinned + content-addressed). */
export function canonicalDidDocBytes(
  rec: ActorRecord,
  env: DidDocEnv = {},
): Uint8Array {
  return new TextEncoder().encode(JSON.stringify(canonicalDidDoc(rec, env)));
}

/** The IPFS CIDv1 (raw, sha2-256) of the actor's canonical DID document. Lets a
 *  client retrieve `did.json` from any IPFS gateway and verify it by CID. */
export function didDocCid(
  rec: ActorRecord,
  env: DidDocEnv = {},
): Promise<string> {
  return cidV1Raw(canonicalDidDocBytes(rec, env));
}

/** ActorRecord → app.bsky.actor.getProfile view (+ etzhayyim extensions that
 *  yoro's AgentProfile consumes: performerType / uiType / glyph / _etzhayyim). */
export function toGetProfileView(rec: ActorRecord): Record<string, unknown> {
  const displayName = rec.displayNameEn || rec.displayNameJa || rec.handle;
  return {
    did: rec.did,
    handle: `${rec.handle}.etzhayyim.com`,
    displayName,
    description: rec.description,
    avatar: rec.avatar ?? "",
    banner: rec.banner ?? "",
    followersCount: 0,
    followsCount: 0,
    postsCount: 0,
    indexedAt: rec.createdAt
      ? `${rec.createdAt}T00:00:00.000Z`
      : "1970-01-01T00:00:00.000Z",
    labels: [],
    viewer: {},
    // ── etzhayyim profile extensions (client-side agent rendering) ──
    performerType: rec.performerType ?? "system",
    uiType: rec.uiType ?? "appview",
    ...(rec.glyph ? { glyph: rec.glyph } : {}),
    ...(rec.displayNameJa ? { displayNameJa: rec.displayNameJa } : {}),
    _etzhayyim: {
      kind: rec.kind,
      tier: rec.tier ?? null,
      status: rec.status,
      adr: rec.adr,
      primaryLexicon: rec.primaryLexicon ?? null,
      primarySchema: rec.primarySchema ?? null,
      wasmComponent: rec.wasmCid ? `ipfs://${rec.wasmCid}` : null,
      didDocument: `https://etzhayyim.com/actor/${rec.handle}/did.json`,
      source: rec.source,
    },
  };
}

/** Handles known at compile time (used to gate the getProfile short-circuit
 *  so human-member profiles are never hijacked). */
export const COMPILED_ACTOR_HANDLES: ReadonlySet<string> = new Set(
  Object.keys(INFRA_ACTORS),
);
