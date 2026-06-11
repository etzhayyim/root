#!/usr/bin/env python3
"""Tests for wasm_sbom_gen — kotoba CID parity, CycloneDX shape, ingest binding.

Run:  python3 70-tools/scripts/wasm-sbom/test_wasm_sbom_gen.py
"""
import hashlib
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wasm_sbom_gen as W  # noqa: E402


# ── an INDEPENDENT RFC4648 base32-lower encoder (cross-checks base64.b32encode
#    so an alphabet/padding bug in the CID can't pass silently) ───────────────
_B32 = "abcdefghijklmnopqrstuvwxyz234567"


def _indep_base32_lower(data: bytes) -> str:
    bits = 0
    acc = 0
    out = []
    for byte in data:
        acc = (acc << 8) | byte
        bits += 8
        while bits >= 5:
            bits -= 5
            out.append(_B32[(acc >> bits) & 0x1F])
    if bits:
        out.append(_B32[(acc << (5 - bits)) & 0x1F])
    return "".join(out)


def test_cid_matches_independent_base32():
    payload = b"hello"
    cid, sha_hex = W.kotoba_program_cid(payload)
    assert sha_hex == hashlib.sha256(payload).hexdigest()
    cid_bytes = bytes([0x01, 0x71, 0x12, 0x20]) + hashlib.sha256(payload).digest()
    assert cid == "b" + _indep_base32_lower(cid_bytes), cid
    print("ok  cid_matches_independent_base32:", cid)


def test_cid_structure():
    cid, _ = W.kotoba_program_cid(b"any wasm bytes here")
    # CIDv1 dag-cbor sha2-256 over 36 bytes → 'b' + 58 base32 chars.
    assert cid.startswith("b") and len(cid) == 59, (cid, len(cid))
    # CIDv1(0x01) dag-cbor(0x71) → multibase 'b' + base32('\x01\x71…') starts 'af'
    assert cid[1:3] == "af", cid[:4]
    print("ok  cid_structure")


def test_cid_deterministic_and_distinct():
    a, _ = W.kotoba_program_cid(b"foo")
    b, _ = W.kotoba_program_cid(b"foo")
    c, _ = W.kotoba_program_cid(b"bar")
    assert a == b and a != c
    print("ok  cid_deterministic_and_distinct")


def test_requirements_parse():
    reqs = "# comment\nlanggraph>=0.2\ntyping_extensions>=4.0\npydantic==2.6.1 ; python_version>='3.9'\n-r other.txt\n"
    comps = W.parse_requirements(reqs, freeze={})
    by_name = {c["name"]: c for c in comps}
    assert set(by_name) == {"langgraph", "typing_extensions", "pydantic"}, by_name
    assert by_name["pydantic"]["purl"] == "pkg:pypi/pydantic@2.6.1"
    assert by_name["pydantic"]["version"] == "2.6.1"
    # >= becomes a constraint (honest: not a resolved lock)
    lg = by_name["langgraph"]
    assert lg["purl"] == "pkg:pypi/langgraph@0.2"
    src = [p["value"] for p in lg["properties"] if p["name"] == "wasm:versionSource"][0]
    assert src == "constraint", src
    # typing_extensions name normalized in purl
    assert by_name["typing_extensions"]["purl"].startswith("pkg:pypi/typing-extensions@")
    print("ok  requirements_parse")


def test_freeze_overrides_constraint():
    reqs = "langgraph>=0.2\n"
    freeze = W.parse_freeze("langgraph==0.2.74\n")
    comps = W.parse_requirements(reqs, freeze)
    assert comps[0]["purl"] == "pkg:pypi/langgraph@0.2.74"
    src = [p["value"] for p in comps[0]["properties"] if p["name"] == "wasm:versionSource"][0]
    assert src == "lock", src
    print("ok  freeze_overrides_constraint")


def _args(**kw):
    base = dict(actor="sumitsubo", world="kotoba-actor", program_type="wasm-node",
                built_by="componentize-py@0.23.0", sourcing="representative", adr="2606036000")
    base.update(kw)
    return types.SimpleNamespace(**base)


def test_cyclonedx_and_ingest_bind_to_cid():
    wasm = b"\x00asm\x01\x00\x00\x00 dummy component"
    cid, sha_hex = W.kotoba_program_cid(wasm)
    comps = W.parse_requirements("langgraph>=0.2\ntyping_extensions>=4.0\n", {})
    args = _args()
    cdx = W.build_cyclonedx(cid, sha_hex, len(wasm), args, comps)
    ing = W.build_ingest(cid, sha_hex, len(wasm), args, comps)

    # CycloneDX: primary component is the wasm, keyed by the program CID
    assert cdx["bomFormat"] == "CycloneDX" and cdx["specVersion"] == "1.5"
    mc = cdx["metadata"]["component"]
    assert mc["bom-ref"] == cid
    assert mc["hashes"][0]["content"] == sha_hex
    prog_cid_prop = [p for p in mc["properties"] if p["name"] == "kotoba:programCid"]
    assert prog_cid_prop and prog_cid_prop[0]["value"] == cid
    assert len(cdx["components"]) == 2
    # reproducible: no wall-clock timestamp
    assert "timestamp" not in cdx["metadata"]

    # ingest: image entity keyed by CID + each component bound via relation edge
    ents = {e["type"]: [] for e in ing["entities"]}
    for e in ing["entities"]:
        ents[e["type"]].append(e)
    assert len(ents["WasmActorImage"]) == 1
    img = ents["WasmActorImage"][0]
    assert img["id"] == cid
    claim = {c["pred"]: c["value"] for c in img["claims"]}
    assert claim["wasm/programCid"] == cid
    assert claim["wasm/actor"] == "sumitsubo"
    assert claim["wasm/world"] == "kotoba-actor"
    assert claim["wasm/sha256"] == sha_hex
    assert len(ents["SbomComponent"]) == 2
    for c in ents["SbomComponent"]:
        cl = {x["pred"]: x["value"] for x in c["claims"]}
        assert cl["cdx/purl"].startswith("pkg:pypi/")  # VulnMatch join key present
        rel = c["relations"][0]
        assert rel["pred"] == "wasm/componentOf" and rel["dstId"] == cid
    print("ok  cyclonedx_and_ingest_bind_to_cid")


def test_from_cdx_rust_path():
    # a cargo-cyclonedx-shaped doc (rust actor) is re-keyed by the program CID
    rust_cdx = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.3",
        "components": [
            {"type": "library", "name": "serde", "version": "1.0.197",
             "purl": "pkg:cargo/serde@1.0.197"},
        ],
    }
    comps = W.components_from_cdx(rust_cdx)
    wasm = b"rust wasm bytes"
    cid, sha_hex = W.kotoba_program_cid(wasm)
    ing = W.build_ingest(cid, sha_hex, len(wasm), _args(actor="tsumugi", world=""), comps)
    sbom_comps = [e for e in ing["entities"] if e["type"] == "SbomComponent"]
    assert len(sbom_comps) == 1
    cl = {x["pred"]: x["value"] for x in sbom_comps[0]["claims"]}
    assert cl["cdx/purl"] == "pkg:cargo/serde@1.0.197"
    assert sbom_comps[0]["relations"][0]["dstId"] == cid
    print("ok  from_cdx_rust_path")


def main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print(f"\n{len(fns)}/{len(fns)} wasm-sbom tests green")


if __name__ == "__main__":
    main()
