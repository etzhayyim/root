"""budget_ledger.py — 弾正 (danjo) budget_ledger ingest method (the coded R0 method).

Reads gov.dataset.budgetRecord-shaped records (com.etzhayyim.gov.dataset.budgetRecord) and
normalizes them into a *budget ledger*: per-record content CIDs + a per-(programCode, fiscalYear)
grouping of appropriation vs outlay lines that kanae_flow_assembler consumes downstream
(domestic-flow-chain-assembly, ADR-2605302300).

danjo is the censor's EYE, never the sword (ADR-2605301600). This method is PASSIVE and
NON-ADJUDICATING by construction:
  G3 — reads pre-published records only; it never fetches a live portal (the seed is the corpus).
  G4 — it emits FACTUAL ledger structure only; no crime/violation/guilt field exists or is computed.
  G5 — every ledger line carries its source-record CID; downstream edges need ≥2 of them.
  G13 — `stateAlignedFlag` passes through unchanged (not independently verified here).

A "CID" here is a deterministic content hash (sha256 over the canonical record) prefixed with the
gov.dataset record locator — the same string shape kanae cites in `sourceRecordCids`. It is stable
(same record → same CID) so the pipeline is reproducible and testable offline. Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def record_cid(rec: dict[str, Any]) -> str:
    """Deterministic gov.dataset record CID: locator + sha256 content digest (G5 provenance)."""
    canonical = json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    fy = rec.get("fiscalYear", "0")
    rid = rec.get("recordId", "unknown")
    sensor = rec.get("sourceSensor", "unknown")
    return f"gov.dataset.budgetRecord:{sensor}:{fy}:{rid}#{digest}"


def normalize_record(rec: dict[str, Any]) -> dict[str, Any]:
    """One ledger line from a budgetRecord. Pure; carries its own CID (G5)."""
    kind = rec.get("recordKind")
    if kind not in ("appropriation", "obligation", "outlay", "subaward"):
        raise ValueError(f"unknown recordKind {kind!r} (budgetRecord lexicon enum)")
    amount = rec.get("amountLocal")
    if not isinstance(amount, int) or amount < 0:
        raise ValueError(f"amountLocal must be a non-negative integer (minor units), got {amount!r}")
    return {
        "cid": record_cid(rec),
        "recordKind": kind,
        "jurisdiction": rec.get("jurisdiction", "jpn"),
        "programName": rec.get("programName", ""),
        "programCode": rec.get("programCode", ""),
        "amountLocal": amount,
        "currencyIso4217": rec.get("currencyIso4217", "JPY"),
        "fiscalYear": int(rec.get("fiscalYear", 0)),
        "recipientName": rec.get("recipientName", ""),
        "recipientLocalId": rec.get("recipientLocalId", ""),
        "recipientLei": rec.get("recipientLei", ""),
        "awardDateUtc": rec.get("awardDateUtc", ""),
        "sourceUrl": rec.get("sourceUrl", ""),
        "stateAlignedFlag": bool(rec.get("stateAlignedFlag", False)),
    }


def build_ledger(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Ingest budgetRecords → a budget ledger grouped by (programCode, fiscalYear).

    Returns:
      {
        "lines": [normalized line, ...],          # every record, with CID
        "groups": {                                # appropriation/outlay split per program-year
          "JP-MEXT-EDUSCI|2024": {
            "programCode", "programName", "fiscalYear", "jurisdiction",
            "appropriations": [line, ...], "outlays": [line, ...]
          }, ...
        }
      }
    """
    lines = [normalize_record(r) for r in records]
    groups: dict[str, Any] = {}
    for ln in lines:
        key = f"{ln['programCode']}|{ln['fiscalYear']}"
        g = groups.setdefault(
            key,
            {
                "programCode": ln["programCode"],
                "programName": ln["programName"],
                "fiscalYear": ln["fiscalYear"],
                "jurisdiction": ln["jurisdiction"],
                "appropriations": [],
                "outlays": [],
            },
        )
        if ln["recordKind"] == "appropriation":
            g["appropriations"].append(ln)
        elif ln["recordKind"] in ("outlay", "obligation", "subaward"):
            g["outlays"].append(ln)
    return {"lines": lines, "groups": groups}


def load_seed(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc.get("records", doc if isinstance(doc, list) else [])


if __name__ == "__main__":
    import sys

    seed = sys.argv[1] if len(sys.argv) > 1 else "20-actors/danjo/data/gov-fiscal-seed.jp.json"
    ledger = build_ledger(load_seed(seed))
    print(f"budget_ledger: {len(ledger['lines'])} lines, {len(ledger['groups'])} program-year groups")
    for key, g in ledger["groups"].items():
        print(f"  {key}: {len(g['appropriations'])} appropriation / {len(g['outlays'])} outlay")
