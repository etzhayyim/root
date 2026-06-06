"""test_social.py — 系図 (keizu) dry-run social-post invariants. ADR-2606066000."""
from __future__ import annotations

from _t import expect_raises, run
from social import (DISCLAIMER, build_live, draft_committee_post,
                    draft_money_post)

_FINDING = {"committee": "c1", "label": "demo委員会", "member_count": 3,
            "distinct_organs": 2, "organs": ["A", "B"]}
_SRCS = ["https://a.gov/", "https://b.gov/"]


def test_committee_post_pins_invariants():
    p = draft_committee_post(_FINDING, _SRCS)
    assert p[":post/status"] == ":dry-run"
    assert p[":post/is-mirror"] is True
    assert p[":post/non-adjudicating-notice"] is True
    assert p[":post/server-held-key"] is False
    assert p[":post/body"].startswith(DISCLAIMER[:8])


def test_post_carries_sources():
    p = draft_committee_post(_FINDING, _SRCS)
    assert len(p[":post/sources"]) >= 2


def test_g3_under_sourced_post_refused():
    expect_raises(lambda: draft_committee_post(_FINDING, ["only-one"]), contains="G3")


def test_money_post_dry_run():
    mc = {"hhi": 0.5, "total": 100.0, "shares": [("payee-x", 0.6), ("payee-y", 0.4)]}
    p = draft_money_post(mc, _SRCS)
    assert p[":post/status"] == ":dry-run"
    assert "HHI" in p[":post/body"]


def test_g8_live_post_refused():
    expect_raises(lambda: build_live(), contains="G8")


def test_money_post_empty_shares_safe():
    p = draft_money_post({"hhi": 0.0, "total": 0.0, "shares": []}, _SRCS)
    assert p[":post/status"] == ":dry-run"
    assert "(none)" in p[":post/body"]   # no IndexError on empty concentration


def test_committee_post_blank_author_is_fine():
    p = draft_committee_post(_FINDING, _SRCS, author="")
    assert p[":post/author"] == ""       # author only required for a (gated) live post


if __name__ == "__main__":
    run("social", [(k, v) for k, v in sorted(globals().items())
                   if k.startswith("test_") and callable(v)])
