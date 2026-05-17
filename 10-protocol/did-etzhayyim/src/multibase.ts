/**
 * Multibase encoder/decoder (subset for CIDv1).
 *
 * Spec: draft-multiformats-multibase-08
 * https://github.com/multiformats/multibase
 *
 * Supported prefixes (sufficient for CIDv1 IPFS canonical form):
 *   'b' — base32 lowercase, RFC 4648 §6, no padding
 *   'f' — base16 lowercase
 *   'z' — base58btc (used by Multikey publicKeyMultibase)
 */

const BASE32_LOWER_ALPHABET = "abcdefghijklmnopqrstuvwxyz234567";
const BASE58BTC_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

export function encodeBase32(bytes: Uint8Array): string {
  let bits = 0;
  let value = 0;
  let out = "";
  for (const byte of bytes) {
    value = (value << 8) | byte;
    bits += 8;
    while (bits >= 5) {
      out += BASE32_LOWER_ALPHABET[(value >>> (bits - 5)) & 0x1f];
      bits -= 5;
    }
  }
  if (bits > 0) {
    out += BASE32_LOWER_ALPHABET[(value << (5 - bits)) & 0x1f];
  }
  return out;
}

export function decodeBase32(str: string): Uint8Array {
  const out: number[] = [];
  let bits = 0;
  let value = 0;
  for (const ch of str.toLowerCase()) {
    const idx = BASE32_LOWER_ALPHABET.indexOf(ch);
    if (idx < 0) throw new Error(`invalid base32 char: ${ch}`);
    value = (value << 5) | idx;
    bits += 5;
    if (bits >= 8) {
      out.push((value >>> (bits - 8)) & 0xff);
      bits -= 8;
    }
  }
  return new Uint8Array(out);
}

export function encodeBase16(bytes: Uint8Array): string {
  let s = "";
  for (const b of bytes) s += b.toString(16).padStart(2, "0");
  return s;
}

export function decodeBase16(hex: string): Uint8Array {
  if (hex.length % 2 !== 0) throw new Error("odd-length hex");
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i += 1) {
    const v = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
    if (Number.isNaN(v)) throw new Error("invalid hex");
    out[i] = v;
  }
  return out;
}

export function encodeBase58btc(bytes: Uint8Array): string {
  if (bytes.length === 0) return "";
  const digits = [0];
  for (const byte of bytes) {
    let carry = byte;
    for (let i = 0; i < digits.length; i += 1) {
      carry += digits[i] * 256;
      digits[i] = carry % 58;
      carry = Math.floor(carry / 58);
    }
    while (carry > 0) {
      digits.push(carry % 58);
      carry = Math.floor(carry / 58);
    }
  }
  let leadingZeros = 0;
  for (const b of bytes) {
    if (b !== 0) break;
    leadingZeros += 1;
  }
  let out = BASE58BTC_ALPHABET[0].repeat(leadingZeros);
  for (let i = digits.length - 1; i >= 0; i -= 1) out += BASE58BTC_ALPHABET[digits[i]];
  return out;
}

export type MultibasePrefix = "b" | "f" | "z";

export function multibaseEncode(prefix: MultibasePrefix, bytes: Uint8Array): string {
  switch (prefix) {
    case "b": return "b" + encodeBase32(bytes);
    case "f": return "f" + encodeBase16(bytes);
    case "z": return "z" + encodeBase58btc(bytes);
  }
}

export function multibaseDecode(s: string): { prefix: MultibasePrefix; bytes: Uint8Array } {
  if (s.length < 2) throw new Error("multibase string too short");
  const prefix = s[0] as MultibasePrefix;
  const body = s.slice(1);
  switch (prefix) {
    case "b": return { prefix, bytes: decodeBase32(body) };
    case "f": return { prefix, bytes: decodeBase16(body) };
    case "z": throw new Error("base58btc decode not implemented (encode only — used for Multikey)");
    default:  throw new Error(`unsupported multibase prefix: ${prefix}`);
  }
}
