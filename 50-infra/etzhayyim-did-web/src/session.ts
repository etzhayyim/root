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

import { verifyCacao, type Cacao, type VerifyOutcome } from "./cacao.ts";

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
