#!/usr/bin/env python3
"""tsumugi (A) analyze_scale.py tests — one per structural gate (ADR-2606092000).

Verifies:
  - 長崎 surfaces as the top cross-sector cluster with full 産官学報 diversity (=4)
  - concentration is edge-primary (per-locality aggregate; no per-node score in output)
  - S2 person-exclusion: a :private-person standing RAISES
  - S1: a :pwr/power-score node attr RAISES
  - S4: an under-sourced tie (<2 sources) RAISES
  - S5: a verdict token (:癒着) as :tie/kind RAISES
  - determinism: two runs produce identical output
"""
import sys, pathlib, tempfile

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
import analyze_scale as A  # noqa: E402

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
results = []

def check(name, cond):
    results.append(cond)
    print(f"  [{PASS if cond else FAIL}] {name}")

def expect_raise(name, edn_text):
    with tempfile.NamedTemporaryFile("w", suffix=".edn", delete=False, encoding="utf-8") as f:
        f.write(edn_text); path = f.name
    try:
        A.load(path); check(name, False)
    except ValueError:
        check(name, True)
    finally:
        pathlib.Path(path).unlink(missing_ok=True)


def main():
    print("\n=== tsumugi (A) scale tests ===")
    nodes, ties = A.load()
    result = A.analyze(nodes, ties)

    # 長崎 is a full 産官学報 (4 sectors) cluster; the top cluster is always a 4-sector weave
    # (as more real regional clusters land — 愛知/広島 — the #1 slot reflects true density)
    by_loc = {x["locality"]: x for x in result["localities"]}
    nagasaki = by_loc.get("jp.nagasaki")
    check("jp.nagasaki present as a cluster", nagasaki is not None)
    check("長崎 weaves all 4 産官学報 sectors", nagasaki and nagasaki["sector_diversity"] == 4)
    check("長崎 concentration is positive", nagasaki and nagasaki["concentration"] > 0)
    check("top locality is a full 4-sector 産官学報 cluster",
          result["localities"][0]["sector_diversity"] >= 4)

    # broker is an org/seat id (never a private person) and spans sectors
    brokers = result["brokers"]
    check("top broker is a seat/org id", brokers and brokers[0]["id"].startswith(("org.", "seat.")))
    check("top broker bridges ≥2 other sectors", brokers[0]["span"] >= 2)

    # granularity (粒度) — 社内派閥/学閥/コミュニティ surface as collective-kinds
    cks = {x["kind"] for x in result["collective_kinds"]}
    check("社内派閥 (intra-org-faction) granularity present", ":intra-org-faction" in cks)
    check("学閥 (academic-clique) granularity present", ":academic-clique" in cks)
    check("コミュニティ (community) granularity present", ":community" in cks)
    check("市区町村 (municipality) granularity present", ":municipality" in cks)
    # 市区町村 scale is one step below 県 (regional) — 豊田市/長崎市 clusters surface
    scale_names = {s["scale"] for s in result["scales"]}
    check("municipal scale present (市区町村)", ":municipal" in scale_names)
    check("supranational scale present (EU)", ":supranational" in scale_names)
    check("global scale present (IMF/BIS)", ":global" in scale_names)
    # every scale tier from :global down to :intra-org is now exercised
    check("all 7 scale tiers exercised", len(scale_names & set(A.SCALES)) == len(A.SCALES))
    check("豊田市 (jp.aichi.toyota-shi) cluster surfaces", "jp.aichi.toyota-shi" in by_loc)
    # 全世界 coverage has begun — at least one non-JP locality present
    check("overseas (non-jp) locality present", any(not l.startswith("jp") for l in by_loc))

    # cross-scale vertical integration — Toyota family (root org.corp.jp.7203) threads ≥2 scales
    vfam = {x["root"]: x for x in result["vertical"]}
    check("vertical integration computed", len(result["vertical"]) >= 1)
    toyota = vfam.get("org.corp.jp.7203")
    check("Toyota family threads ≥2 scales (国→市→社内)", toyota and toyota["scale_span"] >= 2)

    # S1 — output graph carries NO per-node score, only per-locality readouts
    graph = A.render_graph_edn(result)
    check("S1: no per-node score attr in output", ":pwr/power-score" not in graph
          and ":scale.cluster/concentration" in graph)

    # gate breaches must RAISE
    base_node = '{:pwr/id "x" :pwr/label "x" :pwr/standing %s :pwr/scale :local :pwr/sector :san :pwr/locality "z"}'
    expect_raise("S2: :private-person standing raises", "[" + base_node % ":private-person" + "]")
    expect_raise("S1: :pwr/power-score attr raises",
                 '[{:pwr/id "x" :pwr/label "x" :pwr/standing :institutional :pwr/scale :local '
                 ':pwr/sector :san :pwr/locality "z" :pwr/power-score 9}]')
    expect_raise("S4: under-sourced tie (<2) raises",
                 '[{:tie/id "t" :tie/kind :funds :tie/from "a" :tie/to "b" '
                 ':tie/grasping-load 0.5 :tie/sources ["only-one"] :tie/sourcing :representative}]')
    expect_raise("S5: verdict token :癒着 as :tie/kind raises",
                 '[{:tie/id "t" :tie/kind :癒着 :tie/from "a" :tie/to "b" '
                 ':tie/grasping-load 0.5 :tie/sources ["a" "b"] :tie/sourcing :representative}]')

    # determinism
    r2 = A.analyze(*A.load())
    check("determinism: identical report", A.render_report(result) == A.render_report(r2))

    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
