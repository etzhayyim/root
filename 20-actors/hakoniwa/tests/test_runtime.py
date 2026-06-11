#!/usr/bin/env python3
"""hakoniwa 箱庭 — runtime tests: social emission + Murakumo fallback + autonomous loop.
ADR-2606111500 (R1). Pure stdlib, network-free, deterministic.

Verifies:
  - G2: a post asserting a point/certain future is REFUSED (draft + emit boundary)
  - G3: a post steering behaviour (買え/投票/you should) is REFUSED
  - G7: a :published post with no member-DID author is REFUSED (draft + emit)
  - a clean distribution post passes both guards and carries the invariant flags
  - Murakumo narrate() falls back deterministically to a template when the fleet is offline,
    and the fallback narration itself passes the post guards
  - the autonomous loop runs end-to-end, persists a content-addressed tx per cycle, and the
    append-only commit-DAG verifies (tamper-evident); a re-run reproduces identical CIDs
  - :published mode (with a member DID) is representable and persists (R1 authorization)
"""
import sys
import pathlib
import tempfile

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

import world as W  # noqa: E402
import simulate as S  # noqa: E402
import distribution as D  # noqa: E402
import murakumo as M  # noqa: E402
import social as SOC  # noqa: E402
import autorun  # noqa: E402
import kotoba as K  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-scenario.kotoba.edn"


def _dist():
    nodes, edges = W.load(SEED)
    results, _ = S.ensemble(nodes, edges, steps=12, replicas=64, seed=7)
    return D.distribution(results)


def test_post_guards_clean_pass():
    p = SOC.draft_distribution_post("町の洪水避難訓練の自主採用", _dist(),
                                    narration="架空ペルソナによるシナリオ探索です。")
    assert p[":post/distribution-only"] is True
    assert p[":post/non-steering"] is True
    assert p[":post/server-held-key"] is False
    assert p[":post/status"] == ":dry-run"
    # emit re-applies the guards and returns a receipt
    r = SOC.emit(p)
    assert r["substrate"] == "kotoba-datom-log"


def test_g2_no_point_refused():
    for bad in ("必ず採用される", "確実に普及する未来", "we predict that adoption is guaranteed"):
        raised = False
        try:
            SOC.draft_distribution_post("s", _dist(), narration=bad)
        except ValueError:
            raised = True
        assert raised, f"G2 breach: point/certainty narration accepted: {bad!r}"


def test_g3_no_steer_refused():
    for bad in ("今すぐ投票しよう", "あなたは支持せよ", "you should sign up now", "ボイコットしよう"):
        raised = False
        try:
            SOC.draft_distribution_post("s", _dist(), narration=bad)
        except ValueError:
            raised = True
        assert raised, f"G3 breach: steering narration accepted: {bad!r}"


def test_g7_published_needs_author():
    raised = False
    try:
        SOC.draft_distribution_post("s", _dist(), status=":published")  # no author
    except ValueError:
        raised = True
    assert raised, "G7 breach: :published post accepted with no member-DID author"
    # with an author it is representable
    p = SOC.draft_distribution_post("s", _dist(), author="did:web:etzhayyim.com:member:test",
                                    status=":published")
    assert p[":post/status"] == ":published"
    # emit refuses a :published post if the author is stripped post-hoc
    p[":post/author"] = ""
    bad = False
    try:
        SOC.emit(p)
    except ValueError:
        bad = True
    assert bad, "G7 breach: emit published a post with no author"


def test_murakumo_fallback_is_deterministic_and_guard_clean():
    d = _dist()
    n1 = M.narrate("町の洪水避難訓練の自主採用", d, prefer_fleet=False)
    n2 = M.narrate("町の洪水避難訓練の自主採用", d, prefer_fleet=False)
    assert n1 == n2, "template fallback not deterministic"
    assert n1["via"] == ":template-fallback"
    # the fallback narration must itself pass the post guards (no point / no steer)
    p = SOC.draft_distribution_post("町の洪水避難訓練の自主採用", d, narration=n1["text"])
    assert p[":post/body"]


def test_persona_step_fallback_clamps():
    r = M.persona_step(0.5, 0.9, 0.6, 0.4, prefer_fleet=False)
    assert r["via"] == ":kernel-fallback"
    assert 0.0 <= r["stance"] <= 1.0


def test_autonomous_loop_persists_and_verifies():
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "h.datoms.kotoba.edn"
        res = autorun.run_autonomous(3, log_path=log)
        assert res["cycles"] == 3
        assert res["log_length"] == 3
        assert res["chain"]["ok"], f"commit-DAG broken: {res['chain']}"
        assert all(b["datoms"] > 50 for b in res["beats"]), "too few datoms persisted per cycle"
        # every cycle emitted to the canonical substrate
        for b in res["beats"]:
            assert b["emit"]["substrate"] == "kotoba-datom-log"


def test_autonomous_loop_resume_safe_identical_cids():
    with tempfile.TemporaryDirectory() as td:
        a = autorun.run_autonomous(3, log_path=pathlib.Path(td) / "a.edn")
    with tempfile.TemporaryDirectory() as td:
        b = autorun.run_autonomous(3, log_path=pathlib.Path(td) / "b.edn")
    assert [x["cid"] for x in a["beats"]] == [x["cid"] for x in b["beats"]], \
        "autonomous run is not resume-safe (CIDs differ across identical runs)"


def test_published_mode_persists():
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "h.edn"
        res = autorun.run_autonomous(2, log_path=log,
                                     author="did:web:etzhayyim.com:member:founder", publish=True)
        assert res["chain"]["ok"]
        assert all(b["post_status"] == ":published" for b in res["beats"]), \
            "R1 :published mode did not produce published posts"


def test_tamper_breaks_chain():
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "h.edn"
        autorun.run_autonomous(2, log_path=log)
        lines = log.read_text(encoding="utf-8").splitlines()
        # corrupt a datom value in the first transaction line
        for i, ln in enumerate(lines):
            if ln.startswith("{:tx/id 1"):
                lines[i] = ln.replace(":forecast/point-asserted false",
                                      ":forecast/point-asserted true")
                break
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        assert K.verify_chain(log)["ok"] is False, "tamper of a persisted datom was not detected"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
