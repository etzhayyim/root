// auth-forward.ts — stateless XRPC shim from yatabase CF Worker to
// lg-yatabase Granian pod for vertex_api_key writes.
//
// Per ADR-2605111200 the CF Worker is edge-only and cannot call
// createKyselyDb. All vertex_api_key INSERTs now route through
// `/xrpc/ai.gftd.apps.yata.{signup,invite,revoke}` on the pod side.
// This file is a thin wrapper around the same forwardBmc HMAC pattern;
// kept separate so the auth NSIDs are colocated with the auth-signup
// handler that calls them.
//
// Auth model:
//   * /signup is anonymous: caller has NO Bearer token. Worker still
//     adds x-internal-trust HMAC so the pod can verify the call came
//     from the Worker (not the open internet).
//   * /invite + /revoke are caller-authenticated: Worker resolves the
//     Bearer key via PDS first, then forwards with x-gftd-org-did.

import { forwardBmc, type ForwardEnv, type ForwardIdentity, type ForwardResult } from "./bmc-forward";

const ANON_IDENTITY: ForwardIdentity = {
  did: "anon",
  orgDid: "anon",
};

export interface SignupForwardInput {
  email?: string;
  name?: string;
}

export interface SignupForwardOutput {
  ok: boolean;
  apiKey?: string;
  keyId?: string;
  orgDid?: string;
  tenantName?: string;
  awsAccessKeyId?: string;
  awsSecretAccessKey?: string;
  emailStatus?: string;
  welcome?: string;
  next?: string;
  pricing?: string;
  error?: string;
  message?: string;
}

export async function forwardSignup(
  env: ForwardEnv,
  body: SignupForwardInput,
  traceId?: string,
): Promise<ForwardResult> {
  return forwardBmc(
    env,
    "POST",
    "ai.gftd.apps.yata.signup",
    body as Record<string, unknown>,
    traceId ? { ...ANON_IDENTITY, traceId } : ANON_IDENTITY,
    { timeoutMs: 30_000 },
  );
}

export async function forwardInvite(
  env: ForwardEnv,
  body: { name: string; email?: string },
  identity: ForwardIdentity,
): Promise<ForwardResult> {
  return forwardBmc(env, "POST", "ai.gftd.apps.yata.invite", body as Record<string, unknown>, identity, {
    timeoutMs: 20_000,
  });
}

export async function forwardRevoke(
  env: ForwardEnv,
  body: { vertex_id: string },
  identity: ForwardIdentity,
): Promise<ForwardResult> {
  return forwardBmc(env, "POST", "ai.gftd.apps.yata.revoke", body as Record<string, unknown>, identity, {
    timeoutMs: 20_000,
  });
}
