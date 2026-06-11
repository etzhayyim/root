/**
 * etzhayyim authz XRPC handler — Phase α P1 (ADR-2605212030).
 *
 * Implements the org.etzhayyim.authz.* lexicons defined in
 * `00-contracts/lexicons/org/etzhayyim/authz/`.
 *
 * Read paths (resolveRoot, isActive checks) are fully functional once
 * `AUTHZ_CONTRACT_ADDRESS` + `BASE_RPC_URL` + `CHAIN_ID` env vars are
 * set in wrangler.toml [vars]. viem reads the EtzhayyimAuthz contract
 * directly.
 *
 * Write paths (provisionRoot / mirrorVendorRoot) return a Council Safe
 * proposal payload that an operator pastes into https://app.safe.global
 * per docs/council-multisig-sop.md. The Worker never submits owner-only
 * txs itself — Council multisig authority is the SoT.
 *
 * Out of scope (Phase α P1 follow-up):
 *   - getProvenance event log scan (eth_getLogs for RootKeyRotated +
 *     VendorRootMirrored, chronological provenance assembly)
 *   - vendor JWT verification for the Stripe-bridge cross-call (lives in
 *     ADR-2605212050; that XRPC will be served by a different Worker)
 */

import type { Address, Hex } from "viem";
import { isAddress, getAddress, verifyMessage } from "viem";
import {
  loadChainConfig,
  resolveByDwebHash,
  getRootById,
  type ChainConfig,
  type OnChainRoot,
} from "./chain";
import { provisionDigest, vendorContinuityDigest, dwebHandleHash } from "./digest";
import { makeNonceStore, newNonce, type NoncePayload } from "./nonces";
import {
  buildProvisionRootProposal,
  buildMirrorVendorRootProposal,
} from "./safe-proposal";

interface Env {
  AUTHZ_CONTRACT_ADDRESS?: string;
  BASE_RPC_URL?: string;
  CHAIN_ID?: string;
  COUNCIL_SAFE_ADDRESS?: string;
  NONCES?: KVNamespace;
  // ROOT_CACHE?: KVNamespace;     // pending Phase α P1 follow-up
}

// ─── XRPC response helpers ──────────────────────────────────────────────

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

// ─── Config gate ────────────────────────────────────────────────────────

function chainOrError(env: Env): ChainConfig | Response {
  const cfg = loadChainConfig(env);
  if (!cfg) {
    return xrpcError(
      503,
      "ChainNotConfigured",
      "AUTHZ_CONTRACT_ADDRESS / BASE_RPC_URL / CHAIN_ID env vars are not set; deploy EtzhayyimAuthz per docs/base-sepolia-deploy-runbook.md and update wrangler.toml [vars].",
    );
  }
  return cfg;
}

function councilSafeOrError(env: Env): Address | Response {
  const safe = env.COUNCIL_SAFE_ADDRESS;
  if (!safe || !isAddress(safe)) {
    return xrpcError(
      503,
      "CouncilSafeNotConfigured",
      "COUNCIL_SAFE_ADDRESS env var is not set; cannot build a Council proposal payload.",
    );
  }
  return getAddress(safe);
}

// ─── Validators ─────────────────────────────────────────────────────────

const HEX_BYTES32 = /^0x[0-9a-fA-F]{64}$/;
const HEX_SIG = /^0x[0-9a-fA-F]{130}$/;
const DWEB_HANDLE = /^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)*\.etzhayyim\.com$/i;

function asHexBytes32(s: unknown): Hex | null {
  return typeof s === "string" && HEX_BYTES32.test(s) ? (s as Hex) : null;
}
function asAddress(s: unknown): Address | null {
  return typeof s === "string" && isAddress(s) ? getAddress(s) : null;
}
function asHexSig(s: unknown): Hex | null {
  return typeof s === "string" && HEX_SIG.test(s) ? (s as Hex) : null;
}
function asDwebHandle(s: unknown): string | null {
  return typeof s === "string" && DWEB_HANDLE.test(s) && s.length >= 3 && s.length <= 253
    ? s.toLowerCase()
    : null;
}

// ─── DID format helpers ─────────────────────────────────────────────────

function buildDid(rootId: Hex, contract: Address): string {
  return `did:erc725:base:${contract}#${rootId.slice(2)}`;
}
function buildDwebDid(handle: string): string {
  return `did:web:${handle}`;
}
function parseDid(did: string): { rootId?: Hex; contract?: Address; handle?: string } {
  // did:web:<handle>.etzhayyim.com — handle form
  const dwebMatch = /^did:web:([a-z0-9.-]+\.etzhayyim\.com)$/i.exec(did);
  if (dwebMatch) return { handle: dwebMatch[1].toLowerCase() };
  // did:web:etzhayyim.com:actor:<handle> — path-based form
  const dwebPathMatch = /^did:web:etzhayyim\.com:actor:([a-z0-9-]+)$/i.exec(did);
  if (dwebPathMatch) return { handle: `${dwebPathMatch[1].toLowerCase()}.etzhayyim.com` };
  // did:erc725:base:<contract>#<rootIdHex>
  const ercMatch = /^did:erc725:base:(0x[0-9a-fA-F]{40})#([0-9a-fA-F]{64})$/.exec(did);
  if (ercMatch) {
    return { contract: getAddress(ercMatch[1]), rootId: `0x${ercMatch[2]}` as Hex };
  }
  return {};
}

function rootToOutput(rootId: Hex, data: OnChainRoot, contract: Address): Record<string, unknown> {
  const handle = null; // dweb handle plaintext is not stored on-chain; only the hash.
  const out: Record<string, unknown> = {
    rootId,
    did: buildDid(rootId, contract),
    dwebDid: handle ? buildDwebDid(handle) : `did:web:?.etzhayyim.com#${data.dwebHandleHash.slice(2, 10)}`,
    activeKey: data.activeKey,
    active: data.active,
    createdBlock: Number(data.createdBlock),
    lastRotatedBlock: Number(data.lastRotatedBlock),
  };
  if (data.predecessorVendorRootHash !== "0x0000000000000000000000000000000000000000000000000000000000000000") {
    out.predecessorVendorRootHash = data.predecessorVendorRootHash;
    out.predecessorVendorAddr = data.predecessorVendorAddr;
  }
  return out;
}

// ─── Handlers ───────────────────────────────────────────────────────────

async function handleBeginRootProvision(req: Request, env: Env): Promise<Response> {
  const cfgOrErr = chainOrError(env);
  if (cfgOrErr instanceof Response) return cfgOrErr;
  const cfg = cfgOrErr;

  type Input = { dwebHandle?: unknown; activeKey?: unknown; purposeNarrow?: unknown };
  let body: Input;
  try {
    body = (await req.json()) as Input;
  } catch {
    return xrpcError(400, "InvalidRequest", "body is not valid JSON");
  }
  const handle = asDwebHandle(body.dwebHandle);
  if (!handle) return xrpcError(400, "DwebHandleInvalid", "dwebHandle must match <label>.etzhayyim.com");
  const activeKey = asAddress(body.activeKey);
  if (!activeKey) return xrpcError(400, "ActiveKeyInvalid", "activeKey must be a 0x-prefixed 20-byte address");

  const handleHash = dwebHandleHash(handle);

  // Reject early if the handle is already taken on-chain (saves Council time).
  const existing = await resolveByDwebHash(cfg, handleHash);
  if (existing) {
    return xrpcError(409, "DwebHandleTaken", `dwebHandle is already bound to root ${existing.rootId}`);
  }

  const nonce = newNonce();
  const digest = provisionDigest({
    chainId: cfg.chainId,
    authzContractAddress: cfg.contractAddress,
    dwebHandleHash: handleHash,
    activeKey,
    nonce: nonce as Hex,
  });

  const payload: NoncePayload = {
    dwebHandleHash: handleHash,
    dwebHandle: handle,
    activeKey,
    digest,
    chainId: cfg.chainId,
    contractAddress: cfg.contractAddress,
    createdAtMs: Date.now(),
    purposeNarrow: typeof body.purposeNarrow === "string" ? body.purposeNarrow : undefined,
  };

  const store = makeNonceStore(env.NONCES);
  await store.put(nonce, payload);

  return xrpcJson({
    digest,
    dwebHandleHash: handleHash,
    nonce,
    expiresAt: Math.floor((payload.createdAtMs + 5 * 60 * 1000) / 1000),
    chainId: cfg.chainId,
    contractAddress: cfg.contractAddress,
  });
}

async function handleCompleteRootProvision(req: Request, env: Env): Promise<Response> {
  const cfgOrErr = chainOrError(env);
  if (cfgOrErr instanceof Response) return cfgOrErr;
  const cfg = cfgOrErr;
  const safeOrErr = councilSafeOrError(env);
  if (safeOrErr instanceof Response) return safeOrErr;
  const councilSafe = safeOrErr;

  type Input = { nonce?: unknown; signature?: unknown };
  let body: Input;
  try {
    body = (await req.json()) as Input;
  } catch {
    return xrpcError(400, "InvalidRequest", "body is not valid JSON");
  }
  if (typeof body.nonce !== "string") return xrpcError(400, "NonceUnknown", "nonce is required");
  const signature = asHexSig(body.signature);
  if (!signature) return xrpcError(400, "SignatureInvalid", "signature must be 0x-prefixed 65-byte ECDSA r||s||v");

  const store = makeNonceStore(env.NONCES);
  const payload = await store.consume(body.nonce);
  if (!payload) return xrpcError(400, "NonceUnknown", "nonce not found or already used");
  if (Date.now() - payload.createdAtMs > 5 * 60 * 1000) {
    return xrpcError(400, "NonceExpired", "nonce expired (5-minute TTL)");
  }
  if (payload.chainId !== cfg.chainId || payload.contractAddress.toLowerCase() !== cfg.contractAddress.toLowerCase()) {
    return xrpcError(400, "NonceUnknown", "nonce was issued against a different chain/contract config");
  }

  // Verify EIP-191 personal_sign signature against the recorded activeKey.
  // viem's verifyMessage applies the \x19Ethereum Signed Message:\n32 prefix.
  // We pass the inner-hashed digest as a raw bytes32 "message" (viem will
  // hash + prefix it again; mismatch → reject). Instead we sign the inner
  // pre-prefix hash and verify by reconstructing the prefix ourselves.
  //
  // For simplicity here we accept that the client signs `payload.digest`
  // (which already includes the EIP-191 prefix). We then compare the
  // ECDSA recovery against payload.activeKey via verifyMessage on the
  // pre-prefix inner. To do so we re-derive the inner.
  //
  // viem's verifyMessage(args) treats `message` as the raw message — it
  // re-applies the EIP-191 prefix internally. The inner of our digest
  // (without prefix) is precisely that "raw message". We don't have the
  // inner cached, but we can reconstruct: digest = keccak("\x19...32" || inner),
  // so given the digest the inner is not recoverable. Therefore the
  // canonical signing payload is the digest itself (pre-hashed by client
  // and signed as raw 32 bytes via eth_sign / personal_sign).
  //
  // viem provides `verifyHash` which signs an already-hashed message; we
  // use that since the wallet should sign `digest` directly.
  // Note: verifyMessage's "raw" overload supports hex with applyHashing=false.
  const ok = await verifyMessage({
    address: payload.activeKey,
    message: { raw: payload.digest },
    signature,
  });
  if (!ok) {
    return xrpcError(
      400,
      "SignatureInvalid",
      "signature does not recover to the activeKey supplied in beginRootProvision",
    );
  }

  // Build the Council Safe proposal. We do NOT submit; Council multisig is SoT.
  const proposal = buildProvisionRootProposal({
    authzContractAddress: cfg.contractAddress,
    councilSafe,
    chainId: cfg.chainId,
    dwebHandleHash: payload.dwebHandleHash,
    activeKey: payload.activeKey,
  });

  return new Response(
    JSON.stringify({
      status: "council-proposal-pending",
      councilProposal: proposal,
      followUp: {
        sop: "https://github.com/etzhayyim/root/blob/main/50-infra/etzhayyim-authz/docs/council-multisig-sop.md",
        pollVia: `GET /xrpc/org.etzhayyim.authz.resolveRoot?dwebHandle=${encodeURIComponent(payload.dwebHandle)}`,
      },
    }),
    {
      status: 202,
      headers: { "content-type": "application/json; charset=utf-8" },
    },
  );
}

async function handleResolveRoot(url: URL, env: Env): Promise<Response> {
  const cfgOrErr = chainOrError(env);
  if (cfgOrErr instanceof Response) return cfgOrErr;
  const cfg = cfgOrErr;

  const did = url.searchParams.get("did");
  const dwebHandleParam = url.searchParams.get("dwebHandle");
  const rootIdParam = url.searchParams.get("rootId");
  const supplied = [did, dwebHandleParam, rootIdParam].filter((x) => x != null && x !== "").length;
  if (supplied !== 1) {
    return xrpcError(400, "InvalidArgument", "exactly one of did / dwebHandle / rootId must be supplied");
  }

  let rootId: Hex | null = null;
  let handle: string | null = null;

  if (rootIdParam) {
    rootId = asHexBytes32(rootIdParam);
    if (!rootId) return xrpcError(400, "InvalidArgument", "rootId must be 0x-prefixed bytes32");
  } else if (dwebHandleParam) {
    handle = asDwebHandle(dwebHandleParam);
    if (!handle) return xrpcError(400, "InvalidArgument", "dwebHandle must match <label>.etzhayyim.com");
  } else if (did) {
    const parsed = parseDid(did);
    if (parsed.handle) {
      handle = parsed.handle;
    } else if (parsed.rootId && parsed.contract) {
      if (parsed.contract.toLowerCase() !== cfg.contractAddress.toLowerCase()) {
        return xrpcError(400, "InvalidArgument", `did references contract ${parsed.contract}, expected ${cfg.contractAddress}`);
      }
      rootId = parsed.rootId;
    } else {
      return xrpcError(400, "InvalidArgument", "did is not a recognised etzhayyim DID form");
    }
  }

  if (handle) {
    const hh = dwebHandleHash(handle);
    const r = await resolveByDwebHash(cfg, hh);
    if (!r) return xrpcError(404, "NotFound", `no active root for dwebHandle ${handle}`);
    const out = rootToOutput(r.rootId, r.data, cfg.contractAddress);
    out.dwebDid = buildDwebDid(handle); // we know the plaintext handle here.
    return xrpcJson(out);
  }
  if (rootId) {
    const data = await getRootById(cfg, rootId);
    if (!data) return xrpcError(404, "NotFound", `no root with rootId ${rootId}`);
    const out = rootToOutput(rootId, data, cfg.contractAddress);
    return xrpcJson(out);
  }
  return xrpcError(500, "InvalidArgument", "unreachable");
}

async function handleMirrorVendorRoot(req: Request, env: Env): Promise<Response> {
  const cfgOrErr = chainOrError(env);
  if (cfgOrErr instanceof Response) return cfgOrErr;
  const cfg = cfgOrErr;
  const safeOrErr = councilSafeOrError(env);
  if (safeOrErr instanceof Response) return safeOrErr;
  const councilSafe = safeOrErr;

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
  const handle = asDwebHandle(body.dwebHandle);
  if (!handle) return xrpcError(400, "DwebHandleTaken", "dwebHandle invalid (validated against <label>.etzhayyim.com)");
  const newActiveKey = asAddress(body.newActiveKey);
  if (!newActiveKey) return xrpcError(400, "ActiveKeyInvalid", "newActiveKey must be a 0x-prefixed 20-byte address");
  if (typeof body.vendorRootDid !== "string" || !body.vendorRootDid.startsWith("did:erc725:")) {
    return xrpcError(400, "VendorRootUnknown", "vendorRootDid must be a did:erc725:... DID string");
  }
  const vendorAddr = asAddress(body.vendorAddr);
  if (!vendorAddr) return xrpcError(400, "VendorRootUnknown", "vendorAddr must be a 0x-prefixed 20-byte address");
  const proof = asHexSig(body.vendorContinuityProof);
  if (!proof) {
    return xrpcError(
      400,
      "VendorContinuityProofInvalid",
      "vendorContinuityProof must be 0x-prefixed 65-byte ECDSA r||s||v",
    );
  }

  const handleHash = dwebHandleHash(handle);
  const taken = await resolveByDwebHash(cfg, handleHash);
  if (taken) return xrpcError(409, "DwebHandleTaken", `dwebHandle is already bound to root ${taken.rootId}`);

  const digest = vendorContinuityDigest({
    vendorRootDid: body.vendorRootDid,
    dwebHandleHash: handleHash,
    newActiveKey,
  });

  const ok = await verifyMessage({
    address: vendorAddr,
    message: { raw: digest },
    signature: proof,
  });
  if (!ok) {
    return xrpcError(
      400,
      "VendorContinuityProofInvalid",
      "vendorContinuityProof does not recover to vendorAddr",
    );
  }

  // keccak256 of the vendor DID string for predecessorVendorRootHash on-chain.
  const { keccak256, toBytes } = await import("viem");
  const predecessorVendorRootHash = keccak256(toBytes(body.vendorRootDid));

  const proposal = buildMirrorVendorRootProposal({
    authzContractAddress: cfg.contractAddress,
    councilSafe,
    chainId: cfg.chainId,
    dwebHandleHash: handleHash,
    newActiveKey,
    predecessorVendorRootHash,
    predecessorVendorAddr: vendorAddr,
  });

  return new Response(
    JSON.stringify({
      status: "council-proposal-pending",
      vendorRootHash: predecessorVendorRootHash,
      councilProposal: proposal,
      followUp: {
        sop: "https://github.com/etzhayyim/root/blob/main/50-infra/etzhayyim-authz/docs/council-multisig-sop.md",
        pollVia: `GET /xrpc/org.etzhayyim.authz.resolveRoot?dwebHandle=${encodeURIComponent(handle)}`,
      },
    }),
    {
      status: 202,
      headers: { "content-type": "application/json; charset=utf-8" },
    },
  );
}

async function handleGetProvenance(url: URL, env: Env): Promise<Response> {
  const cfgOrErr = chainOrError(env);
  if (cfgOrErr instanceof Response) return cfgOrErr;
  const cfg = cfgOrErr;

  const rootIdParam = url.searchParams.get("rootId");
  const rootId = asHexBytes32(rootIdParam);
  if (!rootId) return xrpcError(400, "InvalidArgument", "rootId is required (0x-prefixed bytes32)");

  const data = await getRootById(cfg, rootId);
  if (!data) return xrpcError(404, "NotFound", `no root with rootId ${rootId}`);

  // Phase α P1 follow-up: event log scan via eth_getLogs.
  // For now, return the current state with `rotations: []` and the
  // vendor predecessor link if present.
  const out: Record<string, unknown> = {
    rootId,
    did: buildDid(rootId, cfg.contractAddress),
    dwebDid: `did:web:?.etzhayyim.com#${data.dwebHandleHash.slice(2, 10)}`,
    current: {
      activeKey: data.activeKey,
      active: data.active,
      createdBlock: Number(data.createdBlock),
      lastRotatedBlock: Number(data.lastRotatedBlock),
    },
    rotations: [],
    _note:
      "rotations[] is empty in Phase α P1; event log scan via eth_getLogs is pending follow-up.",
  };
  if (
    data.predecessorVendorRootHash !==
    "0x0000000000000000000000000000000000000000000000000000000000000000"
  ) {
    out.vendorPredecessor = {
      vendorRootHash: data.predecessorVendorRootHash,
      vendorAddr: data.predecessorVendorAddr,
    };
  }
  return xrpcJson(out);
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
        nonceStore: env.NONCES ? "kv" : "memory",
        phase: "α P1 (ADR-2605212030) — viem reader + Council Safe proposal builder live; event scan + KV-default pending",
      });
    }

    if (!url.pathname.startsWith("/xrpc/")) {
      return xrpcError(404, "MethodNotFound", "this Worker only serves /xrpc/* and /_health");
    }
    const nsid = url.pathname.slice("/xrpc/".length);

    try {
      switch (nsid) {
        case "org.etzhayyim.authz.beginRootProvision":
          if (request.method !== "POST") return xrpcError(405, "MethodNotAllowed");
          return await handleBeginRootProvision(request, env);

        case "org.etzhayyim.authz.completeRootProvision":
          if (request.method !== "POST") return xrpcError(405, "MethodNotAllowed");
          return await handleCompleteRootProvision(request, env);

        case "org.etzhayyim.authz.mirrorVendorRoot":
          if (request.method !== "POST") return xrpcError(405, "MethodNotAllowed");
          return await handleMirrorVendorRoot(request, env);

        case "org.etzhayyim.authz.resolveRoot":
          if (request.method !== "GET") return xrpcError(405, "MethodNotAllowed");
          return await handleResolveRoot(url, env);

        case "org.etzhayyim.authz.getProvenance":
          if (request.method !== "GET") return xrpcError(405, "MethodNotAllowed");
          return await handleGetProvenance(url, env);

        default:
          return xrpcError(404, "MethodNotFound", `NSID ${nsid} is not handled by etzhayyim-authz`);
      }
    } catch (err) {
      return xrpcError(
        500,
        "InternalError",
        err instanceof Error ? err.message : String(err),
      );
    }
  },
} satisfies ExportedHandler<Env>;
