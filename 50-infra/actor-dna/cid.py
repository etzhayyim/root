#!/usr/bin/env python3
"""actor-dna — kotoba content-address helpers (CIDv1, sha2-256, base32-lower).

Pure-stdlib, byte-identical to the repo-canonical content-address (mirrors
`orgs/etzhayyim/com-etzhayyim-rasen/methods/cid.py` + `kotoba-core::KotobaCid`):

  - `cidv1_raw`     CIDv1 / raw codec (0x55)  — `ipfs add --cid-version=1 --raw-leaves`;
                    the address of a byte blob (a WASM program, a rules/lexicon EDN).
  - `cidv1_dag_cbor` CIDv1 / dag-cbor (0x71) — `KotobaCid::from_bytes`; the address kotoba
                    derives for a NAMED graph (`from_bytes(name.encode())`) and dag-cbor objs.

Both are single-block (< 256 KiB); above that an artifact chunks into a UnixFS dag-pb tree
(root codec 0x70) and needs the ipfs builder — out of scope (a DNA manifest is tiny).
"""
from __future__ import annotations

import hashlib

_B32 = "abcdefghijklmnopqrstuvwxyz234567"  # RFC4648 base32 lower, no padding (multibase 'b')
SINGLE_BLOCK_LIMIT = 256 * 1024


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
    """CIDv1 / raw (0x55) / sha2-256 — the content-address of a byte blob."""
    mh = bytes([0x12, 0x20]) + hashlib.sha256(data).digest()
    return "b" + _base32(bytes([0x01, 0x55]) + mh)


def cidv1_dag_cbor(data: bytes) -> str:
    """CIDv1 / dag-cbor (0x71) / sha2-256 — `KotobaCid::from_bytes(data)`; the named-graph CID."""
    mh = bytes([0x12, 0x20]) + hashlib.sha256(data).digest()
    return "b" + _base32(bytes([0x01, 0x71]) + mh)


def graph_cid(name: str) -> str:
    """The kotoba graph identifier for a graph NAME (`KotobaCid::from_bytes(name.bytes)`)."""
    return cidv1_dag_cbor(name.encode("utf-8"))


def is_cidv1(s: str) -> bool:
    """A light shape guard: multibase-'b' base32 of plausible length (not a full decode)."""
    return isinstance(s, str) and s.startswith("b") and len(s) >= 20 and all(c in _B32 for c in s[1:])
