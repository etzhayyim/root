/**
 * ipaddress rw-free — record types.
 *
 * Per ADR-2605203000 Option B (PDS XRPC). Mirrors the bootstrap
 * lexicons at 00-contracts/lexicons/ai/gftd/apps/ipaddress/* — those
 * are still `x-bootstrap` stubs; tightening follows in the next slice
 * alongside more command ports.
 *
 * Identity hierarchy (per CLAUDE.md authority-chain):
 *   did:web:ipaddress.etzhayyim.com                — controller
 *   did:web:ipaddress.etzhayyim.com:rir:{rir}      — RIR (apnic/arin/ripe/lacnic/afrinic)
 *   did:web:ipaddress.etzhayyim.com:nir:{cc}       — NIR (jpnic/cnnic/krnic/etc)
 *   did:web:ipaddress.etzhayyim.com:provider:{slug}
 *   did:web:ipaddress.etzhayyim.com:asn:{number}
 *   did:web:ipaddress.etzhayyim.com:prefix:{cidr}
 *   did:web:ipaddress.etzhayyim.com:ip:{address}
 */

export type Rir = "apnic" | "arin" | "ripe" | "lacnic" | "afrinic";

/** Record body for `ai.gftd.apps.ipaddress.asn`. */
export interface AsnRecord {
  did: string;
  number: number;
  name?: string;
  country?: string;
  rir?: Rir;
  prefixes?: string[];
  createdAt: string;
}

export interface AsnView extends AsnRecord {
  asnUri: string;
}

export interface RegisterAsnInput {
  number: number;
  name?: string;
  country?: string;
  rir?: Rir;
  prefixes?: string[];
}

export interface RegisterAsnOutput {
  status: "registered" | "alreadyExists" | "rejected";
  asnUri?: string;
  did?: string;
  number?: number;
  error?: string;
}

export interface GetAsnInput {
  number: number;
}

export interface GetAsnOutput {
  asn?: AsnView;
  error?: string;
}

export const IPADDRESS_DID_PREFIX =
  "did:web:ipaddress.etzhayyim.com:" as const;

/** Build the path-based DID for an ASN. */
export function asnDid(number: number): string {
  return `${IPADDRESS_DID_PREFIX}asn:${number}`;
}

/** rkey from ASN number — used for idempotent re-register. */
export function asnRkey(number: number): string {
  return `asn-${number}`;
}
