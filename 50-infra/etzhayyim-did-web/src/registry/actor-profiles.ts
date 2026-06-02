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

/** Return a copy of `rec` with an Ed25519 verificationMethod for
 *  `publicKeyMultibase` merged in (replacing any existing `#session-key`). This
 *  is the publish-path counterpart to the auth Worker's `registerSigningKey`:
 *  writing the registered key into the actor record is what makes it appear in
 *  did.json and lets a did:web Signal binding verify (ADR-2606014000 D4).
 *  Defined below `ed25519VerificationMethod` is hoisted — see that function. */
export function withVerificationMethod(
  rec: ActorRecord,
  publicKeyMultibase: string,
): ActorRecord {
  const vm = ed25519VerificationMethod(rec.did, publicKeyMultibase);
  const kept = rec.vm.filter((v) => v.id !== vm.id);
  return { ...rec, vm: [...kept, vm] };
}

/** Ed25519 verification-method type understood by the kotoba-auth did:web
 *  resolver (`DidDocument::ed25519_public_key`). */
export const ED25519_VM_TYPE = "Ed25519VerificationKey2020";

/**
 * Build an Ed25519 verificationMethod entry for an actor's DID document from a
 * `publicKeyMultibase` (`z…`). The key is NOT minted here — it is the member's
 * **client-self-custodied** session key registered via Stage C-2
 * (`registerSigningKey`, ADR-2606014500) or an on-chain ERC725 mirror. Either
 * way the server never holds the private key (ADR-2605231525). Populating
 * `rec.vm` with this is what lets `ai.gftd.signal.resolve.identity` verify a
 * did:web Signal binding (ADR-2606014000 D4) instead of returning unverified.
 */
export function ed25519VerificationMethod(
  did: string,
  publicKeyMultibase: string,
): ActorVerificationMethod {
  return {
    id: `${did}#session-key`,
    type: ED25519_VM_TYPE,
    controller: did,
    publicKeyMultibase,
  };
}

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
  const subdomainDid = `did:web:${rec.handle}.etzhayyim.com`;
  const alsoKnownAs: string[] = [subdomainDid];
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
  // Reference every Ed25519 verification method under authentication +
  // assertionMethod so the registered/mirrored key is usable for DID-auth and
  // for verifying assertions (e.g. the Signal-identity binding, ADR-2606014000).
  const ed25519Ids = rec.vm
    .filter((v) => v["type"] === ED25519_VM_TYPE)
    .map((v) => v.id);
  const doc: Record<string, unknown> = {
    "@context": [
      "https://www.w3.org/ns/did/v1",
      "https://w3id.org/security/suites/jws-2020/v1",
    ],
    id: pathBasedDid,
    alsoKnownAs,
    verificationMethod: rec.vm.map((v) => ({ ...v })),
    service: rec.service.map((s) => ({ ...s })),
    _meta: {
      adr: ["2605212030", "2605241800", "2606013800", "2606014000", ...rec.adr],
      source: rec.source,
      kind: rec.kind,
      status: rec.status,
      glyph: rec.glyph,
      primaryLexicon: rec.primaryLexicon,
      primarySchema: rec.primarySchema,
      note:
        rec.vm.length === 0
          ? "verificationMethod empty — member session-key / ERC725 mirror pending; did:web trust root = TLS (no server-minted key, ADR-2605231525)"
          : "verificationMethod = member client-registered session key or on-chain ERC725 mirror (never server-minted)",
    },
  };
  if (ed25519Ids.length > 0) {
    doc.authentication = ed25519Ids;
    doc.assertionMethod = ed25519Ids;
  }
  return doc;
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
