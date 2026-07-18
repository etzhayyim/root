"""Fail-closed CROSS-ACTOR referential-integrity invariants for the ooyake (公)
government-atlas procedure seed and its links into toritsugi (取次).

ooyake is the structural atlas of government units; each `:gov.procedure/*` record
(`orgs/etzhayyim/com-etzhayyim-ooyake/registry/gov-units*.edn`) is OWNED by a government unit and may
LINK to the matching citizen-facing toritsugi procedure via
`:gov.procedure/toritsugi-ref`. Those two cross-references are exactly what a
single-actor suite cannot validate — a unit-id typo orphans the procedure from the
atlas, and a toritsugi procedureId rename orphans the link. This suite pins both:

  1. Referential integrity (atlas-internal): every `:gov.procedure/owner-unit`
     resolves to an existing `:gov.unit/id`. No dangling owner.
  2. Referential integrity (cross-actor ooyake -> toritsugi): every
     `:gov.procedure/toritsugi-ref`, when present, resolves to an existing
     toritsugi `procedureId` in procedures.seed.json. No orphaned link.
  3. Honesty (G5/G14, consistent with the other actors): every procedure ships
     `:gov.procedure/verification-status :unverified-seed`.

R0-safe: test-only, deterministic, network-free — never imports/executes a cell's
runtime, never touches a live channel. (It imports only the pure `parse_edn`
helper from the reconcile cell module, the same way gen_coverage_doc.py does.)
"""

from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_RECONCILE = _REPO / "20-actors" / "ooyake" / "cells" / "reconcile"
_REGISTRY_GLOB = str(_REPO / "20-actors" / "ooyake" / "registry" / "gov-units*.edn")
_TORITSUGI_ROOT = Path(os.environ.get("ETZHAYYIM_TORITSUGI_ROOT", _REPO.parent / "com-etzhayyim-toritsugi"))
_TORITSUGI = _TORITSUGI_ROOT / "registry" / "procedures.seed.edn"

sys.path.insert(0, str(_RECONCILE))
from cell import parse_edn  # noqa: E402


def _load_atlas() -> tuple[set[str], list[dict]]:
    units: set[str] = set()
    procedures: list[dict] = []
    for f in sorted(glob.glob(_REGISTRY_GLOB)):
        doc = parse_edn(open(f, encoding="utf-8").read())
        for u in doc.get(":units", []):
            uid = u.get(":gov.unit/id")
            if uid:
                units.add(uid)
        procedures.extend(doc.get(":procedures", []))
    return units, procedures


def _toritsugi_ids() -> set[str]:
    data = parse_edn(_TORITSUGI.read_text())
    return {p["procedureId"] for p in data["procedures"]}


# ─────────────────────────────────────────────────────────────────────────
# 0. the atlas actually ships procedures (guard against silent emptying)
# ─────────────────────────────────────────────────────────────────────────


def test_atlas_has_procedures_and_units():
    units, procs = _load_atlas()
    assert units, "atlas MUST contain government units"
    assert procs, "atlas MUST contain at least one :gov.procedure record"


# ─────────────────────────────────────────────────────────────────────────
# 1. owner-unit resolves to an existing unit (atlas-internal integrity)
# ─────────────────────────────────────────────────────────────────────────


def test_every_owner_unit_resolves():
    units, procs = _load_atlas()
    dangling = [
        p.get(":gov.procedure/id")
        for p in procs
        if p.get(":gov.procedure/owner-unit") not in units
    ]
    assert not dangling, (
        f"dangling :gov.procedure/owner-unit (no matching :gov.unit/id) — "
        f"fail-closed: {dangling}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 2. toritsugi-ref resolves to an existing toritsugi procedureId (cross-actor)
# ─────────────────────────────────────────────────────────────────────────


def test_every_toritsugi_ref_resolves():
    _, procs = _load_atlas()
    tids = _toritsugi_ids()
    orphaned = [
        (p.get(":gov.procedure/id"), p.get(":gov.procedure/toritsugi-ref"))
        for p in procs
        if p.get(":gov.procedure/toritsugi-ref")
        and p.get(":gov.procedure/toritsugi-ref") not in tids
    ]
    assert not orphaned, (
        f"orphaned :gov.procedure/toritsugi-ref (no matching toritsugi "
        f"procedureId) — fail-closed: {orphaned}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 3. honesty — every procedure ships :unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_procedure_is_unverified_seed():
    _, procs = _load_atlas()
    for p in procs:
        status = p.get(":gov.procedure/verification-status")
        assert status == ":unverified-seed", (
            f"G14: {p.get(':gov.procedure/id')} MUST ship verification-status "
            f":unverified-seed; got {status!r}"
        )


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
