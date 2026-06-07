"""ingest.py — 潮目 (shionome) offline public-source normalizer. ADR-2606072200.

Normalizes batches of public market-data records (exchange data / fund-flow reports /
central-bank releases / index providers) into shionome :bucket/:flow/:snap datoms. OFFLINE by
default and REFUSES `--live` without the G8 gate (operator attestation + SHIONOME_ALLOW_LIVE=1)
— the keizu/yadori/watari pattern.

Every normalized record is run through the same weave.validate_* gates, so an under-sourced, a
NaN-magnitude, or a TRADE/advisory-bearing input is refused here (トレードはしない), not silently
ingested.

Stdlib only.
"""

from __future__ import annotations

import os
from typing import Any

from registry import sourcing_for
from weave import validate_bucket, validate_flow, validate_snapshot

# raw bucket fields that map to canonical :bucket/* attrs; anything else is carried through as
# :bucket/<field> so the validate_bucket PII / rating scan (G1/G2/G4/G9) bites on the ingest path.
_KNOWN_BUCKET_FIELDS = ("id", "scope", "label", "asset_class", "region", "risk",
                        "sources", "sourcing", "sourceId")


def _sourcing(raw: dict) -> str:
    """G11 — if the record names a registry sourceId, the REGISTRY'S verification status WINS
    (a caller cannot forge :authoritative for an unverified source). Else honor the caller's
    declared sourcing, defaulting to :representative."""
    if raw.get("sourceId"):
        return sourcing_for(raw["sourceId"])
    return ":" + str(raw.get("sourcing", "representative")).lstrip(":")


def normalize_bucket(raw: dict) -> dict:
    """Normalize a capital-bucket record → validated :bucket/* datom (raises on G1/G2/G4/G9).
    Extra raw fields are carried through so a smuggled PII / rating field is caught."""
    b = {
        ":bucket/id": raw["id"],
        ":bucket/scope": ":" + str(raw.get("scope", "")).lstrip(":"),
        ":bucket/sourcing": _sourcing(raw),
    }
    for k in ("label", "asset_class", "region"):
        if raw.get(k):
            b[":bucket/" + k.replace("_", "-")] = raw[k]
    if raw.get("risk"):
        b[":bucket/risk"] = ":" + str(raw["risk"]).lstrip(":")
    if raw.get("sources"):
        b[":bucket/sources"] = [s for s in raw["sources"] if str(s).strip()]
    for k, v in raw.items():
        if k not in _KNOWN_BUCKET_FIELDS:
            b[":bucket/" + k] = v   # surfaces PII / rating / signal / target keys to validate_bucket
    validate_bucket(b)
    return b


def normalize_flow(raw: dict) -> dict:
    """Normalize a capital-flow record → validated :flow/* datom (raises on a gate)."""
    f = {
        ":flow/id": raw["id"],
        ":flow/source": raw.get("source", "external"),
        ":flow/target": raw.get("target", "external"),
        ":flow/kind": ":" + str(raw["kind"]).lstrip(":"),
        ":flow/magnitude": float(raw.get("magnitude", 0.0)),
        ":flow/unit": raw.get("unit", ""),
        ":flow/no-trade-notice": True,
        ":flow/as-of": int(raw.get("as_of", 0)),
        ":flow/sourcing": _sourcing(raw),
        ":flow/sources": [s for s in raw.get("sources", []) if str(s).strip()],
    }
    validate_flow(f)
    return f


def normalize_snapshot(raw: dict) -> dict:
    """Normalize an observed bucket metric → validated :snap/* datom (raises on a gate)."""
    s = {
        ":snap/id": raw["id"],
        ":snap/bucket": raw["bucket"],
        ":snap/metric": ":" + str(raw["metric"]).lstrip(":"),
        ":snap/value": float(raw.get("value", 0.0)),
        ":snap/as-of": int(raw.get("as_of", 0)),
        ":snap/sourcing": _sourcing(raw),
        ":snap/sources": [s for s in raw.get("sources", []) if str(s).strip()],
    }
    validate_snapshot(s)
    return s


def normalize_batch(batch: dict) -> dict:
    """Normalize a mixed offline batch into shionome datoms. Each record validated."""
    out: dict[str, list] = {"buckets": [], "flows": [], "snapshots": []}
    for b in batch.get("buckets", []):
        out["buckets"].append(normalize_bucket(b))
    for f in batch.get("flows", []):
        out["flows"].append(normalize_flow(f))
    for s in batch.get("snapshots", []):
        out["snapshots"].append(normalize_snapshot(s))
    return out


def ingest_live(*_args, **_kwargs):
    """G8 — live ingest from market-data sources is outward-gated. Refuses unless the operator
    gate is set AND an attestation DID is supplied (which still routes to Council Lv6+)."""
    if os.environ.get("SHIONOME_ALLOW_LIVE") != "1":
        raise RuntimeError(
            "shionome R0: live market-data ingest is Council Lv6+ + operator gated (G8). "
            "Set SHIONOME_ALLOW_LIVE=1 + supply an operator attestation DID to proceed (still Council-gated)."
        )
    raise RuntimeError("shionome R0: live ingest path not wired — design-only (G8).")


if __name__ == "__main__":
    import sys

    if "--live" in sys.argv:
        ingest_live()
    else:
        sample = {
            "buckets": [{"id": "demo-eq", "scope": "asset-class", "label": "demo equities",
                         "asset_class": "equities", "region": "us", "risk": "risk",
                         "sources": ["https://www.sec.gov/"]}],
            "flows": [{"id": "demo-flow", "source": "external", "target": "demo-eq",
                       "kind": "fund-inflow", "magnitude": 1.5, "unit": "usd-bn", "as_of": 20260601,
                       "sources": ["https://www.ici.org/research", "https://fred.stlouisfed.org/"]}],
            "snapshots": [{"id": "demo-snap", "bucket": "demo-eq", "metric": "return-pct",
                           "value": 1.2, "as_of": 20260601, "sources": ["https://fred.stlouisfed.org/"]}],
        }
        out = normalize_batch(sample)
        print(f"# shionome offline normalize — buckets={len(out['buckets'])} "
              f"flows={len(out['flows'])} snapshots={len(out['snapshots'])} (all validated)")
