#!/usr/bin/env python3
"""kaiyaku 解約 — tate handoff ingest tests (wave 26). Pure stdlib.

The compose loop closes: tate's make_kaiyaku_handoff output is parsed by kaiyaku's
ingest and every :kaiyaku-routed clause flag becomes a notice-window candidate —
round-trip across the two actors, no shared code beyond the EDN wire format.
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
sys.path.insert(0, str(ACTOR_DIR.parent / "tate" / "methods"))

from handoff_ingest import ingest, to_datoms, _live_handoff_from_tate  # noqa: E402


def _cands():
    return ingest(_live_handoff_from_tate())


def test_roundtrip_count_matches_tate():
    """Every :kaiyaku-routed tate flag arrives as exactly one candidate."""
    from terms_scan import load_docs, load_patterns, scan
    docs, _ = load_docs()
    res = scan(docs, load_patterns())
    expect = [f for f in res["flags"] if f["route"] == ":kaiyaku"]
    cands = _cands()
    assert len(cands) == len(expect) and len(cands) >= 10
    assert {c["clause"] for c in cands} == {f["clause"] for f in expect}


def test_candidates_are_calendar_actions():
    for c in _cands():
        assert c["action"] == ":calendar-notice-window", c
        assert c["anchor"], c  # 開示アンカーは handoff を越えて保持される
        assert c["jurisdiction"].startswith(":")


def test_datoms_emitted():
    cands = _cands()
    text = to_datoms(cands, tx=5)
    assert text.count(":kaiyaku.handoff/clause") == len(cands)
    assert ":kaiyaku.handoff/action :calendar-notice-window" in text


def test_kaiyaku_claude_md_counts_in_sync():
    """Wave 38: kaiyaku 側も CLAUDE.md のテスト数を実数照合 (同期封殺5本目 —
    両 actor で counts-sync 完備)."""
    import re
    md = (ACTOR_DIR / "CLAUDE.md").read_text(encoding="utf-8")
    n_tests = sum(f.read_text(encoding="utf-8").count("\ndef test_")
                  for f in (ACTOR_DIR / "tests").glob("test_*.py"))
    m = re.search(r"# (\d+) tests, pure stdlib", md)
    assert m and int(m.group(1)) == n_tests, f"kaiyaku CLAUDE.md test count drift (actual {n_tests})"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} passed")
