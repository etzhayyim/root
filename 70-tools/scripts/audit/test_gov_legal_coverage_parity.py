"""Fail-closed CROSS-ACTOR coverage invariants for the worldwide
government-procedure (toritsugi 取次) and legal-aid (chigiri 契) seed registries.

This suite pins the *relationship between* the two actors that together answer the
two halves of the founding question — worldwide ADMINISTRATIVE-procedure coverage
(toritsugi) and worldwide LEGAL-procedure / legal-aid coverage (chigiri). The
per-actor suites (test_toritsugi_registry_seed.py / test_chigiri_registry_seed.py)
pin each registry's internal invariants; THIS suite pins the cross-registry
invariants neither can see alone:

  1. Both registries use only well-formed jurisdiction codes — ISO-3166-1
     alpha-3 lowercase, or the documented `eu-wide` pseudo-jurisdiction for
     EU-wide procedures (Single Digital Gateway / EHIC / GDPR DSAR). Catches
     typos like "uk"/"usa2"/"UK" that would silently fragment coverage.
  2. Coverage floor (regression guard): each registry spans >= 47 distinct
     jurisdictions — the parity level reached 2026-06-05. A removal that drops
     coverage below this floor fails fast.
  3. Parity floor (regression guard): the two actors SHARE >= 45 jurisdictions.
     Intersection only shrinks when a jurisdiction is *removed* from one actor,
     so this guards the achieved alignment WITHOUT being brittle to future
     single-actor growth (adding a new jurisdiction to one side never lowers the
     intersection).

R0-safe: test-only, deterministic, network-free — never imports/executes a cell,
never touches a live channel.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_TORITSUGI_ROOT = Path(os.environ.get("ETZHAYYIM_TORITSUGI_ROOT", _REPO.parent / "com-etzhayyim-toritsugi"))
_CHIGIRI_ROOT = Path(os.environ.get("ETZHAYYIM_CHIGIRI_ROOT", _REPO.parent / "com-etzhayyim-chigiri"))
_TORITSUGI = _TORITSUGI_ROOT / "registry" / "procedures.seed.edn"
_CHIGIRI = _CHIGIRI_ROOT / "registry" / "legal-aid.seed.edn"
sys.path.insert(0, str(_REPO / "20-actors" / "ooyake" / "cells" / "reconcile"))
from cell import parse_edn  # noqa: E402

# ISO-3166-1 alpha-3, lowercase.
_ISO3_RE = re.compile(r"^[a-z]{3}$")
# Documented non-ISO pseudo-jurisdictions (intentional, not typos).
_ALLOWED_NON_ISO = {"eu-wide"}

# Coverage / parity floors — the levels reached 2026-06-05. These are regression
# guards (">="), so coverage may grow freely; only a SHRINK below them fails.
_COVERAGE_FLOOR = 47
_PARITY_FLOOR = 45


def _jurisdictions(path: Path, list_key: str) -> set[str]:
    data = parse_edn(path.read_text())
    rows = data[list_key]
    return {(r.get("jurisdiction") or "").strip() for r in rows}


def _toritsugi() -> set[str]:
    return _jurisdictions(_TORITSUGI, "procedures")


def _chigiri() -> set[str]:
    return _jurisdictions(_CHIGIRI, "referrals")


# ─────────────────────────────────────────────────────────────────────────
# 1. jurisdiction codes are well-formed (ISO-3 or documented pseudo)
# ─────────────────────────────────────────────────────────────────────────


def test_jurisdiction_codes_well_formed():
    for label, juris in (("toritsugi", _toritsugi()), ("chigiri", _chigiri())):
        for code in juris:
            assert code, f"{label}: empty jurisdiction code is not allowed"
            ok = bool(_ISO3_RE.match(code)) or code in _ALLOWED_NON_ISO
            assert ok, (
                f"{label}: jurisdiction {code!r} is neither ISO-3166-1 alpha-3 "
                f"(lowercase 3 letters) nor a documented pseudo-jurisdiction "
                f"({sorted(_ALLOWED_NON_ISO)}) — likely a typo that fragments coverage"
            )


# ─────────────────────────────────────────────────────────────────────────
# 2. coverage floor — each registry spans >= _COVERAGE_FLOOR jurisdictions
# ─────────────────────────────────────────────────────────────────────────


def test_each_registry_meets_coverage_floor():
    for label, juris in (("toritsugi", _toritsugi()), ("chigiri", _chigiri())):
        assert len(juris) >= _COVERAGE_FLOOR, (
            f"{label}: coverage regressed — spans {len(juris)} distinct "
            f"jurisdictions, floor is {_COVERAGE_FLOOR} (reached 2026-06-05). "
            f"got {sorted(juris)}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 3. parity floor — the two actors share >= _PARITY_FLOOR jurisdictions
# ─────────────────────────────────────────────────────────────────────────


def test_cross_actor_parity_floor():
    t, c = _toritsugi(), _chigiri()
    shared = t & c
    assert len(shared) >= _PARITY_FLOOR, (
        f"cross-actor parity regressed — toritsugi (admin procedures) and "
        f"chigiri (legal aid) share only {len(shared)} jurisdictions; floor is "
        f"{_PARITY_FLOOR}. toritsugi-only={sorted(t - c)} chigiri-only={sorted(c - t)}"
    )


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
