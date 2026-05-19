import { createHash } from "node:crypto";

/**
 * Deterministic content-addressed rkey for KG records.
 *
 * Format: 13 characters from the ATProto TID alphabet (base32-sortable lowercase, no padding,
 * uppercase removed). Not a real timestamp-ordered TID — same input always returns the
 * same rkey, which is exactly what projector idempotency requires.
 *
 * Collision space: 13 chars * 5 bits = 65 bits. Birthday bound ≈ 2^32 records.
 * The projector emits O(10^3) records today, so collisions are not a concern.
 */
const ALPHABET = "234567abcdefghijklmnopqrstuvwxyz"; // ATProto TID alphabet

export function deterministicRkey(canonicalInput: string): string {
  const hash = createHash("sha256").update(canonicalInput, "utf8").digest();
  let bits = 0n;
  for (const byte of hash.slice(0, 9)) bits = (bits << 8n) | BigInt(byte);
  // We need 13 * 5 = 65 bits; 9 bytes = 72 bits. Trim high 7 bits.
  bits &= (1n << 65n) - 1n;
  let out = "";
  for (let i = 0; i < 13; i++) {
    const idx = Number(bits & 0x1fn);
    out = ALPHABET[idx] + out;
    bits >>= 5n;
  }
  return out;
}

export function sha256Hex(input: string): string {
  return createHash("sha256").update(input, "utf8").digest("hex");
}
