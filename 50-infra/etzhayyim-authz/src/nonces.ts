/**
 * Provisioning nonce store. Single-use, 5-minute TTL.
 *
 * Production: backed by CF KV (NONCES binding).
 * Dev / wrangler dev without KV: in-memory Map fallback (not durable
 * across Worker restarts; acceptable only for testing).
 */

import type { Address, Hex } from "viem";

export interface NoncePayload {
  dwebHandleHash: Hex;
  dwebHandle: string;
  activeKey: Address;
  digest: Hex;
  chainId: number;
  contractAddress: Address;
  createdAtMs: number;
  purposeNarrow?: string;
  // Phase α P2 mirror flow only:
  vendorRootDid?: string;
  vendorAddr?: Address;
}

const TTL_MS = 5 * 60 * 1000;

const memoryStore = new Map<string, NoncePayload>();

export interface NonceStore {
  put(nonce: string, payload: NoncePayload): Promise<void>;
  consume(nonce: string): Promise<NoncePayload | null>;
}

export function makeNonceStore(kv: KVNamespace | undefined): NonceStore {
  if (kv) {
    return {
      async put(nonce, payload) {
        await kv.put(nonce, JSON.stringify(payload), { expirationTtl: TTL_MS / 1000 });
      },
      async consume(nonce) {
        const raw = await kv.get(nonce);
        if (!raw) return null;
        await kv.delete(nonce);
        const parsed = JSON.parse(raw) as NoncePayload;
        if (Date.now() - parsed.createdAtMs > TTL_MS) return null;
        return parsed;
      },
    };
  }
  return {
    async put(nonce, payload) {
      memoryStore.set(nonce, payload);
    },
    async consume(nonce) {
      const v = memoryStore.get(nonce);
      if (!v) return null;
      memoryStore.delete(nonce);
      if (Date.now() - v.createdAtMs > TTL_MS) return null;
      return v;
    },
  };
}

export function newNonce(): string {
  // 16 random bytes, hex-encoded — 128 bits, sufficient for collision
  // resistance over a 5-min window with thousands of pending nonces.
  const buf = new Uint8Array(16);
  crypto.getRandomValues(buf);
  return "0x" + Array.from(buf).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export function noncePayloadFreshSec(p: NoncePayload): number {
  return Math.max(0, Math.floor((TTL_MS - (Date.now() - p.createdAtMs)) / 1000));
}
