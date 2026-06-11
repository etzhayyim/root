#!/usr/bin/env python3
"""integrity.py — the actor's integrity ruleset: code-defined validation of DATA before commit.

This is the kotoba analogue of a Holochain INTEGRITY ZOME. Today the kotoba engine is
append-only with CACAO auth (who may write), but nothing validates WHAT is written — data
integrity is an operational gate (G7/Council), not structural. This module makes integrity a
**content-addressed ruleset** that an actor enforces at its transact boundary: the DNA manifest
references the ruleset by CID (`:dna/validation-cid`), so the rules are tamper-evident (edit a
rule → new CID → new DNA → a different actor), and `validate()` REJECTS non-conforming datoms
before they are pushed.

Honest scope (ADR-2606112000): this enforces at the ACTOR/CLIENT tier (the only tier this repo
owns — the engine is the `40-engine/kotoba` submodule). Engine-tier enforcement (the kotoba
transact path invoking the DNA's `validate` before commit, so a peer's writes are checked too) is
the gated follow-up. The content-addressed ruleset is the half that makes that follow-up trustless.

A ruleset (canonical EDN, itself content-addressed):

    {:integrity/spec "kotoba-integrity/v0"
     :integrity/graph "ibuki"                 ; datoms may target ONLY this graph
     :integrity/append-only true              ; only :db/add — no retraction (非終末論)
     :integrity/closed-attrs [":joucho/mood" ":heartbeat/beat" …]   ; only these attrs allowed
     :integrity/required-attrs {":organism" [":organism/niche"]}    ; an entity tag → must-haves
     :integrity/attr-types {":joucho/mood" :keyword ":heartbeat/beat" :int …}
     :integrity/deny-attrs [":published"]}    ; structurally forbidden (e.g. ibuki never asserts :published)

Stdlib only. Deterministic.
"""
from __future__ import annotations

import cid as cidlib

SPEC = "kotoba-integrity/v0"
RULE_KEYS = (
    ":integrity/spec",
    ":integrity/graph",
    ":integrity/append-only",
    ":integrity/closed-attrs",
    ":integrity/required-attrs",
    ":integrity/attr-types",
    ":integrity/deny-attrs",
)
_VALUE_TYPES = ("keyword", "string", "int", "float", "bool", "cid", "did")


class IntegrityError(ValueError):
    """Raised when a ruleset itself is malformed."""


def _edn(v) -> str:
    """Canonical EDN for the small value space a ruleset uses (str/bool/int/keyword/list/dict)."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        # a keyword (leading ':') stays bare; otherwise a quoted string
        if v.startswith(":"):
            return v
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, (list, tuple)):
        return "[" + " ".join(_edn(x) for x in v) + "]"
    if isinstance(v, dict):
        items = sorted(v.items(), key=lambda kv: str(kv[0]))
        return "{" + " ".join(f"{_edn(k)} {_edn(val)}" for k, val in items) + "}"
    raise IntegrityError(f"non-canonical value in ruleset: {v!r}")


def rules_edn(rules: dict) -> bytes:
    """Canonical EDN bytes of a ruleset — the content that `validation_cid` addresses."""
    if rules.get(":integrity/spec") != SPEC:
        raise IntegrityError(f"ruleset spec must be {SPEC!r}, got {rules.get(':integrity/spec')!r}")
    extra = [k for k in rules if k not in RULE_KEYS]
    if extra:
        raise IntegrityError(f"ruleset has unknown keys {extra}")
    keys = [k for k in RULE_KEYS if k in rules]
    return ("{" + " ".join(f"{k} {_edn(rules[k])}" for k in keys) + "}").encode("utf-8")


def validation_cid(rules: dict) -> str:
    """The raw CIDv1 of the canonical ruleset — what the DNA's `:dna/validation-cid` pins."""
    return cidlib.cidv1_raw(rules_edn(rules))


def _typed_ok(value, typ: str) -> bool:
    if typ == "keyword":
        return isinstance(value, str) and value.startswith(":")
    if typ == "string":
        return isinstance(value, str) and not value.startswith(":")
    if typ == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if typ == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if typ == "bool":
        return isinstance(value, bool)
    if typ == "cid":
        return cidlib.is_cidv1(value)
    if typ == "did":
        return isinstance(value, str) and value.startswith("did:")
    raise IntegrityError(f"unknown value type {typ!r} (allowed: {list(_VALUE_TYPES)})")


def validate(datoms, rules: dict, *, graph: str | None = None) -> tuple[bool, list[str]]:
    """Check every datom against the ruleset. Returns (ok, violations). A datom is a tuple
    `(op, e, a, v)` (op like ':db/add'). REJECTS rather than guesses — the integrity-zome stance.

    `graph` (the graph the push targets) is checked against `:integrity/graph` when both present —
    the data may only land in the graph the DNA binds."""
    if rules.get(":integrity/spec") != SPEC:
        return False, [f"ruleset spec must be {SPEC!r}"]
    v: list[str] = []
    bound_graph = rules.get(":integrity/graph")
    if bound_graph and graph is not None and graph != bound_graph:
        v.append(f"graph {graph!r} != ruleset-bound graph {bound_graph!r}")

    append_only = rules.get(":integrity/append-only", False)
    closed = set(rules.get(":integrity/closed-attrs") or [])
    denied = set(rules.get(":integrity/deny-attrs") or [])
    types = rules.get(":integrity/attr-types") or {}
    required = rules.get(":integrity/required-attrs") or {}

    seen_attrs_by_entity: dict = {}
    for i, d in enumerate(datoms):
        if not isinstance(d, (list, tuple)) or len(d) != 4:
            v.append(f"datom {i}: not a 4-tuple (op e a v): {d!r}")
            continue
        op, e, a, val = d
        if append_only and op != ":db/add":
            v.append(f"datom {i}: op {op!r} violates :integrity/append-only (only :db/add)")
        if a in denied:
            v.append(f"datom {i}: attribute {a!r} is structurally forbidden (:integrity/deny-attrs)")
        if closed and a not in closed:
            v.append(f"datom {i}: attribute {a!r} not in :integrity/closed-attrs (closed vocabulary)")
        if a in types and not _typed_ok(val, types[a]):
            v.append(f"datom {i}: value {val!r} for {a!r} is not a {types[a]}")
        seen_attrs_by_entity.setdefault(e, set()).add(a)

    # required-attrs: keyed by an entity-tag PREFIX of the attribute namespace (e.g. ':organism'
    # requires that any entity asserting a ':organism/*' attr also carries the listed attrs).
    for tag, must in required.items():
        ns = tag[1:] if tag.startswith(":") else tag
        for e, attrs in seen_attrs_by_entity.items():
            if any(a.startswith(f":{ns}/") or a.startswith(f":{ns}.") for a in attrs):
                for need in must:
                    if need not in attrs:
                        v.append(f"entity {e!r} asserts {tag} but is missing required {need!r}")
    return (not v), v
