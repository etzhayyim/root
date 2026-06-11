"""Governance / honest-framing tests for noroshi (烽) — ADR-2606051600 (item 4).

Locks the charter-substrate boundary and the honesty of the framing so a future edit can't quietly:
  • drop a gate/non-goal from the actor CLAUDE.md (doc drift),
  • import a forbidden substrate (RisingWave/SQL) or commercial-inference SDK (G6/G9),
  • or strip the honest R0/R1 disclaimers from a report (G8/G10 — no silicon, outward-gated).
"""

from __future__ import annotations

import importlib
import pathlib

import pytest

from _edn import load_edn

_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _manifest() -> dict:
    return load_edn(_ROOT / "manifest.edn")


# ── doc consistency: every gate/non-goal is documented ───────────────────────
def test_every_gate_appears_in_actor_claude_md():
    claude = (_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    missing = [g[":gate/id"] for g in _manifest()[":actor/gates"] if g[":gate/id"] not in claude]
    assert not missing, f"gates missing from CLAUDE.md: {missing}"


def test_every_non_goal_appears_in_actor_claude_md():
    claude = (_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    missing = [n[":ng/id"] for n in _manifest()[":actor/non-goals"] if n[":ng/id"] not in claude]
    assert not missing, f"non-goals missing from CLAUDE.md: {missing}"


# ── substrate boundary: stdlib + Murakumo-only (no SQL store, no commercial SDK) ──
_FORBIDDEN_IMPORTS = (
    "risingwave", "psycopg", "kysely", "sqlalchemy",
    "import openai", "from openai", "runpod", "boto3", "vertexai",
    "import anthropic", "from anthropic",
)


# Scan implementation files only — test files legitimately *name* the forbidden tokens.
_IMPL_PY = sorted(p for p in _ROOT.glob("**/*.py") if not p.name.startswith("test_"))


@pytest.mark.parametrize("py", _IMPL_PY, ids=lambda p: p.name)
def test_no_forbidden_substrate_or_inference_import(py):
    text = py.read_text(encoding="utf-8").lower()
    hits = [tok for tok in _FORBIDDEN_IMPORTS if tok in text]
    assert not hits, f"{py.name} references forbidden substrate/inference: {hits} (G6/G9)"


# ── honest framing: each report() carries an R0/R1 honesty marker ────────────
_HONEST_MARKERS = ("r0", "g7", "g8", ":representative", "honest", "no live", "no robot",
                   "no foundry", "unpopulated", "gated", "simulation only")


@pytest.mark.parametrize("mod", ["link_budget", "isac_sim", "active_alignment",
                                 "cable_endpoint", "kami_isac_bridge", "pic_layout"])
def test_report_carries_honest_framing(mod):
    text = importlib.import_module(mod).report().lower()
    assert any(mk in text for mk in _HONEST_MARKERS), f"{mod}.report() lost its honesty disclaimer"
