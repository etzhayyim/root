#!/usr/bin/env python3
"""dna.py — the Actor DNA manifest: ONE content-addressed unit binding CODE + DATA.

The gap this closes (ADR-2606112000). Today a kotoba actor is FOUR separate content-addresses
linked only by references in did.json: the WASM program CID, the data-graph CID, the validation
rules, the lexicon. Ethereum (bytecode+storage at one account) and Holochain (a DNA hash wrapping
WASM zomes + integrity rules + the DHT) instead bind code and data into ONE identity. The Actor
DNA manifest is that single binding for kotoba:

    {:dna/spec "kotoba-actor-dna/v0"
     :dna/actor-did   "did:web:etzhayyim.com:actor:<h>"
     :dna/wasm-cid    "b…"      ; CODE   — raw CID of the WASM program (ipfs add -raw)
     :dna/graph       "<name>"  ; DATA   — the graph this code governs
     :dna/graph-cid   "b…"      ; DERIVED = graph_cid(:dna/graph) — the binding is ASSERTED,
     :dna/validation-cid "b…"   ;          not implicit; verify() recomputes + checks it
     :dna/lexicon-cid "b…"      ; the schema the data conforms to
     :dna/capability  "datom:transact"}

The manifest is itself a content-addressed object: `dna_cid(manifest)` = the raw CID of its
canonical EDN bytes (pinnable to kotobase.net like any block, ADR-2606091500). That single
DNA CID becomes the actor's canonical identity — did.json points to `ipfs://<dna-cid>` and
nothing else. Change ANY part (recompile the WASM, edit a rule, retarget the graph) → a new
validation/wasm/graph CID → a new DNA CID → a different actor. Code and data are now fused
into one tamper-evident hash, the Holochain-DNA / Ethereum-account property kotoba lacked.

Stdlib only. Deterministic: canonical EDN (sorted keys, fixed spacing) → byte-identical CID.
"""
from __future__ import annotations

import cid as cidlib

SPEC = "kotoba-actor-dna/v0"
DEFAULT_CAPABILITY = "datom:transact"
# the binding fields, in canonical (sorted) order — the manifest is exactly these keys
FIELDS = (
    ":dna/actor-did",
    ":dna/capability",
    ":dna/graph",
    ":dna/graph-cid",
    ":dna/lexicon-cid",
    ":dna/spec",
    ":dna/validation-cid",
    ":dna/wasm-cid",
)
_CID_FIELDS = (":dna/wasm-cid", ":dna/graph-cid", ":dna/validation-cid", ":dna/lexicon-cid")


class DnaError(ValueError):
    """Raised when a DNA manifest is malformed, mis-bound, or fails verification."""


def _edn_str(s: str) -> str:
    # EDN string: double-quoted, backslash + quote escaped. DIDs/CIDs/names carry neither,
    # but escape defensively so the canonical form is total.
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def manifest_edn(manifest: dict) -> bytes:
    """Canonical EDN bytes of a manifest — sorted keys, single spaces, no trailing newline.
    Deterministic: the SAME manifest always serializes to the SAME bytes → the same DNA CID."""
    missing = [k for k in FIELDS if k not in manifest]
    if missing:
        raise DnaError(f"DNA manifest missing fields {missing}")
    extra = [k for k in manifest if k not in FIELDS]
    if extra:
        raise DnaError(f"DNA manifest has unknown fields {extra} (the manifest is exactly {list(FIELDS)})")
    body = " ".join(f"{k} {_edn_str(str(manifest[k]))}" for k in FIELDS)  # FIELDS already sorted
    return ("{" + body + "}").encode("utf-8")


def dna_cid(manifest: dict) -> str:
    """The actor's canonical identity: the raw CIDv1 of the manifest's canonical EDN bytes
    (byte-identical to `ipfs add --cid-version=1 --raw-leaves`; pinnable to kotobase.net)."""
    return cidlib.cidv1_raw(manifest_edn(manifest))


def build(*, actor_did: str, wasm_cid: str, graph: str, validation_cid: str,
          lexicon_cid: str, capability: str = DEFAULT_CAPABILITY) -> dict:
    """Assemble a DNA manifest from its parts. `:dna/graph-cid` is DERIVED from `graph`
    (`graph_cid(graph)`) so the manifest ASSERTS 'this code governs THIS graph' — the binding
    is explicit and tamper-evident, not implied by a separate did.json reference."""
    if not actor_did.startswith("did:"):
        raise DnaError(f"actor-did must be a DID, got {actor_did!r}")
    for label, c in (("wasm", wasm_cid), ("validation", validation_cid), ("lexicon", lexicon_cid)):
        if not cidlib.is_cidv1(c):
            raise DnaError(f"{label}-cid is not a CIDv1: {c!r}")
    if not graph:
        raise DnaError("graph name must be non-empty")
    return {
        ":dna/spec": SPEC,
        ":dna/actor-did": actor_did,
        ":dna/wasm-cid": wasm_cid,
        ":dna/graph": graph,
        ":dna/graph-cid": cidlib.graph_cid(graph),   # DERIVED — the assertion
        ":dna/validation-cid": validation_cid,
        ":dna/lexicon-cid": lexicon_cid,
        ":dna/capability": capability,
    }


def verify(manifest: dict, *, blobs: dict | None = None) -> tuple[bool, str]:
    """Verify a DNA manifest's internal integrity (and, if `blobs` given, that referenced
    content actually hashes to its declared CID — the trustless re-verify, like a WASM loader).

    `blobs` maps a field name (e.g. ':dna/wasm-cid') → the raw bytes it should address.
    Returns (ok, reason). Pure: no I/O, deterministic."""
    try:
        if manifest.get(":dna/spec") != SPEC:
            return False, f"unknown spec {manifest.get(':dna/spec')!r} (expected {SPEC!r})"
        # the binding assertion: :dna/graph-cid MUST be graph_cid(:dna/graph) — else the
        # manifest claims a graph it does not actually address (tamper / mismatch)
        want = cidlib.graph_cid(manifest[":dna/graph"])
        if manifest[":dna/graph-cid"] != want:
            return False, (f"graph binding broken: :dna/graph-cid {manifest[':dna/graph-cid']} "
                           f"!= graph_cid({manifest[':dna/graph']!r}) {want}")
        for f in _CID_FIELDS:
            if not cidlib.is_cidv1(manifest[f]):
                return False, f"{f} is not a CIDv1: {manifest[f]!r}"
        # canonical round-trip: the manifest must serialize cleanly (exact field set)
        manifest_edn(manifest)
        if blobs:
            for field, data in blobs.items():
                if field not in _CID_FIELDS:
                    return False, f"cannot verify blob for non-CID field {field!r}"
                got = cidlib.cidv1_raw(data)
                if got != manifest[field]:
                    return False, f"{field} content mismatch: declared {manifest[field]}, bytes hash to {got}"
        return True, f"ok (dna {dna_cid(manifest)})"
    except (KeyError, DnaError) as e:
        return False, str(e)


def did_service_entry(manifest: dict) -> dict:
    """The single did.json service entry that points at this DNA — the actor's whole identity
    is now ONE CID. (Mirrors the EtzhayyimWasmComponent shape, ADR-2606014500, but addresses the
    DNA manifest, which in turn binds the wasm + graph + rules.)"""
    cid = dna_cid(manifest)
    return {
        "id": f"{manifest[':dna/actor-did']}#dna",
        "type": "EtzhayyimActorDna",
        "serviceEndpoint": f"ipfs://{cid}",
        "dnaCid": cid,
    }
