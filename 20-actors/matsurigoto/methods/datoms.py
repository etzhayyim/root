#!/usr/bin/env python3
"""matsurigoto 政 — R1.B: persist module executions to the kotoba Datom log.

ADR-2606052300. Converts a service module's output (R0 returned in-memory dicts) into
APPEND-ONLY EAVT datoms over the `egov-exec-v1` graph, and builds an offline `kg.ingest_batch`
body. State becomes canonical, as-of, replayable (ADR-2605262130 + 2605312345) — the same
membrane ake/watari/kanjo use.

Invariants enforced HERE (mirroring 00-contracts/schemas/egov-execution-ontology.kotoba.edn):
  G1 no-operator-master-key : the tx datom asserts :egov.tx/server-held-authority false, and a
                              persisted certificate's :egov.cert/proof is forced to nil — a
                              module signs nothing (ADR-2605231525).
  G3 authority-bearing      : :operated-by ∈ {:etzhayyim-council, :adopting-government};
                              :authority-mode ∈ {:sovereign-governance, :supplied-to-state}.
  G5 append-only            : every record datom carries :egov.record/immutable true.
  G8 outward-gated          : kg_ingest_batch(published=True) RAISES — live ingest is
                              Council+operator gated; R0/R1 is dry-run body construction only.

A datom is an [entity, attribute, value] triple (EAVT). stdlib only.
"""
from __future__ import annotations

ALLOWED_OPERATED_BY = {":etzhayyim-council", ":adopting-government"}
ALLOWED_AUTHORITY_MODE = {":sovereign-governance", ":supplied-to-state"}


def _tx_datoms(tx_id: str, *, service: str, module: str, operated_by: str,
               authority_mode: str, as_of: str, spec_basis: str,
               sourcing: str = ":representative", atlas_did: str | None = None) -> list:
    if operated_by not in ALLOWED_OPERATED_BY:
        raise ValueError(f"G3: :operated-by {operated_by!r} not allowed")
    if authority_mode not in ALLOWED_AUTHORITY_MODE:
        raise ValueError(f"G3: :authority-mode {authority_mode!r} not allowed")
    if not spec_basis:
        raise ValueError("G2: :spec-basis required")
    d = [
        [tx_id, ":egov.tx/id", tx_id],
        [tx_id, ":egov.tx/service", service],
        [tx_id, ":egov.tx/module", module],
        [tx_id, ":egov.tx/operated-by", operated_by],
        [tx_id, ":egov.tx/authority-mode", authority_mode],
        [tx_id, ":egov.tx/as-of", as_of],
        [tx_id, ":egov.tx/spec-basis", spec_basis],
        [tx_id, ":egov.tx/sourcing", sourcing],
        [tx_id, ":egov.tx/server-held-authority", False],  # G1
    ]
    if atlas_did:
        d.append([tx_id, ":egov.tx/atlas-did", atlas_did])
    return d


def _assert_unsigned(artifact: dict) -> None:
    """G1: a module-produced artifact must be unsigned (proof None, no server-held authority)."""
    if artifact.get("proof") is not None:
        raise ValueError("G1: a module artifact must be unsigned (proof must be None)")
    if artifact.get("server_held_authority") is not False:
        raise ValueError("G1: server_held_authority must be False")


def _cert_datoms(tx_id: str, artifact: dict) -> list:
    _assert_unsigned(artifact)
    cert_e = f"{tx_id}#cert"
    return [
        [cert_e, ":egov.cert/of-tx", tx_id],
        [cert_e, ":egov.cert/kind", artifact.get("kind") or artifact.get("type", ["", "?"])[-1]],
        [cert_e, ":egov.cert/status", artifact["status"]],
        [cert_e, ":egov.cert/proof", None],  # G1 — nil until the governing organ signs externally
    ]


# ── per-module converters (take the module's R0 output dict) ──
def assessment_datoms(out: dict, *, tx_id: str, **tx) -> list:
    """tax-assess output → datoms."""
    d = _tx_datoms(tx_id, module="tax-assess", **tx)
    d += [
        [tx_id, ":egov.assessment/of-tx", tx_id],
        [tx_id, ":egov.assessment/liability", out["liability"]],
        [tx_id, ":egov.assessment/effective-rate", out["effective_rate"]],
        [tx_id, ":egov.assessment/currency", out.get("currency", "XXX")],
    ]
    if "receipt" in out:
        d += _cert_datoms(tx_id, out["receipt"])
    return d


def civil_datoms(out: dict, *, tx_id: str, **tx) -> list:
    """civil-registry registration → datoms (append-only)."""
    rec = out["record"]
    d = _tx_datoms(tx_id, module="civil-registry", **tx)
    rid = rec["record_id"]
    d += [
        [rid, ":egov.record/id", rid],
        [rid, ":egov.record/of-tx", tx_id],
        [rid, ":egov.record/kind", rec["vital_kind"]],
        [rid, ":egov.record/immutable", True],  # G5
    ]
    d += _cert_datoms(tx_id, out["certificate"])
    return d


def incorporation_datoms(out: dict, *, tx_id: str, **tx) -> list:
    """corp-registry incorporation → datoms."""
    rec = out["record"]
    d = _tx_datoms(tx_id, module="corp-registry", **tx)
    rid = rec["record_id"]
    d += [
        [rid, ":egov.record/id", rid],
        [rid, ":egov.record/of-tx", tx_id],
        [rid, ":egov.record/kind", "incorporation"],
        [rid, ":egov.record/immutable", True],  # G5
        [rid, ":egov.record/lei", rec["lei"]],
    ]
    d += _cert_datoms(tx_id, out["certificate"])
    return d


def passport_datoms(out: dict, *, tx_id: str, **tx) -> list:
    """credential-issue passport → datoms (MRZ kept off the log; only the issuance record)."""
    d = _tx_datoms(tx_id, module="credential-issue", **tx)
    rid = f"{tx_id}#mrtd"
    d += [
        [rid, ":egov.record/id", rid],
        [rid, ":egov.record/of-tx", tx_id],
        [rid, ":egov.record/kind", "passport"],
        [rid, ":egov.record/immutable", True],  # G5
    ]
    d += _cert_datoms(tx_id, out["document"])
    return d


def kg_ingest_batch(datoms: list, *, graph: str = "egov-exec-v1", published: bool = False) -> dict:
    """Build a `kg.ingest_batch` body. G8: published=True RAISES — live ingest is Council+operator
    gated. R1 constructs the dry-run body only."""
    if published:
        raise RuntimeError(
            "G8: live kotoba ingest is Council+operator gated (principal A: Council Lv7+; "
            "principal B: adopting state). Construct the body and hand off; do not publish here."
        )
    return {
        "op": "kg.ingest_batch",
        "graph": graph,
        "published": False,
        "datoms": list(datoms),
        "count": len(datoms),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent / "modules"))
    import tax_assess as T
    out = T.assess_from_return(6_000_000, 1_000_000, "JPN.income")
    ds = assessment_datoms(out, tx_id="tx-demo", service="tax.income.file",
                           operated_by=":etzhayyim-council", authority_mode=":sovereign-governance",
                           as_of="2026-06-06T00:00:00Z", spec_basis="JP 速算表")
    body = kg_ingest_batch(ds)
    print(f"{body['count']} datoms, published={body['published']}")
