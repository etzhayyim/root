"""test_cid.py — the content-address helpers are byte-identical to the kotoba canon."""
from __future__ import annotations

import base64
import hashlib

import cid as c
from _t import run


def _oracle(codec: int, data: bytes) -> str:
    """Independent reference via stdlib base64.b32encode (proves the hand-rolled _base32)."""
    raw = bytes([0x01, codec, 0x12, 0x20]) + hashlib.sha256(data).digest()
    return "b" + base64.b32encode(raw).decode("ascii").rstrip("=").lower()


def test_raw_matches_stdlib_b32_oracle():
    for data in (b"", b"hello", b"\x00\x01\x02", b"the breath of life"):
        assert c.cidv1_raw(data) == _oracle(0x55, data), data


def test_dag_cbor_matches_stdlib_b32_oracle():
    for data in (b"", b"ibuki", b"actors-v1"):
        assert c.cidv1_dag_cbor(data) == _oracle(0x71, data), data


def test_graph_cid_is_dag_cbor_of_the_name():
    assert c.graph_cid("ibuki") == c.cidv1_dag_cbor(b"ibuki")
    assert c.graph_cid("ibuki").startswith("bafyrei")   # CIDv1 dag-cbor sha256 prefix


def test_raw_and_dag_cbor_differ_for_same_bytes():
    assert c.cidv1_raw(b"x") != c.cidv1_dag_cbor(b"x")   # codec is part of the address


def test_is_cidv1_shape_guard():
    assert c.is_cidv1(c.cidv1_raw(b"z"))
    assert c.is_cidv1(c.graph_cid("g"))
    assert not c.is_cidv1("Qm123")           # CIDv0 is not 'b'-multibase
    assert not c.is_cidv1("not-a-cid!")
    assert not c.is_cidv1("")


if __name__ == "__main__":
    run("cid", [(n, f) for n, f in sorted(globals().items())
                if n.startswith("test_") and callable(f)])
