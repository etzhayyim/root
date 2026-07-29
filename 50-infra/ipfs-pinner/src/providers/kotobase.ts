/**
 * kotobase provider — pin a shard to kotobase.net, the kotoba-native IPFS
 * Pinning Service (https://kotobase.net, `did:web:kotobase.net`, gftd infra,
 * built on etzhayyim/kotoba). This is the religious-corp DURABLE remote pin
 * target to pair with the local {@link kubo} provider (ADR-2605171800 Stage 4
 * replication-factor ≥ 2): kubo provides the blocks locally, kotobase fetches
 * and pins the root CID off-site (CAR-on-B2, ADR-2606042100), and content is
 * retrievable from any IPFS gateway or node that can reach the swarm.
 *
 * Interface: the standard IPFS Pinning Service API (PSA,
 * https://ipfs.github.io/pinning-services-api-spec/):
 *   - POST {base}/pins  body {cid, name?}  -> 202 PinStatus {requestid, status, pin, ...}
 *
 * The pin is by CID. mst-projector names each CAR `<rootCid>.car`, so the root
 * CID is the filename stem — no CAR parse needed; we submit it to kotobase,
 * which fetches the blocks (from the paired kubo node / the swarm) and pins
 * them durably. The submitted CID is verified against the returned PinStatus.
 *
 * Auth (per kotobase /llms-full.txt) — exactly one of:
 *   - `ETZ_KOTOBASE_JWT`  → `Authorization: Bearer <jwt>` (gftd-AUTHN JWT, `sub` = tenant DID)
 *   - `ETZ_KOTOBASE_CACAO` (base64-cbor) + `ETZ_KOTOBASE_DID` → `Authorization: CACAO <b64>`
 *     + `x-kotoba-did: <tenant DID>`. The CACAO must grant `kotobase:pin` over the tenant
 *     DID as graph scope — the SAME self-signed-CACAO mechanism ibuki uses for its kotoba
 *     write leash (ADR-2606111400), here scoped to pinning. No platform key is held: the
 *     CACAO is minted in the member/operator's own runtime and PRESENTED here.
 *
 * Endpoint base: `ETZ_KOTOBASE_URL` (default `https://kotobase.net`).
 * Gateway (informational, returned in the receipt): `ETZ_KOTOBASE_GATEWAY`
 * (no default; the field is omitted when unset).
 */

import { basename } from "node:path";

export interface KotobasePinResult {
  cid: string;
  receipt: {
    provider: "kotobase";
    base: string;
    requestid: string;
    status: string;
    auth: "bearer" | "cacao";
    /** Absent unless ETZ_KOTOBASE_GATEWAY is set — see DEFAULT_GATEWAY. */
    gatewayUrl?: string;
  };
}

interface PinStatus {
  requestid?: string;
  status?: string;
  pin?: { cid?: string; name?: string };
  error?: { reason?: string; details?: string };
}

const DEFAULT_BASE = "https://kotobase.net";
/**
 * No default gateway. This was "https://ipfs.gftd.ai", which answers 530
 * (origin unreachable, measured 2026-07-29), so every receipt carried a
 * retrieval URL that does not retrieve.
 *
 * It is not swapped for another host. The gateway is informational — the pin
 * itself is durable at kotobase regardless — and which gateway a reader should
 * use is a deployment fact, not a library one: a public gateway can serve the
 * CID, but so can the operator's own node, and hardcoding either makes the
 * receipt assert something this code cannot know. Set ETZ_KOTOBASE_GATEWAY to
 * put a URL in the receipt; leave it unset and the field is omitted.
 *
 * Note kotobase.net's own llms-full.txt still points at ipfs.gftd.ai for
 * resolution, so that text is stale too.
 */
const DEFAULT_GATEWAY = "";
// CIDv1 base32 ('b' + base32lower) or CIDv0 ('Qm…'); a light shape guard, not a full decode.
const CID_RE = /^(b[a-z2-7]{20,}|Qm[1-9A-HJ-NP-Za-km-z]{44})$/;

function trim(url: string): string {
  return url.replace(/\/+$/, "");
}

/** Root CID = the CAR filename stem (mst-projector writes `<rootCid>.car`). */
export function rootCidFromCarPath(carPath: string): string {
  const stem = basename(carPath).replace(/\.car$/i, "");
  if (!CID_RE.test(stem)) {
    throw new Error(
      `[ipfs-pinner/kotobase] CAR filename ${basename(carPath)!} does not encode a CID stem ` +
        `(expected <rootCid>.car); got ${stem!}`,
    );
  }
  return stem;
}

interface KotobaseAuth {
  headers: Record<string, string>;
  kind: "bearer" | "cacao";
}

/** Build the auth headers from env — Bearer JWT OR self-signed CACAO, never a held key. */
export function kotobaseAuth(
  env: Record<string, string | undefined> = process.env,
): KotobaseAuth {
  const jwt = env.ETZ_KOTOBASE_JWT;
  const cacao = env.ETZ_KOTOBASE_CACAO;
  const did = env.ETZ_KOTOBASE_DID;
  if (jwt) {
    return { headers: { authorization: `Bearer ${jwt}` }, kind: "bearer" };
  }
  if (cacao && did) {
    return {
      headers: { authorization: `CACAO ${cacao}`, "x-kotoba-did": did },
      kind: "cacao",
    };
  }
  throw new Error(
    "[ipfs-pinner/kotobase] needs ETZ_KOTOBASE_JWT, or ETZ_KOTOBASE_CACAO + ETZ_KOTOBASE_DID " +
      "(self-signed CACAO granting kotobase:pin). No platform key is held — the credential is " +
      "minted in the member/operator's own runtime and presented here.",
  );
}

async function postPin(
  base: string,
  auth: KotobaseAuth,
  cid: string,
  name: string,
): Promise<PinStatus> {
  const res = await fetch(`${trim(base)}/pins`, {
    method: "POST",
    headers: { "content-type": "application/json", ...auth.headers },
    body: JSON.stringify({ cid, name }),
  });
  const body = (await res.json().catch(() => ({}))) as PinStatus;
  if (!res.ok) {
    const reason = body.error?.reason ?? `HTTP ${res.status}`;
    throw new Error(`[ipfs-pinner/kotobase] POST /pins failed: ${reason}`);
  }
  if (body.pin?.cid && body.pin.cid !== cid) {
    throw new Error(
      `[ipfs-pinner/kotobase] PinStatus cid mismatch: submitted ${cid}, got ${body.pin.cid}`,
    );
  }
  return body;
}

export async function kotobase(carPath: string): Promise<KotobasePinResult> {
  const base = trim(process.env.ETZ_KOTOBASE_URL ?? DEFAULT_BASE);
  const gateway = trim(process.env.ETZ_KOTOBASE_GATEWAY ?? DEFAULT_GATEWAY);
  const auth = kotobaseAuth();
  const cid = rootCidFromCarPath(carPath);
  const status = await postPin(base, auth, cid, cid);
  return {
    cid,
    receipt: {
      provider: "kotobase",
      base,
      requestid: status.requestid ?? "",
      status: status.status ?? "unknown",
      auth: auth.kind,
      ...(gateway ? { gatewayUrl: `${gateway}/ipfs/${cid}` } : {}),
    },
  };
}

/** Test seam — exposes pure internals for unit tests that inject a fake `fetch`. */
export const __testing = { rootCidFromCarPath, kotobaseAuth, postPin };
