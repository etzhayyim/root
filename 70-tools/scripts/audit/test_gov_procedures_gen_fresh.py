"""Fail-closed FRESHNESS invariant for the compiled gov-procedures Worker registry.

`50-infra/etzhayyim-did-web/src/registry/gov-procedures.gen.ts` is AUTO-GENERATED
by `70-tools/scripts/entity-actors/gen-gov-procedures.py` from the ooyake
`:gov.procedure` records and compiled into the apex Worker (served at
`/.well-known/gov-procedures.json` + `/actor/<gov-handle>/procedures.json`). If a
maintainer edits the ooyake procedures but forgets to re-run the generator, the
PUBLISHED procedures drift from the source of truth — new procedures never appear
on etzhayyim.com, removed ones linger. This suite catches that drift WITHOUT
mutating the committed file: it recomputes the expected projection from ooyake
(the generator's own owner-unit -> handle transform) and asserts the committed
`.gen.ts` matches in both the id set and the exported counts.

Invariants:
  1. The set of procedure ids in the committed .gen.ts EXACTLY equals the set the
     generator would emit today (no missing / no ghost).
  2. GOV_PROCEDURES_TOTAL / _OWNER_COUNT / _JURISDICTION_COUNT match the source.

R0-safe: test-only, deterministic, network-free. Reads the committed TS as text
(regex), never executes it; reuses only ooyake's pure parse_edn.
"""

from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_REG = _REPO / "20-actors" / "ooyake" / "registry"
_GEN = _REPO / "50-infra" / "etzhayyim-did-web" / "src" / "registry" / "gov-procedures.gen.ts"

sys.path.insert(0, str(_REPO / "20-actors" / "ooyake" / "cells" / "reconcile"))
from cell import parse_edn  # noqa: E402


def _to_handle(unit_id: str) -> str:
    """Mirror gen-gov-procedures.py _to_handle (== gen-entity-handles toHandle)."""
    s = unit_id.lower()
    s = re.sub(r"[._\s/]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:63].rstrip("-") if len(s) > 63 else s


def _expected():
    ids, owners, juris = set(), set(), set()
    for f in sorted(glob.glob(str(_REG / "gov-units*.edn"))):
        for p in parse_edn(open(f, encoding="utf-8").read()).get(":procedures", []):
            pid = p.get(":gov.procedure/id")
            owner = p.get(":gov.procedure/owner-unit")
            if not pid or not owner:
                continue
            ids.add(pid)
            owners.add(_to_handle(owner))
            j = p.get(":gov.procedure/jurisdiction")
            if j:
                juris.add(j)
    return ids, owners, juris


def _committed():
    text = _GEN.read_text()

    def const(name: str) -> int:
        m = re.search(rf"export const {name} = (\d+);", text)
        assert m, f"{name} not found in {_GEN.name}"
        return int(m.group(1))

    ids = set(re.findall(r'"id":\s*"(proc\.[^"]+)"', text))
    return ids, const("GOV_PROCEDURES_TOTAL"), const("GOV_PROCEDURES_OWNER_COUNT"), const("GOV_PROCEDURES_JURISDICTION_COUNT")


def test_committed_gen_exists():
    assert _GEN.exists(), f"missing compiled registry: {_GEN}"


def test_procedure_id_set_is_fresh():
    # ooyake :gov.procedure/id values already begin with "proc."; the generator
    # stores them verbatim, so compare the raw id sets directly.
    exp_ids, _, _ = _expected()
    committed_ids, _, _, _ = _committed()
    missing = exp_ids - committed_ids   # ooyake added, gen not re-run
    ghost = committed_ids - exp_ids      # ooyake removed, gen stale
    assert not missing and not ghost, (
        "gov-procedures.gen.ts is STALE — re-run "
        "`python3 70-tools/scripts/entity-actors/gen-gov-procedures.py`.\n"
        f"missing (in ooyake, not published): {sorted(missing)[:10]}\n"
        f"ghost (published, not in ooyake): {sorted(ghost)[:10]}"
    )


def test_exported_counts_match_source():
    exp_ids, exp_owners, exp_juris = _expected()
    _, total, owner_count, juris_count = _committed()
    assert total == len(exp_ids), f"GOV_PROCEDURES_TOTAL {total} != source {len(exp_ids)}"
    assert owner_count == len(exp_owners), (
        f"GOV_PROCEDURES_OWNER_COUNT {owner_count} != source {len(exp_owners)}"
    )
    assert juris_count == len(exp_juris), (
        f"GOV_PROCEDURES_JURISDICTION_COUNT {juris_count} != source {len(exp_juris)}"
    )


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
