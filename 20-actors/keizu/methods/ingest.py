"""ingest.py — 系図 (keizu) offline public-source normalizer. ADR-2606066000.

Normalizes batches of public-source records (官報 / 政治資金収支報告書 / 調達ポータル /
Federal Register / USAspending / TED / OECD rosters) into keizu :node/:rel/:money/:committee
datoms. OFFLINE by default and REFUSES `--live` without the G8 gate (operator attestation +
KEIZU_ALLOW_LIVE=1) — the yadori/watari pattern.

Every normalized record is run through the same weave.validate_* gates, so an under-sourced or
verdict-bearing input is refused here, not silently ingested.

Stdlib only.
"""

from __future__ import annotations

import os
from typing import Any

from registry import sourcing_for
from weave import validate_money, validate_node, validate_rel, _kw

# raw node fields that map to canonical :node/* attrs; anything else is carried through as
# :node/<field> so the validate_node PII / power-score scan (G1/G4/G9) bites on the ingest path.
_KNOWN_NODE_FIELDS = ("id", "scope", "label", "jurisdiction", "organ", "sources", "sourcing",
                      "sourceId")


def _sourcing(raw: dict) -> str:
    """G11 — if the record names a registry sourceId, the REGISTRY'S verification status WINS
    (a caller cannot forge :authoritative for an unverified source). Else honor the caller's
    declared sourcing, defaulting to :representative."""
    if raw.get("sourceId"):
        return sourcing_for(raw["sourceId"])
    return ":" + str(raw.get("sourcing", "representative")).lstrip(":")


def normalize_node(raw: dict) -> dict:
    """Normalize a public-seat record → validated :node/* datom (raises on G1/G4/G9). Extra raw
    fields are carried through so a smuggled PII / power-score field is caught, not silently dropped."""
    node = {
        ":node/id": raw["id"],
        ":node/scope": ":" + str(raw.get("scope", "")).lstrip(":"),
        ":node/sourcing": _sourcing(raw),
    }
    for k in ("label", "jurisdiction", "organ"):
        if raw.get(k):
            node[":node/" + k] = raw[k]
    if raw.get("sources"):
        node[":node/sources"] = [s for s in raw["sources"] if str(s).strip()]
    for k, v in raw.items():
        if k not in _KNOWN_NODE_FIELDS:
            node[":node/" + k] = v   # surfaces PII/power-score keys to validate_node
    validate_node(node)
    return node


def normalize_committee(raw: dict) -> dict:
    """Normalize a public committee roster record → :committee/* datom (seats as node ids)."""
    members = [str(m) for m in raw.get("members", [])]
    if not members:
        raise ValueError("G1: a committee composition needs ≥1 public seat")
    sources = [s for s in raw.get("sources", []) if str(s).strip()]
    if not sources:
        raise ValueError("G3: a committee roster needs ≥1 public source")
    return {
        ":committee/id": raw["id"],
        ":committee/label": raw.get("label", raw["id"]),
        ":committee/jurisdiction": raw.get("jurisdiction", ""),
        ":committee/organ": raw.get("organ", ""),
        ":committee/members": members,
        ":committee/term-from": int(raw.get("term_from", 0)),
        ":committee/sourcing": _sourcing(raw),
        ":committee/sources": sources,
    }


def normalize_rel(raw: dict) -> dict:
    """Normalize a tie record → validated :rel/* datom (raises on a gate)."""
    rel = {
        ":rel/id": raw["id"],
        ":rel/source": raw["source"],
        ":rel/target": raw["target"],
        ":rel/kind": ":" + str(raw["kind"]).lstrip(":"),
        ":rel/weight": float(raw.get("weight", 1.0)),
        ":rel/as-of": int(raw.get("as_of", 0)),
        ":rel/non-adjudicating-notice": True,
        ":rel/sourcing": _sourcing(raw),
        ":rel/sources": [s for s in raw.get("sources", []) if str(s).strip()],
    }
    validate_rel(rel)
    return rel


def normalize_money(raw: dict) -> dict:
    """Normalize a money-flow record → validated :money/* datom (raises on a gate)."""
    m = {
        ":money/id": raw["id"],
        ":money/payer": raw["payer"],
        ":money/payee": raw["payee"],
        ":money/kind": ":" + str(raw["kind"]).lstrip(":"),
        ":money/amount": float(raw.get("amount", 0.0)),
        ":money/currency": raw.get("currency", ""),
        ":money/as-of": int(raw.get("as_of", 0)),
        ":money/sourcing": _sourcing(raw),
        ":money/sources": [s for s in raw.get("sources", []) if str(s).strip()],
    }
    validate_money(m)
    return m


def normalize_batch(batch: dict) -> dict:
    """Normalize a mixed offline batch into keizu datoms. Each record validated."""
    out: dict[str, list] = {"nodes": [], "committees": [], "rels": [], "money": []}
    for n in batch.get("nodes", []):
        out["nodes"].append(normalize_node(n))
    for c in batch.get("committees", []):
        out["committees"].append(normalize_committee(c))
    for r in batch.get("rels", []):
        out["rels"].append(normalize_rel(r))
    for m in batch.get("money", []):
        out["money"].append(normalize_money(m))
    return out


def ingest_live(*_args, **_kwargs):
    """G8 — live ingest from government portals is outward-gated. Refuses unless the operator
    gate is set AND an attestation DID is supplied (which still routes to Council Lv6+)."""
    if os.environ.get("KEIZU_ALLOW_LIVE") != "1":
        raise RuntimeError(
            "keizu R0: live public-source ingest is Council Lv6+ + operator gated (G8). "
            "Set KEIZU_ALLOW_LIVE=1 + supply an operator attestation DID to proceed (still Council-gated)."
        )
    raise RuntimeError("keizu R0: live ingest path not wired — design-only (G8).")


if __name__ == "__main__":
    import sys

    if "--live" in sys.argv:
        ingest_live()
    else:
        sample = {
            "committees": [{"id": "demo-committee", "label": "demo", "jurisdiction": "jp",
                            "organ": "demo-ministry", "members": ["seat-1", "seat-2"],
                            "term_from": 20250101, "sources": ["https://example.gov/"]}],
            "rels": [{"id": "demo-rel", "source": "seat-1", "target": "demo-committee",
                      "kind": "committee-membership", "as_of": 20250101,
                      "sources": ["https://example.gov/a", "https://example.gov/b"]}],
            "money": [{"id": "demo-money", "payer": "demo-ministry", "payee": "seat-1",
                       "kind": "procurement-award", "amount": 1.0e6, "currency": "JPY",
                       "as_of": 20250101, "sources": ["https://example.gov/x", "https://example.gov/y"]}],
        }
        out = normalize_batch(sample)
        print(f"# keizu offline normalize — committees={len(out['committees'])} "
              f"rels={len(out['rels'])} money={len(out['money'])} (all validated)")
