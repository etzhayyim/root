/**
 * etzhayyim authz XRPC handler — Phase α P1 scaffold (ADR-2605212030).
 *
 * Implements the org.etzhayyim.authz.* lexicons defined in
 * `00-contracts/lexicons/org/etzhayyim/authz/`.
 *
 * Phase α P1 scope (this file):
 *   - HTTP routing per AT Protocol XRPC convention (`/xrpc/<NSID>`)
 *   - Lexicon-aligned input validation (per request, with informative errors)
 *   - Deterministic stub responses or `ChainNotConfigured` 503 until the
 *     `AUTHZ_CONTRACT_ADDRESS` env var is set and the chain client wired in.
 *
 * Out of scope for this scaffold (Phase α P1 follow-up):
 *   - viem chain client + actual on-chain reads / proposals to Council Safe
 *   - KV-backed nonce store
 *   - real digest construction matching EtzhayyimAuthz.sol rotation digest
 *   - JWT auth for vendor → etzhayyim XRPC (ADR-2605212050 §D2 cross-link)
 */

interface Env {
  AUTHZ_CONTRACT_ADDRESS: string;
  BASE_RPC_URL: string;
  CHAIN_ID: string;
  COUNCIL_SAFE_ADDRESS: string;
  // NONCES?: KVNamespace;          // pending Phase α P1 chain integration
  // ROOT_CACHE?: KVNamespace;      // pending
}

// ─── XRPC error helpers ─────────────────────────────────────────────────

type XrpcError = { error: string; message?: string };

function xrpcError(status: number, error: string, message?: string): Response {
  const body: XrpcError = message ? { error, message } : { error };
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

function xrpcJson(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

// ─── Chain readiness gate ──────────────────────────────────────────────

function requireChainConfigured(env: Env): Response | null {
  if (!env.AUTHZ_CONTRACT_ADDRESS) {
    return xrpcError(
      503,
      "ChainNotConfigured",
      "AUTHZ_CONTRACT_ADDRESS env var is not set; deploy EtzhayyimAuthz to Base Sepolia per docs/base-sepolia-deploy-runbook.md and update wrangler.toml [vars].",
    );
  }
  return null;
}

// ─── Lightweight validators (lexicon-aligned, no schema runtime) ───────

function isHexBytes32(s: unknown): s is string {
  return typeof s === "string" && /^0x[0-9a-fA-F]{64}$/.test(s);
}
function isHexAddress(s: unknown): s is string {
  return typeof s === "string" && /^0x[0-9a-fA-F]{40}$/.test(s);
}
function isHexSig(s: unknown): s is string {
  return typeof s === "string" && /^0x[0-9a-fA-F]{130}$/.test(s);
}
function isDwebHandle(s: unknown): s is string {
  return (
    typeof s === "string" &&
    s.length >= 3 &&
    s.length <= 253 &&
    /^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)*\.etzhayyim\.com$/i.test(s)
  );
}

// ─── Handler stubs (Phase α P1 — return ChainNotConfigured until wired) ─

async function handleBeginRootProvision(req: Request, env: Env): Promise<Response> {
  const gate = requireChainConfigured(env);
  if (gate) return gate;

  type Input = { dwebHandle?: unknown; activeKey?: unknown; purposeNarrow?: unknown };
  let body: Input;
  try {
    body = (await req.json()) as Input;
  } catch {
    return xrpcError(400, "InvalidRequest", "body is not valid JSON");
  }
  if (!isDwebHandle(body.dwebHandle)) {
    return xrpcError(400, "DwebHandleInvalid", "dwebHandle must match <label>.etzhayyim.com");
  }
  if (!isHexAddress(body.activeKey)) {
    return xrpcError(400, "ActiveKeyInvalid", "activeKey must be a 0x-prefixed 20-byte address");
  }
  // TODO Phase α P1: generate nonce, compute keccak256(dwebHandle), build digest,
  // store nonce in NONCES KV with 5-min TTL, return.
  return xrpcError(
    503,
    "NotImplemented",
    "beginRootProvision: nonce store + digest construction pending Phase α P1 chain integration",
  );
}

async function handleCompleteRootProvision(req: Request, env: Env): Promise<Response> {
  const gate = requireChainConfigured(env);
  if (gate) return gate;

  type Input = { nonce?: unknown; signature?: unknown };
  let body: Input;
  try {
    body = (await req.json()) as Input;
  } catch {
    return xrpcError(400, "InvalidRequest", "body is not valid JSON");
  }
  if (typeof body.nonce !== "string" || body.nonce.length === 0) {
    return xrpcError(400, "NonceUnknown", "nonce is required");
  }
  if (!isHexSig(body.signature)) {
    return xrpcError(400, "SignatureInvalid", "signature must be 0x-prefixed 65-byte ECDSA r||s||v");
  }
  // TODO Phase α P1: look up nonce, verify ECDSA recover == activeKey,
  // require Council multisig approval, submit provisionRoot tx, return rootId + txHash.
  return xrpcError(
    503,
    "NotImplemented",
    "completeRootProvision: chain submission pending Phase α P1 chain integration",
  );
}

async function handleResolveRoot(url: URL, env: Env): Promise<Response> {
  const gate = requireChainConfigured(env);
  if (gate) return gate;

  const did = url.searchParams.get("did");
  const dwebHandle = url.searchParams.get("dwebHandle");
  const rootId = url.searchParams.get("rootId");

  const supplied = [did, dwebHandle, rootId].filter((x) => x != null && x !== "").length;
  if (supplied !== 1) {
    return xrpcError(
      400,
      "InvalidArgument",
      "exactly one of did / dwebHandle / rootId must be supplied",
    );
  }
  if (rootId != null && !isHexBytes32(rootId)) {
    return xrpcError(400, "InvalidArgument", "rootId must be 0x-prefixed bytes32");
  }
  if (dwebHandle != null && !isDwebHandle(dwebHandle)) {
    return xrpcError(400, "InvalidArgument", "dwebHandle must match <label>.etzhayyim.com");
  }
  // TODO Phase α P1: viem read from EtzhayyimAuthz.resolveDwebHandle / roots(rootId);
  // parse did:web / did:erc725 forms; return mapped output.
  return xrpcError(
    503,
    "NotImplemented",
    "resolveRoot: chain read pending Phase α P1 chain integration",
  );
}

async function handleMirrorVendorRoot(req: Request, env: Env): Promise<Response> {
  const gate = requireChainConfigured(env);
  if (gate) return gate;

  type Input = {
    dwebHandle?: unknown;
    newActiveKey?: unknown;
    vendorRootDid?: unknown;
    vendorAddr?: unknown;
    vendorContinuityProof?: unknown;
  };
  let body: Input;
  try {
    body = (await req.json()) as Input;
  } catch {
    return xrpcError(400, "InvalidRequest", "body is not valid JSON");
  }
  if (!isDwebHandle(body.dwebHandle)) {
    return xrpcError(400, "DwebHandleTaken", "dwebHandle invalid or already taken (validated on-chain)");
  }
  if (!isHexAddress(body.newActiveKey)) {
    return xrpcError(400, "ActiveKeyInvalid", "newActiveKey must be a 0x-prefixed 20-byte address");
  }
  if (typeof body.vendorRootDid !== "string" || !body.vendorRootDid.startsWith("did:erc725:")) {
    return xrpcError(
      400,
      "VendorRootUnknown",
      "vendorRootDid must be a did:erc725:... DID string",
    );
  }
  if (!isHexAddress(body.vendorAddr)) {
    return xrpcError(400, "VendorRootUnknown", "vendorAddr must be a 0x-prefixed 20-byte address");
  }
  if (!isHexSig(body.vendorContinuityProof)) {
    return xrpcError(
      400,
      "VendorContinuityProofInvalid",
      "vendorContinuityProof must be 0x-prefixed 65-byte ECDSA r||s||v",
    );
  }
  // TODO Phase α P1:
  //   1. ecrecover the proof; require recovered == vendorAddr.
  //   2. Council Safe propose mirrorVendorRoot(dwebHandleHash, newActiveKey, keccak256(vendorRootDid), vendorAddr).
  //   3. Wait for execution, return rootId + txHash + vendorRootHash.
  return xrpcError(
    503,
    "NotImplemented",
    "mirrorVendorRoot: chain submission pending Phase α P1 chain integration",
  );
}

async function handleGetProvenance(url: URL, env: Env): Promise<Response> {
  const gate = requireChainConfigured(env);
  if (gate) return gate;

  const rootId = url.searchParams.get("rootId");
  if (!isHexBytes32(rootId)) {
    return xrpcError(400, "InvalidArgument", "rootId is required (0x-prefixed bytes32)");
  }
  // TODO Phase α P1: read roots(rootId), then scan RootKeyRotated + VendorRootMirrored
  // events for that rootId via eth_getLogs; assemble provenance array.
  return xrpcError(
    503,
    "NotImplemented",
    "getProvenance: event log scan pending Phase α P1 chain integration",
  );
}

// ─── Router ─────────────────────────────────────────────────────────────

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/_health") {
      return xrpcJson({
        status: "ok",
        contractAddress: env.AUTHZ_CONTRACT_ADDRESS || null,
        chainId: env.CHAIN_ID || null,
        councilSafe: env.COUNCIL_SAFE_ADDRESS || null,
        phase: "α P1 scaffold (ADR-2605212030)",
      });
    }

    if (!url.pathname.startsWith("/xrpc/")) {
      return xrpcError(404, "MethodNotFound", "this Worker only serves /xrpc/* and /_health");
    }
    const nsid = url.pathname.slice("/xrpc/".length);

    // Query methods accept GET; procedures require POST.
    switch (nsid) {
      case "org.etzhayyim.authz.beginRootProvision":
        if (request.method !== "POST") return xrpcError(405, "MethodNotAllowed");
        return handleBeginRootProvision(request, env);

      case "org.etzhayyim.authz.completeRootProvision":
        if (request.method !== "POST") return xrpcError(405, "MethodNotAllowed");
        return handleCompleteRootProvision(request, env);

      case "org.etzhayyim.authz.mirrorVendorRoot":
        if (request.method !== "POST") return xrpcError(405, "MethodNotAllowed");
        return handleMirrorVendorRoot(request, env);

      case "org.etzhayyim.authz.resolveRoot":
        if (request.method !== "GET") return xrpcError(405, "MethodNotAllowed");
        return handleResolveRoot(url, env);

      case "org.etzhayyim.authz.getProvenance":
        if (request.method !== "GET") return xrpcError(405, "MethodNotAllowed");
        return handleGetProvenance(url, env);

      default:
        return xrpcError(404, "MethodNotFound", `NSID ${nsid} is not handled by etzhayyim-authz`);
    }
  },
} satisfies ExportedHandler<Env>;
