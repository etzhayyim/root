/**
 * Minimal deterministic CBOR encoder for a CACAO (ADR-2606061800).
 *
 * The kotoba node decodes `cacaoB64` with `ciborium::from_reader` over the
 * `Cacao { h, p, s }` struct (serde maps with the renamed keys `iat`/`exp`). We
 * only need to ENCODE that exact shape: definite-length maps + text strings +
 * a text array (`resources`). This is the verify-only relay's sole job — the
 * member signs the CACAO; the Worker just re-encodes its JSON form to the CBOR
 * the node expects (proven end-to-end against a live kotoba node).
 *
 * No general CBOR library is bundled; this hand-rolled encoder is exact for the
 * Cacao value space (text/array/map only, lengths < 65536).
 */

import type { Cacao } from "./cacao.ts";

function head(major: number, n: number): Uint8Array {
  const m = major << 5;
  if (n < 24) return Uint8Array.from([m | n]);
  if (n < 256) return Uint8Array.from([m | 24, n]);
  return Uint8Array.from([m | 25, (n >> 8) & 0xff, n & 0xff]);
}

function concat(parts: Uint8Array[]): Uint8Array {
  let n = 0;
  for (const p of parts) n += p.length;
  const out = new Uint8Array(n);
  let i = 0;
  for (const p of parts) {
    out.set(p, i);
    i += p.length;
  }
  return out;
}

function cText(s: string): Uint8Array {
  const u = new TextEncoder().encode(s);
  return concat([head(3, u.length), u]);
}

function cArray(items: Uint8Array[]): Uint8Array {
  return concat([head(4, items.length), ...items]);
}

function cMap(pairs: [string, Uint8Array][]): Uint8Array {
  const parts: Uint8Array[] = [head(5, pairs.length)];
  for (const [k, v] of pairs) {
    parts.push(cText(k));
    parts.push(v);
  }
  return concat(parts);
}

function bytesToBase64(u: Uint8Array): string {
  let s = "";
  for (const b of u) s += String.fromCharCode(b);
  return btoa(s);
}

/**
 * Encode a CACAO to `base64(CBOR(Cacao))` — the `cacaoB64` the kotoba
 * `kg.ingest` endpoint expects. The payload key order mirrors the Rust struct
 * (`iss, aud, iat, exp, nonce, domain, statement, version, resources`), though
 * `from_reader` is order-independent.
 */
export function cacaoToCborBase64(cacao: Cacao): string {
  const p = cacao.p;
  const payloadPairs: [string, Uint8Array][] = [
    ["iss", cText(p.iss)],
    ["aud", cText(p.aud)],
    ["iat", cText(p.iat)],
  ];
  if (p.exp !== undefined) payloadPairs.push(["exp", cText(p.exp)]);
  payloadPairs.push(["nonce", cText(p.nonce)]);
  payloadPairs.push(["domain", cText(p.domain ?? "")]);
  if (p.statement !== undefined) payloadPairs.push(["statement", cText(p.statement)]);
  payloadPairs.push(["version", cText(p.version ?? "1")]);
  payloadPairs.push(["resources", cArray((p.resources ?? []).map(cText))]);

  const value = cMap([
    ["h", cMap([["t", cText(cacao.h.t)]])],
    ["p", cMap(payloadPairs)],
    ["s", cMap([["t", cText(cacao.s.t)], ["s", cText(cacao.s.s)]])],
  ]);
  return bytesToBase64(value);
}
