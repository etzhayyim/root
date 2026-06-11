#!/usr/bin/env python3
"""hinagata 雛形 — electronic-contract (esign bridge) tests (ADR-2606111954). Pure stdlib.

Verifies the contract-signing flow that wires the EXISTING com.etzhayyim.esign.* lexicons:
  - a template renders to a deterministic document carrying its statutory provenance
  - the document is content-addressed (CIDv1 raw, ipfs-parity) + SHA-256 hashed
  - build_envelope produces a schema-shaped com.etzhayyim.esign.envelope (no server key)
  - verify_signature enforces roster membership + document-hash anti-tamper binding
  - check_completion fires only when EVERY roster signer has a valid signature
  - no-server-key: hinagata never signs — it builds unsigned records + verifies structure
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
from cid import cidv1_raw, sha256_hex  # noqa: E402
import esign  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-legal-template-graph.kotoba.edn"


def _graph():
    return load(SEED)


def test_render_is_deterministic_and_traceable():
    nodes, edges = _graph()
    a = esign.render_document("tmpl.dpa-gdpr", nodes, edges)
    b = esign.render_document("tmpl.dpa-gdpr", nodes, edges)
    assert a == b, "document render is not deterministic"
    # the rendered body must carry the statute citations the clauses rest on (traceability)
    assert "GDPR Art. 28" in a, "rendered DPA missing its mandating statute citation"
    assert "NOT legal advice" in a, "G1 disclaimer missing from rendered document"
    # missing fields render as explicit blanks, never invented
    assert "[___]" in a, "missing fields should render as explicit blanks"


def test_render_rejects_non_template():
    nodes, edges = _graph()
    try:
        esign.render_document("cl.confidentiality", nodes, edges)
        assert False, "render_document accepted a non-template node"
    except ValueError:
        pass


def test_envelope_shape_and_content_address():
    nodes, edges = _graph()
    doc = esign.render_document("tmpl.nda-mutual", nodes, edges)
    env = esign.build_envelope(doc, "did:web:etzhayyim.com:actor:x",
                               ["did:plc:alice", "did:plc:bob"], subject="NDA",
                               created_at="2026-06-11T00:00:00Z")
    assert env["$type"] == "com.etzhayyim.esign.envelope"
    for k in ("requesterDid", "documentCid", "documentSha256", "signers", "signingOrder",
              "status", "createdAt"):
        assert k in env, f"envelope missing required field {k}"
    # content-address matches an independent recompute (ipfs-parity CID + hash)
    raw = doc.encode("utf-8")
    assert env["documentCid"] == cidv1_raw(raw)
    assert env["documentSha256"] == sha256_hex(raw)
    assert env["documentCid"].startswith("bafkrei"), "not a CIDv1 raw/sha2-256"
    assert len(env["documentSha256"]) == 66 and env["documentSha256"].startswith("0x")


def _sig(env, did, alg="ES256", tamper=False):
    return {
        "$type": "com.etzhayyim.esign.signature",
        "signerDid": did,
        "documentSha256": "0x" + "00" * 32 if tamper else env["documentSha256"],
        "webauthnAlgorithm": alg,
        "assertionEnvelope": "ciphertext-stub",
        "signedAt": "2026-06-11T01:00:00Z",
    }


def test_verify_signature_binding():
    nodes, edges = _graph()
    doc = esign.render_document("tmpl.nda-mutual", nodes, edges)
    env = esign.build_envelope(doc, "did:web:x", ["did:plc:alice", "did:plc:bob"])

    ok, reasons = esign.verify_signature(env, _sig(env, "did:plc:alice"))
    assert ok, f"valid signature rejected: {reasons}"

    ok, reasons = esign.verify_signature(env, _sig(env, "did:plc:mallory"))
    assert not ok and any("roster" in r for r in reasons), "off-roster signer accepted"

    ok, reasons = esign.verify_signature(env, _sig(env, "did:plc:alice", tamper=True))
    assert not ok and any("tamper" in r or "mismatch" in r for r in reasons), \
        "tampered document hash accepted"

    ok, reasons = esign.verify_signature(env, _sig(env, "did:plc:alice", alg="RS256"))
    assert not ok and any("algorithm" in r for r in reasons), "unsupported algorithm accepted"


def test_completion_requires_all_signers():
    nodes, edges = _graph()
    doc = esign.render_document("tmpl.loan-qard", nodes, edges)
    env = esign.build_envelope(doc, "did:web:x", ["did:plc:alice", "did:plc:bob"],
                               signing_order="sequential")
    # only one of two signed → no completion
    assert esign.check_completion(env, [_sig(env, "did:plc:alice")]) is None
    # both signed → completedEvent fires
    ev = esign.check_completion(env, [_sig(env, "did:plc:alice"), _sig(env, "did:plc:bob")],
                                completed_at="2026-06-11T02:00:00Z")
    assert ev is not None and ev["$type"] == "com.etzhayyim.esign.completedEvent"
    assert ev["signatureCount"] == 2
    assert ev["documentSha256"] == env["documentSha256"]
    # a tampered signature does not count toward completion
    assert esign.check_completion(
        env, [_sig(env, "did:plc:alice"), _sig(env, "did:plc:bob", tamper=True)]) is None


def test_no_server_key_marker_present():
    """The esign bridge must declare it holds no signing key (ADR-2605231525)."""
    src = (ACTOR_DIR / "methods" / "esign.py").read_text(encoding="utf-8")
    assert "no-server-key" in src, "esign.py missing no-server-key declaration"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
