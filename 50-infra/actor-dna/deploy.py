#!/usr/bin/env python3
"""deploy.py — the atomic deploy descriptor: one content-addressed plan, keyed by the DNA CID.

Today an actor deploy is several un-coordinated operations (pin the WASM, ingest the actor
profile, pin did.json) at separate times — there is no single artifact that says "deploy THIS
actor". This module emits a deterministic, content-addressed deploy DESCRIPTOR whose every step
references the one `dna_cid` (dna.py). That gives **atomicity of identity**: even though the
engine executes the steps in sequence (true single-tx atomicity is the engine-tier follow-up,
ADR-2606112000), every step binds to one DNA hash, so a partially-applied or tampered deploy is
detectable — the deploy either reproduces the DNA CID end-to-end or it does not.

Order matters: the content (code, rules, lexicon) is pinned BEFORE the manifest that references
it, the manifest is pinned BEFORE the graph genesis that adopts it, and the did.json link comes
last — so at no point does a published identity reference unpinned content. Execution chains via
`expected_parent` (the kotoba optimistic-concurrency primitive ibuki's bridge already uses), so a
fork fails loudly rather than overwriting.

Stdlib only. Deterministic: the same DNA → the same descriptor bytes → the same deploy CID.
"""
from __future__ import annotations

import cid as cidlib
import dna as dnalib

SPEC = "kotoba-actor-deploy/v0"


class DeployError(ValueError):
    pass


def plan(manifest: dict) -> list[dict]:
    """The ordered deploy steps. Each is a pure descriptor (no I/O); an executor (operator tool /
    ibuki kotoba_bridge) performs it. Every step carries `dna` = the binding identity."""
    ok, why = dnalib.verify(manifest)
    if not ok:
        raise DeployError(f"refusing to plan an unverified DNA: {why}")
    d = dnalib.dna_cid(manifest)
    g = manifest[":dna/graph"]
    return [
        {"step": 1, "op": "pin", "what": "code", "cid": manifest[":dna/wasm-cid"], "dna": d,
         "target": "kotobase.net"},
        {"step": 2, "op": "pin", "what": "validation", "cid": manifest[":dna/validation-cid"], "dna": d,
         "target": "kotobase.net"},
        {"step": 3, "op": "pin", "what": "lexicon", "cid": manifest[":dna/lexicon-cid"], "dna": d,
         "target": "kotobase.net"},
        {"step": 4, "op": "pin", "what": "dna-manifest", "cid": d, "dna": d, "target": "kotobase.net"},
        {"step": 5, "op": "graph-genesis", "what": "data", "graph": g,
         "cid": manifest[":dna/graph-cid"], "dna": d},
        {"step": 6, "op": "did-link", "what": "identity", "service": dnalib.did_service_entry(manifest),
         "dna": d},
    ]


def _edn(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return v if v.startswith(":") else '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, (list, tuple)):
        return "[" + " ".join(_edn(x) for x in v) + "]"
    if isinstance(v, dict):
        items = sorted(v.items(), key=lambda kv: str(kv[0]))
        return "{" + " ".join(f"{_edn(k)} {_edn(val)}" for k, val in items) + "}"
    raise DeployError(f"non-canonical value in descriptor: {v!r}")


def descriptor(manifest: dict) -> dict:
    """The full deploy descriptor object: the DNA CID + the ordered step CIDs. Content-addressed
    by `deploy_cid` — a single hash that fixes EXACTLY what gets deployed."""
    d = dnalib.dna_cid(manifest)
    steps = plan(manifest)
    return {
        ":deploy/spec": SPEC,
        ":deploy/dna-cid": d,
        ":deploy/actor-did": manifest[":dna/actor-did"],
        ":deploy/graph": manifest[":dna/graph"],
        ":deploy/pins": [s["cid"] for s in steps if s["op"] == "pin"],
        ":deploy/step-count": len(steps),
    }


def descriptor_edn(desc: dict) -> bytes:
    keys = sorted(desc.keys())
    return ("{" + " ".join(f"{k} {_edn(desc[k])}" for k in keys) + "}").encode("utf-8")


def deploy_cid(manifest: dict) -> str:
    """The content-address of the deploy descriptor — one hash that fixes the whole deploy."""
    return cidlib.cidv1_raw(descriptor_edn(descriptor(manifest)))


def verify_descriptor(desc: dict, manifest: dict) -> tuple[bool, str]:
    """A descriptor is valid iff it names the manifest's true DNA CID and pins exactly the
    manifest's content (code + validation + lexicon + the manifest itself)."""
    if desc.get(":deploy/spec") != SPEC:
        return False, f"unknown deploy spec {desc.get(':deploy/spec')!r}"
    d = dnalib.dna_cid(manifest)
    if desc.get(":deploy/dna-cid") != d:
        return False, f"deploy dna-cid {desc.get(':deploy/dna-cid')} != manifest dna {d}"
    want_pins = {manifest[":dna/wasm-cid"], manifest[":dna/validation-cid"],
                 manifest[":dna/lexicon-cid"], d}
    if set(desc.get(":deploy/pins") or []) != want_pins:
        return False, "deploy pins do not match the manifest's content set"
    return True, f"ok (deploy {deploy_cid(manifest)})"
