/**
 * `com.etzhayyim.authz.verifyCacao` — stateless same-origin auth gate.
 * ADR-2606060000 — `/profile` WebAuthn / passkey / SIWE without auth.subdomain.
 *
 * This handler lets the `/profile` page (served same-origin via the yoro proxy)
 * flip into edit-mode once a member proves control of their DID — WITHOUT a
 * separate auth.etzhayyim.com hop and WITHOUT the Worker holding any key.
 *
 * It is NOT the write-authorization point. The actual profile mutation is a
 * CACAO-authorized `datom:transact` to the kotoba node, whose `kotoba-auth`
 * `DelegationChain::verify` + single-use NonceStore are the real enforcement
 * (replay protection, capability attenuation). This endpoint only:
 *   1. cryptographically verifies the CACAO signature (Ed25519 locally; eip191
 *      relayed to kotoba — see cacao.ts),
 *   2. binds the audience + domain to THIS apex origin (anti-cross-site),
 *   3. confirms the capability shape (a kotoba://op/… resource is present),
 * and returns the resolved DID + granted scope for the client to gate its UI.
 */

import { verifyCacao, isWellFormed, type Cacao, type VerifyOutcome } from "./cacao.ts";
import type { KotobaClaim } from "./kotoba.ts";

export interface SessionScope {
  /** kotoba://op/* capability URIs requested by the CACAO. */
  capabilities: string[];
  /** kotoba://graph/<cid> graph scopes the capability is bound to. */
  graphs: string[];
}

export interface VerifyCacaoResult {
  valid: boolean;
  did?: string;
  sigType?: string;
  method?: string;
  scope?: SessionScope;
  /** structurally valid but signature-verify must run on the kotoba node. */
  gated?: boolean;
  reason?: string;
}

const APEX_HOSTS = new Set(["etzhayyim.com", "www.etzhayyim.com"]);

function extractScope(cacao: Cacao): SessionScope {
  const resources = cacao.p.resources ?? [];
  return {
    capabilities: resources.filter((r) => r.startsWith("kotoba://op/")),
    graphs: resources.filter((r) => r.startsWith("kotoba://graph/")),
  };
}

/**
 * The CACAO must be addressed to this apex origin (aud + domain), so a token
 * minted for another relying party can't be replayed here. `aud` may be the
 * apex DID or the apex URI; `domain` is the bare host.
 */
function boundToApex(cacao: Cacao): boolean {
  const aud = cacao.p.aud;
  const domain = cacao.p.domain ?? "";
  const audOk =
    aud === "did:web:etzhayyim.com" ||
    APEX_HOSTS.has(audHost(aud)) ||
    aud === "https://etzhayyim.com" ||
    aud === "https://etzhayyim.com/";
  const domainOk = APEX_HOSTS.has(domain);
  return audOk && domainOk;
}

function audHost(aud: string): string {
  try {
    return new URL(aud).host;
  } catch {
    return "";
  }
}

/**
 * Verify a CACAO presented to `/xrpc/com.etzhayyim.authz.verifyCacao`.
 * `nowMs` is injected for deterministic testing.
 */
export async function handleVerifyCacao(
  body: unknown,
  nowMs: number,
): Promise<{ status: number; result: VerifyCacaoResult }> {
  const cacao = (body as { cacao?: Cacao } | null)?.cacao;
  if (!cacao) {
    return {
      status: 400,
      result: { valid: false, reason: "missing 'cacao' in request body" },
    };
  }

  if (!boundToApex(cacao)) {
    return {
      status: 403,
      result: {
        valid: false,
        reason:
          "CACAO audience/domain not bound to etzhayyim.com " +
          "(aud must be did:web:etzhayyim.com or https://etzhayyim.com; " +
          "domain must be etzhayyim.com)",
      },
    };
  }

  const scope = extractScope(cacao);
  if (scope.capabilities.length === 0) {
    return {
      status: 400,
      result: {
        valid: false,
        reason: "CACAO grants no kotoba://op/ capability resource",
        scope,
      },
    };
  }

  const outcome: VerifyOutcome = await verifyCacao(cacao, nowMs);
  if (outcome.valid) {
    return {
      status: 200,
      result: {
        valid: true,
        did: outcome.did,
        sigType: outcome.sigType,
        method: outcome.method,
        scope,
      },
    };
  }

  if (outcome.gated) {
    // eip191/SIWE: structurally valid, signature-verify lives on the kotoba
    // node. The client should re-present the CACAO with its kotoba write — the
    // node verifies the recovery there. Reported honestly so the UI doesn't
    // claim a verified session it can't yet prove on the apex.
    return {
      status: 202,
      result: {
        valid: false,
        gated: true,
        sigType: outcome.sigType,
        scope,
        reason: outcome.reason,
      },
    };
  }

  return {
    status: 401,
    result: { valid: false, sigType: outcome.sigType, reason: outcome.reason },
  };
}

// ─── account write relay (same-origin → kotoba, ADR-2606061800) ─────────────

const CAP_DATOM_TRANSACT = "kotoba://op/datom:transact";

export interface RegisterAccountResult {
  ok: boolean;
  /** structurally valid, but the kotoba write endpoint is not enabled. */
  gated?: boolean;
  did?: string;
  handle?: string;
  reason?: string;
}

/**
 * Relay a member-CACAO-authorized account write to the kotoba node
 * (ADR-2606061800). The member signs a kotoba-scoped CACAO (aud = node
 * `operator_did`, `kotoba://op/datom:transact`); the Worker re-encodes it to
 * `cacaoB64` (CBOR) and forwards an `account.<did>` entity to the node's
 * `kg.ingest`. The Worker holds NO key and does NOT verify the signature (the
 * kotoba node does) — it sanity-checks the CACAO shape + capability and relays.
 *
 * ONE relay backs ALL account writes (the frontend supplies the claim set):
 *   - register    → [account/did, account/controller, account/handle, …profile]
 *   - device-wrap → [account/device/<credId> = wrappedArkB64]   (multi-device add)
 *   - rotate      → [account/controller = newDid, account/rotation/<n> = …] (key rotation)
 *
 * `cborEncode` + `relay` are injected (unit-testable; the CBOR encoder + network
 * stay out of this module). Missing `KOTOBA_WRITE_ENDPOINT` ⇒ relay "gated" ⇒
 * HTTP 202 (honest R0).
 */
export async function handleAccountWrite(
  body: unknown,
  cborEncode: (cacao: Cacao) => string,
  relay: (
    cacaoB64: string,
    id: string,
    claims: KotobaClaim[],
    labelEn?: string,
  ) => Promise<"written" | "gated" | "error">,
): Promise<{ status: number; result: RegisterAccountResult }> {
  const b = body as
    | {
        cacao?: Cacao;
        id?: string;
        did?: string;
        handle?: string;
        profile?: Record<string, unknown>;
        claims?: KotobaClaim[];
        labelEn?: string;
      }
    | null;
  const cacao = b?.cacao;
  if (!cacao || !isWellFormed(cacao)) {
    return { status: 400, result: { ok: false, reason: "missing or malformed 'cacao' in request body" } };
  }
  if (cacao.s.t !== "EdDSA") {
    return { status: 400, result: { ok: false, reason: "account write requires an EdDSA (did:key) CACAO" } };
  }
  const caps = (cacao.p.resources ?? []).filter((r) => r.startsWith("kotoba://op/"));
  if (!caps.includes(CAP_DATOM_TRANSACT)) {
    return { status: 400, result: { ok: false, reason: `CACAO lacks ${CAP_DATOM_TRANSACT} capability` } };
  }
  const did = cacao.p.iss;
  if (b?.did && b.did !== did) {
    return { status: 400, result: { ok: false, reason: "body.did does not match the CACAO issuer (controller key)" } };
  }
  const id = b?.id ?? `account.${did}`;
  if (!id.startsWith("account.")) {
    return { status: 400, result: { ok: false, reason: "id must be 'account.<…>'" } };
  }

  let claims: KotobaClaim[];
  if (Array.isArray(b?.claims) && b.claims.length > 0) {
    // advanced: caller supplies the exact claim set (device-wrap, rotation, …).
    if (!b.claims.every((c) => c && typeof c.pred === "string" && typeof c.value === "string")) {
      return { status: 400, result: { ok: false, reason: "each claim must be {pred:string, value:string}" } };
    }
    claims = b.claims;
  } else {
    const handle = String(b?.handle ?? "");
    claims = [
      { pred: "account/did", value: did },
      { pred: "account/controller", value: did },
    ];
    if (handle) claims.push({ pred: "account/handle", value: handle });
    for (const [k, v] of Object.entries(b?.profile ?? {})) {
      if (typeof v === "string") claims.push({ pred: `account/${k}`, value: v });
    }
  }

  const cacaoB64 = cborEncode(cacao);
  const handle = b?.handle ? String(b.handle) : undefined;
  const write = await relay(cacaoB64, id, claims, b?.labelEn);
  if (write === "written") return { status: 200, result: { ok: true, did, handle } };
  if (write === "gated") {
    return {
      status: 202,
      result: { ok: false, gated: true, did, handle, reason: "kotoba write endpoint not enabled (R0); not yet published" },
    };
  }
  return { status: 502, result: { ok: false, did, handle, reason: "kotoba account write failed" } };
}
