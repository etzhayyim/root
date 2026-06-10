#!/usr/bin/env python3
"""rasen 螺旋 — kotoba IPFS content-address (CIDv1, raw, sha2-256, base32).

Pure-stdlib re-implementation of the repo-canonical content-address used by the WASM
loaders (20-actors/*/wasm/verify.mjs, ADR-2605231525 / 2606014500): CIDv1, raw codec
(0x55), multihash sha2-256 (0x12 0x20), multibase base32-lower with the 'b' prefix. This
is the SAME CID `ipfs add --cid-version=1 --raw-leaves` produces for a single raw block
(< 256 KiB), so a kotoba artifact's content-address is verifiable with or without the
`ipfs` daemon. Verified byte-identical against `ipfs` 0.41.0.

Single-block only by design: rasen ingests a BOUNDED public-reference slice (G5/G7), so the
EDN/Datom artifacts fit one raw block. Artifacts > 256 KiB would chunk into a UnixFS dag-pb
tree (root codec 0x70) and need the ipfs builder — out of scope for the bounded slice.
"""
from __future__ import annotations
import hashlib

_B32 = "abcdefghijklmnopqrstuvwxyz234567"  # RFC4648 base32 lower, no padding (multibase 'b')


def _base32(data: bytes) -> str:
    bits = val = 0
    out = []
    for b in data:
        val = (val << 8) | b
        bits += 8
        while bits >= 5:
            out.append(_B32[(val >> (bits - 5)) & 31])
            bits -= 5
    if bits > 0:
        out.append(_B32[(val << (5 - bits)) & 31])
    return "".join(out)


def cidv1_raw(data: bytes) -> str:
    """CIDv1 / raw (0x55) / sha2-256 — matches `ipfs add --cid-version=1 --raw-leaves`."""
    mh = bytes([0x12, 0x20]) + hashlib.sha256(data).digest()  # sha2-256, 32-byte digest
    cid = bytes([0x01, 0x55]) + mh                            # CIDv1, raw codec
    return "b" + _base32(cid)


SINGLE_BLOCK_LIMIT = 256 * 1024  # ipfs default chunk size; above this the raw CID no longer applies


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        with open(p, "rb") as f:
            data = f.read()
        warn = "  ⚠ >256KiB: dag-pb, not single raw block" if len(data) > SINGLE_BLOCK_LIMIT else ""
        print(f"{cidv1_raw(data)}  {p}  ({len(data)} B){warn}")
