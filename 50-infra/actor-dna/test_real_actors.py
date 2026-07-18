"""test_real_actors.py — the committed Actor DNA of a REAL deployed actor (tsumugi) verifies
against its actual on-disk WASM + schema, byte-for-byte. This proves the substrate binds real
code, not a mock: the manifest's :dna/wasm-cid IS the CID tsumugi.did.json advertises.

Paths are relative to 50-infra/actor-dna/ (where run_tests.sh runs)."""
from __future__ import annotations

import pathlib
import re

import cid as cidlib
import dna as dnalib
from _t import run

_ROOT = pathlib.Path(__file__).resolve().parents[2]   # repo root from 50-infra/actor-dna/
TSUMUGI = _ROOT / "orgs/etzhayyim/com-etzhayyim-tsumugi"
WASM = TSUMUGI / "wasm/loader/tsumugi-core.wasm"
LEXICON = _ROOT / "00-contracts/schemas/engi-organism-ontology.kotoba.edn"
DNA_EDN = TSUMUGI / "dna/tsumugi.dna.edn"
RULES_EDN = TSUMUGI / "dna/tsumugi.integrity.edn"

# the actor's published wasm CID (tsumugi.did.json EtzhayyimWasmComponent service)
PUBLISHED_WASM_CID = "bafkreidfttpqimwnx4i5a3rswum3orcg3qfa3q7fwts6axgqtcpuokddfi"
# the golden DNA CID — tsumugi's single content-addressed identity
GOLDEN_DNA_CID = "bafkreibmg6zwuq7ftxrk33sjf6tg7s6j3f7ggj5nanqcbkekx5rimdl7v4"


def _parse_manifest(text: str) -> dict:
    """Tiny extractor for the flat `:key "value"` manifest (no full EDN parser needed)."""
    return {k: v for k, v in re.findall(r'(:[\w.\-/]+)\s+"([^"]*)"', text)}


def test_committed_artifacts_exist():
    for p in (WASM, LEXICON, DNA_EDN, RULES_EDN):
        assert p.exists(), p


def test_wasm_cid_matches_the_real_deployed_program_and_the_published_did():
    real = cidlib.cidv1_raw(WASM.read_bytes())
    assert real == PUBLISHED_WASM_CID, real         # the substrate reproduces the deployed CID
    m = _parse_manifest(DNA_EDN.read_text())
    assert m[":dna/wasm-cid"] == real               # the manifest binds the REAL code


def test_lexicon_and_validation_cids_address_the_committed_files():
    m = _parse_manifest(DNA_EDN.read_text())
    assert m[":dna/lexicon-cid"] == cidlib.cidv1_raw(LEXICON.read_bytes())
    # the rules file was written canonical + a trailing newline; the CID is of the canonical bytes
    assert m[":dna/validation-cid"] == cidlib.cidv1_raw(RULES_EDN.read_bytes().rstrip(b"\n"))


def test_graph_binding_is_asserted_and_correct():
    m = _parse_manifest(DNA_EDN.read_text())
    assert m[":dna/graph"] == "tsumugi"
    assert m[":dna/graph-cid"] == cidlib.graph_cid("tsumugi")


def test_committed_manifest_round_trips_to_the_golden_dna_cid():
    m = _parse_manifest(DNA_EDN.read_text())
    # rebuild via the canonical path and confirm the committed file IS canonical (byte-identical)
    assert dnalib.manifest_edn(m) == DNA_EDN.read_text().rstrip("\n").encode("utf-8")
    assert dnalib.dna_cid(m) == GOLDEN_DNA_CID
    ok, why = dnalib.verify(m, blobs={":dna/wasm-cid": WASM.read_bytes()})
    assert ok, why


if __name__ == "__main__":
    run("real_actors", [(n, f) for n, f in sorted(globals().items())
                        if n.startswith("test_") and callable(f)])
