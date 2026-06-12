#!/usr/bin/env python3
"""hinagata 雛形 — kotoba IPFS content-address (CIDv1, raw, sha2-256, base32).

Pure-stdlib re-implementation of the repo-canonical content-address used by the WASM
loaders (20-actors/*/wasm/verify.mjs, ADR-2605231525 / 2606014500): CIDv1, raw codec
(0x55), multihash sha2-256 (0x12 0x20), multibase base32-lower with the 'b' prefix. This
is the SAME CID `ipfs add --cid-version=1 --raw-leaves` produces for a single raw block
(< 256 KiB), so a published template body's content-address is verifiable with or without
the `ipfs` daemon — anyone can re-derive the CID of a hinagata template and confirm the
bytes they fetched are the bytes the commons published (G4).

Single-block only by design: an individual template body / clause text fits one raw block.
Artifacts > 256 KiB would chunk into a UnixFS dag-pb tree (root codec 0x70) and need the
ipfs builder — out of scope for a single document.
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


def sha256_hex(data: bytes) -> str:
    """0x-prefixed lowercase hex SHA-256 — the esign documentSha256 defense-in-depth hash."""
    return "0x" + hashlib.sha256(data).hexdigest()


SINGLE_BLOCK_LIMIT = 256 * 1024  # ipfs default chunk size; above this the raw CID no longer applies


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        with open(p, "rb") as f:
            data = f.read()
        warn = "  ⚠ >256KiB: dag-pb, not single raw block" if len(data) > SINGLE_BLOCK_LIMIT else ""
        print(f"{cidv1_raw(data)}  {sha256_hex(data)}  {p}  ({len(data)} B){warn}")
