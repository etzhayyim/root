#!/usr/bin/env python3
"""kaiyaku 解約 — severance-plan tests (ADR-2606112200). Pure stdlib.

Verifies the executor gates empirically:
  - safest-first tier routing: api → T1, browser-permitted → T2, else T3
  - G3: a :prohibited/:unknown browser stance NEVER yields T2; evasion verbs raise
  - cascade ties plan a rehome-dependency step FIRST
  - G8: notice/penalty are carried into the plan (cost-of-severance honesty)
  - G5/G6: every plan demands member-sig + dry-run + Council gate; execute() raises
  - only :sever / :review-cascade ties are plannable (:keep refuses)
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze  # noqa: E402
from plan import select_tier, build_plan, plans, execute, _make_step, EVASION_VERBS  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-en-ledger.kotoba.edn"


def _ctx():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    return nodes, {t["svc"]: t for t in res["ties"]}


def test_tier_routing():
    nodes, _ = _ctx()
    assert select_tier(nodes["svc:saas-c"]) == "T1"      # api :available
    assert select_tier(nodes["svc:video-a"]) == "T2"     # browser :permitted
    assert select_tier(nodes["svc:gym-b"]) == "T3"       # browser :prohibited
    assert select_tier(nodes["svc:merchant-g"]) == "T3"  # browser :unknown → refuse T2


def test_prohibited_browser_never_t2():
    """G3 by construction: no input shape with :browser :prohibited returns T2."""
    nodes, _ = _ctx()
    for svc in nodes.values():
        cancel = svc.get(":svc/cancel", {}) or {}
        if cancel.get(":browser") in (":prohibited", ":unknown"):
            assert select_tier(svc) != "T2", svc.get(":svc/id")


def test_evasion_unrepresentable():
    for verb in sorted(EVASION_VERBS):
        try:
            _make_step(verb, "x")
            raise AssertionError(f"evasion verb '{verb}' was representable")
        except ValueError:
            pass


def test_cascade_rehome_first():
    nodes, ties = _ctx()
    p = build_plan(nodes["svc:mail-f"], ties["svc:mail-f"])
    assert p["recommendation"] == ":review-cascade"
    assert p["steps"][0]["verb"] == "rehome-dependency"
    rehomes = [s for s in p["steps"] if s["verb"] == "rehome-dependency"]
    assert len(rehomes) == 2  # sns-e + cloud-h both SSO through mail-f


def test_cost_of_severance_carried():
    nodes, ties = _ctx()
    p = build_plan(nodes["svc:gym-b"], ties["svc:gym-b"])
    assert p["notice_days"] == 30 and p["penalty_jpy"] == 5000
    # and no step plans around the obligation
    assert all("penalty" not in s["verb"] for s in p["steps"])


def test_destructive_gates_and_dry_run():
    nodes, ties = _ctx()
    p = build_plan(nodes["svc:video-a"], ties["svc:video-a"])
    assert p["requires"] == {"member_sig": True, "dry_run_confirm": True,
                             "council_lv6_operator_gate": True}
    assert p["mode"] == "dry-run"
    assert all(s["mode"] == "dry-run" for s in p["steps"])
    try:
        execute(p)
        raise AssertionError("execute() must raise at R0 (G5/G6)")
    except RuntimeError:
        pass


def test_keep_not_plannable():
    nodes, ties = _ctx()
    try:
        build_plan(nodes["svc:saas-c"], ties["svc:saas-c"])  # :keep
        raise AssertionError(":keep tie was plannable")
    except ValueError:
        pass


def test_plans_cover_all_severables():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    ps = plans(nodes, edges)
    want = {t["svc"] for t in res["ties"]
            if t["recommendation"] in (":sever", ":review-cascade")}
    assert {p["svc"] for p in ps} == want
    assert all(s["verb"] == "export-own-data" for p in ps for s in p["steps"][-2:-1])


def test_plans_json_export():
    """Wave 40: severance plans の機械可読 JSON (tate と対称 — yoro UI 配線が
    両 actor で完備)."""
    import json
    nodes, edges = load(SEED)
    ps = plans(nodes, edges)
    back = json.loads(json.dumps(ps, ensure_ascii=False))
    assert len(back) == len(ps) >= 5
    assert all(p["mode"] == "dry-run" and "steps" in p for p in back)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} passed")
