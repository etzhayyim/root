#!/usr/bin/env python3
"""cidtool.py — minimal CIDv1 helpers for kotoba-b2-pin (stdlib only).

Used by the shell scripts to:
  * list-heads     : print "graph_ipns<TAB>head_cid" for each durable IPNS head
  * codec <cid>    : print the multicodec name of a CIDv1 (for `block put --cid-codec`)

No external deps. base32 (RFC4648 lower, no pad) is the 'b' multibase used by
kubo CIDv1 strings (bafy…). We only need to read the codec varint, so a partial
decode is enough and avoids pulling in py-multiformats.
"""
import base64
import json
import os
import sys

# multicodec code -> name (the codecs kotoba/kubo actually emit)
CODECS = {
    0x55: "raw",
    0x70: "dag-pb",
    0x71: "dag-cbor",
    0x0129: "dag-json",
}


def _b32_decode(s: str) -> bytes:
    # multibase 'b' = base32 lower, no padding
    body = s[1:]  # strip multibase prefix
    pad = (-len(body)) % 8
    return base64.b32decode(body.upper() + "=" * pad)


def _read_uvarint(b: bytes, i: int):
    x = 0
    shift = 0
    while True:
        byte = b[i]
        i += 1
        x |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return x, i


def codec_of(cid: str) -> str:
    if not cid.startswith("b"):
        # CIDv0 (Qm…) is dag-pb by definition
        return "dag-pb"
    raw = _b32_decode(cid)
    i = 0
    version, i = _read_uvarint(raw, i)
    if version != 1:
        return "dag-pb"
    codec, i = _read_uvarint(raw, i)
    return CODECS.get(codec, f"0x{codec:x}")


def list_heads(path: str):
    with open(os.path.expanduser(path)) as f:
        heads = json.load(f)
    for h in heads:
        cid = h.get("value") or ""
        name = h.get("name") or ""
        if cid:
            print(f"{name}\t{cid}")


def main(argv):
    if not argv:
        print("usage: cidtool.py {list-heads <heads.json> | codec <cid>}", file=sys.stderr)
        return 2
    cmd = argv[0]
    if cmd == "list-heads":
        list_heads(argv[1])
    elif cmd == "codec":
        print(codec_of(argv[1]))
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
