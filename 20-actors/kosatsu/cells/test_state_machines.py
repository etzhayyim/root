"""test_state_machines.py — 高札 (kosatsu) cell scaffolds + publication membrane. ADR-2606072000."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "methods"))

from _t import expect_raises, run  # noqa: E402
from competing_claim_weave.cell import CompetingClaimWeaveCell  # noqa: E402
from designation_ingest.cell import DesignationIngestCell  # noqa: E402
from social_post.cell import SocialPostCell  # noqa: E402
from social_post.state_machine import PostPhase, transition_to_drafted  # noqa: E402


# ── G8: every cell .solve() raises at R0 ──────────────────────────────────────
def test_designation_ingest_solve_raises():
    expect_raises(lambda: DesignationIngestCell().solve({}), contains="G8")


def test_competing_claim_weave_solve_raises():
    expect_raises(lambda: CompetingClaimWeaveCell().solve({}), contains="G8")


def test_social_post_solve_raises():
    expect_raises(lambda: SocialPostCell().solve({}), contains="G8")


# ── publication membrane (G2/G3/G7/G8/G9) ─────────────────────────────────────
def test_post_drafts_when_clean():
    out = transition_to_drafted({"subject": "subj-alpha contested",
                                 "sources": ["https://ofac.treasury.gov/", "https://www.sanctionsmap.eu/"]})
    cs = out["cell_state"]
    assert cs["phase"] == PostPhase.DRAFTED.value
    assert cs["payload"][":post/status"] == ":dry-run"
    assert cs["payload"][":post/is-mirror"] is True
    assert cs["payload"][":post/server-held-key"] is False
    assert cs["payload"][":post/body"].startswith("[mirror")


def test_post_refuses_under_sourced():
    out = transition_to_drafted({"subject": "x", "sources": ["https://ofac.treasury.gov/"]})
    assert out["cell_state"]["phase"] == PostPhase.REFUSED.value
    assert "G3" in out["cell_state"]["refusal"]


def test_post_refuses_published_status():
    out = transition_to_drafted({"subject": "x", "requested_status": "published",
                                 "sources": ["https://ofac.treasury.gov/", "https://www.sanctionsmap.eu/"]})
    assert out["cell_state"]["phase"] == PostPhase.REFUSED.value
    assert "G8" in out["cell_state"]["refusal"]


def test_post_refuses_server_key():
    out = transition_to_drafted({"subject": "x", "server_held_key": True,
                                 "sources": ["https://ofac.treasury.gov/", "https://www.sanctionsmap.eu/"]})
    assert out["cell_state"]["phase"] == PostPhase.REFUSED.value
    assert "G7" in out["cell_state"]["refusal"]


if __name__ == "__main__":
    run("state-machines", [(k, v) for k, v in sorted(globals().items())
                           if k.startswith("test_") and callable(v)])
