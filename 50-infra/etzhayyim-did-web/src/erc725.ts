/**
 * On-chain ERC725 verificationMethod mirror (ADR-2606015200, realizing
 * ADR-2605212030 Phase B / ADR-2606013800 "vm is a MIRROR, never server-minted").
 *
 * Reads `EtzhayyimAuthz.resolveDwebHandle(keccak256("<handle>.etzhayyim.com"))`
 * from Base L2 via `eth_call` and maps the returned active key to a DID
 * verificationMethod. GATED + best-effort: returns [] unless both
 * AUTHZ_CONTRACT_ADDRESS and BASE_RPC_URL are configured, and on any error — so
 * did:web resolution never depends on the chain (TLS trust holds, no server key).
 *
 * No live contract yet (EtzhayyimAuthz pending Base Sepolia) → this returns [] in
 * practice; the pure pieces (keccak256, node derivation, key→vm mapping) are
 * unit-tested so the wiring is correct the moment the contract lands.
 */

export interface Erc725Env {
  readonly AUTHZ_CONTRACT_ADDRESS?: string;
  readonly BASE_RPC_URL?: string;
  readonly CHAIN_ID?: string;
}

// ── keccak-256 (Keccak-f[1600], rate 1088, pad 0x01…0x80) ───────────────────
const RC: bigint[] = [
  0x0000000000000001n, 0x0000000000008082n, 0x800000000000808an,
  0x8000000080008000n, 0x000000000000808bn, 0x0000000080000001n,
  0x8000000080008081n, 0x8000000000008009n, 0x000000000000008an,
  0x0000000000000088n, 0x0000000080008009n, 0x000000008000000an,
  0x000000008000808bn, 0x800000000000008bn, 0x8000000000008089n,
  0x8000000000008003n, 0x8000000000008002n, 0x8000000000000080n,
  0x000000000000800an, 0x800000008000000an, 0x8000000080008081n,
  0x8000000000008080n, 0x0000000080000001n, 0x8000000080008008n,
];
const R = [
  [0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61],
  [28, 55, 25, 21, 56], [27, 20, 39, 8, 14],
];
const M64 = (1n << 64n) - 1n;
const rotl = (x: bigint, n: number): bigint =>
  ((x << BigInt(n)) | (x >> BigInt(64 - n))) & M64;

function keccakF(s: bigint[]): void {
  for (let round = 0; round < 24; round++) {
    const c = [0n, 0n, 0n, 0n, 0n];
    for (let x = 0; x < 5; x++)
      c[x] = s[x] ^ s[x + 5] ^ s[x + 10] ^ s[x + 15] ^ s[x + 20];
    const d = [0n, 0n, 0n, 0n, 0n];
    for (let x = 0; x < 5; x++) d[x] = c[(x + 4) % 5] ^ rotl(c[(x + 1) % 5], 1);
    for (let x = 0; x < 5; x++)
      for (let y = 0; y < 5; y++) s[x + 5 * y] ^= d[x];
    const b: bigint[] = new Array(25).fill(0n);
    for (let x = 0; x < 5; x++)
      for (let y = 0; y < 5; y++)
        b[y + 5 * ((2 * x + 3 * y) % 5)] = rotl(s[x + 5 * y], R[x][y]);
    for (let x = 0; x < 5; x++)
      for (let y = 0; y < 5; y++)
        s[x + 5 * y] =
          b[x + 5 * y] ^ (~b[((x + 1) % 5) + 5 * y] & b[((x + 2) % 5) + 5 * y]);
    s[0] ^= RC[round];
  }
}

export function keccak256(input: Uint8Array): Uint8Array {
  const rate = 136; // bytes
  const padded = new Uint8Array(Math.ceil((input.length + 1) / rate) * rate);
  padded.set(input);
  padded[input.length] ^= 0x01;
  padded[padded.length - 1] ^= 0x80;
  const s: bigint[] = new Array(25).fill(0n);
  for (let off = 0; off < padded.length; off += rate) {
    for (let i = 0; i < rate / 8; i++) {
      let lane = 0n;
      for (let j = 0; j < 8; j++)
        lane |= BigInt(padded[off + i * 8 + j]) << BigInt(8 * j);
      s[i] ^= lane;
    }
    keccakF(s);
  }
  const out = new Uint8Array(32);
  for (let i = 0; i < 4; i++) {
    let lane = s[i];
    for (let j = 0; j < 8; j++) {
      out[i * 8 + j] = Number(lane & 0xffn);
      lane >>= 8n;
    }
  }
  return out;
}

const hex = (b: Uint8Array): string =>
  [...b].map((x) => x.toString(16).padStart(2, "0")).join("");

/** keccak256("<handle>.etzhayyim.com") → 0x… node id (the contract's key). */
export function dwebHandleNode(handle: string): string {
  return "0x" + hex(keccak256(new TextEncoder().encode(`${handle}.etzhayyim.com`)));
}

/** 4-byte function selector for `resolveDwebHandle(bytes32)`. */
function selector(): string {
  return hex(keccak256(new TextEncoder().encode("resolveDwebHandle(bytes32)"))).slice(0, 8);
}

/** Map an on-chain active key (33/65-byte secp256k1 pubkey hex, or empty) to a
 *  DID verificationMethod array. Empty / zero key → []. */
export function activeKeyToVm(
  did: string,
  contract: string,
  keyHex: string,
): Record<string, unknown>[] {
  const clean = keyHex.replace(/^0x/, "");
  if (!clean || /^0+$/.test(clean)) return [];
  return [
    {
      id: `${did}#authz-key`,
      type: "EcdsaSecp256k1VerificationKey2019",
      controller: did,
      chainRef: `did:erc725:base:${contract}#${dwebHandleNode(did.split(":").pop() || "")}`,
      publicKeyHex: `0x${clean}`,
    },
  ];
}

/** Best-effort on-chain read; returns [] unless configured + the call succeeds. */
export async function fetchOnChainVm(
  env: Erc725Env,
  handle: string,
  did: string,
): Promise<Record<string, unknown>[]> {
  const contract = env.AUTHZ_CONTRACT_ADDRESS;
  const rpc = env.BASE_RPC_URL;
  if (!contract || !rpc) return [];
  try {
    const node = dwebHandleNode(handle).replace(/^0x/, "");
    const data = "0x" + selector() + node.padStart(64, "0");
    const res = await fetch(rpc, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "eth_call",
        params: [{ to: contract, data }, "latest"],
      }),
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) return [];
    const json = (await res.json()) as { result?: string };
    if (!json.result || json.result === "0x") return [];
    return activeKeyToVm(did, contract, json.result);
  } catch {
    return [];
  }
}
