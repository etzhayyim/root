#!/usr/bin/env python3
"""tsumugi ingest_scale.py tests — G7-gated structural-public org ingest (ADR-2606092000).

Hermetic (no network — the live path is exercised via a recorded WDQS-shaped fixture).
Verifies:
  - offline ingest adds org nodes + :custodies ties from the fixture
  - S2 person-excluded: every ingested node is :institutional (no person ever admitted)
  - S4/S5: every ingested tie is :custodies with >=2 sources, no verdict token
  - S1: no per-node score attr on ingested nodes
  - G7: `--live` without the operator gate RAISES LiveGateRefused
  - live WDQS JSON parses to rows (recorded fixture, no network)
  - the committed seed file is NEVER mutated by a merge write (out/ only)
  - determinism
"""
import sys, os, pathlib, tempfile

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
import ingest_scale as I  # noqa: E402

SEED = str(ACTOR_DIR / "data" / "seed-scale-power.kotoba.edn")
FIXTURES = ACTOR_DIR / "data" / "ingest-scale"

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
results = []

def check(name, cond):
    results.append(cond)
    print(f"  [{PASS if cond else FAIL}] {name}")


# a recorded WDQS SPARQL-results object (hermetic — what fetch_wikidata_orgs would return)
def _wdqs_obj():
    def cell(v):
        return {"value": v}
    # non-seed orgs so normalization yields NEW nodes/ties (Google/Audi are now promoted in-seed)
    return {"results": {"bindings": [
        {"child": cell("http://www.wikidata.org/entity/Q888"), "childLabel": cell("Pixar"),
         "parent": cell("http://www.wikidata.org/entity/Q7414"), "parentLabel": cell("The Walt Disney Company"),
         "countryLabel": cell("United States")},
        {"childLabel": cell("YouTube"), "parentLabel": cell("Google LLC"), "countryLabel": cell("United States")},
    ]}}


def main():
    print("\n=== tsumugi ingest_scale (G7) tests ===")
    # Hermetic synthetic fixture — independent of the committed fixture/seed convergence state.
    # The real fixture is consumed into the seed round by round; this synthetic one stays stable.
    import json as _json
    with tempfile.TemporaryDirectory() as _td:
        _sfx = pathlib.Path(_td)
        (_sfx / "synthetic.json").write_text(_json.dumps({"orgs": [
            {"child": "Pixar", "parent": "The Walt Disney Company",
             "country": "United States", "childRef": "Q888"},
            {"child": "Marvel Studios", "parent": "The Walt Disney Company",
             "country": "United States"},
        ]}))
        nodes, ties, new_nodes, new_ties, dropped = I.ingest_offline(_sfx, SEED)
        _, _, n2, t2, _ = I.ingest_offline(_sfx, SEED)   # determinism second run

    check("offline ingest adds org nodes", len(new_nodes) >= 1)
    check("offline ingest adds :custodies ties", len(new_ties) >= 1)

    # S2 — every ingested node is institutional; a person can never appear
    check("S2: all ingested nodes :institutional",
          all(n[":pwr/standing"] == ":institutional" for n in new_nodes))
    check("S2: no :private-person standing ingested",
          all(n[":pwr/standing"] != ":private-person" for n in new_nodes))
    # S1 — no per-node score attr
    forbidden = {":pwr/power-score", ":pwr/influence", ":pwr/rank", ":pwr/score"}
    check("S1: no per-node score attr ingested",
          all(not (set(n) & forbidden) for n in new_nodes))
    # S4/S5 — ties are factual :custodies with >=2 sources
    check("S5: all ingested ties :custodies (factual)",
          all(t[":tie/kind"] == ":custodies" for t in new_ties))
    check("S4: all ingested ties have >=2 sources",
          all(len(t[":tie/sources"]) >= 2 for t in new_ties))

    # G7 — live without the operator gate must RAISE
    saved = (os.environ.pop("TSUMUGI_OPERATOR_GATE", None), os.environ.pop("TSUMUGI_OPERATOR_DID", None))
    raised = False
    try:
        sys.argv = ["ingest_scale.py", "--live"]
        I.main()
    except I.LiveGateRefused:
        raised = True
    except SystemExit:
        pass
    finally:
        if saved[0] is not None: os.environ["TSUMUGI_OPERATOR_GATE"] = saved[0]
        if saved[1] is not None: os.environ["TSUMUGI_OPERATOR_DID"] = saved[1]
    check("G7: --live without operator gate raises LiveGateRefused", raised)

    # live WDQS JSON parses to rows (hermetic)
    rows = I.parse_wikidata_orgs(_wdqs_obj())
    check("live WDQS parse yields rows", len(rows) == 2 and rows[0]["child"] == "Pixar")
    check("live WDQS parse extracts QID ref from URI", rows[0]["childRef"] == "Q888")
    # those rows normalize cleanly through the membrane
    _, _, lv_nodes, lv_ties, _ = I.normalize_rows(rows, SEED)
    check("live rows normalize to org nodes + custody ties", bool(lv_nodes) and bool(lv_ties))

    # ANCHORED mode (hermetic): query builder pins to seed-org QIDs; aliases reconcile parents
    q = I.build_anchored_query(50)
    check("anchored query uses VALUES over anchor QIDs",
          "VALUES ?parent" in q and all(f"wd:{qid}" in q for qid in I.ANCHOR_QIDS))
    check("anchored query keeps S2 human-exclusion filter", "wd:Q5" in q)
    arow = [{"child": "Cruise LLC", "parent": "General Motors", "country": "United States"}]
    _, _, a_nodes, a_ties, _ = I.normalize_rows(arow, SEED)
    check("alias: GM children attach to existing seed org (no parallel parent)",
          bool(a_ties) and a_ties[0][":tie/from"] == "org.corp.us.gm"
          and all(n[":pwr/id"] != "org.ext.general-motors" for n in a_nodes))

    # RING-2 (hermetic): anchors derive from the seed's own citation QIDs; child-side alias
    qids = I.derive_seed_qids(SEED)
    check("ring-2: seed-derived anchor QIDs found", len(qids) >= 100 and "Q95" in qids)
    q2 = I.build_anchored_query(10, sorted(qids)[:5])
    check("ring-2: query builds over derived anchors", "VALUES ?parent" in q2)
    crow = [{"child": "Audi AG", "parent": "Volkswagen Group", "country": "Germany"}]
    _, _, c_nodes, c_ties, _ = I.normalize_rows(crow, SEED)
    check("alias: child-side variant reuses existing seed org (no duplicate Audi)",
          all(n[":pwr/id"] != "org.ext.audi-ag" for n in c_nodes))

    # FORAGE (粘菌/菌糸, hermetic): offline plan from the seed — harvested vs frontier tips
    plan = I.forage_plan(SEED)
    check("forage: separates harvested anchors from frontier tips",
          plan["harvested_anchors"] >= 1 and plan["frontier_tips"] >= 1)
    check("forage: emits a grow-or-fruit recommendation",
          ("GROW" in plan["recommendation"]) or ("FRUIT" in plan["recommendation"]))
    check("forage: not starving while Wikidata anchors remain",
          plan["starving"] is (plan["anchor_qids_available"] == 0 or plan["frontier_tips"] == 0))

    # GLEIF source (hermetic): recorded L2 page parses; rows carry GLEIF citations; membrane holds
    gleif_obj = {"data": [{"id": "TESTLEI00000000000AA", "attributes": {"entity": {
        "legalName": {"name": "Test Subsidiary GmbH"},
        "legalAddress": {"country": "DE"}}}}]}
    grows = I.parse_gleif_children(gleif_obj, "Volkswagen AG")
    check("gleif: recorded page parses to rows", len(grows) == 1
          and grows[0]["child"] == "Test Subsidiary GmbH" and grows[0]["country"] == "DE")
    check("gleif: row carries L2-RR citation + real record URL",
          grows[0]["cite"][0].startswith("GLEIF Level-2")
          and grows[0]["cite"][1] == "https://search.gleif.org/#/record/TESTLEI00000000000AA")
    _, _, g_nodes, g_ties, _ = I.normalize_rows(grows, SEED)
    check("gleif: rows cross the membrane (attach to seed VW, GLEIF citations kept)",
          bool(g_ties) and g_ties[0][":tie/from"] == "org.ext.volkswagen-ag"
          and g_ties[0][":tie/sources"][0].startswith("GLEIF Level-2"))
    check("gleif: ISO-2 country maps to locality (DE→de, GB→uk)",
          I.locality_of("DE") == "de" and I.locality_of("GB") == "uk")

    # committed seed is NEVER mutated by a merge write
    before = pathlib.Path(SEED).read_bytes()
    with tempfile.TemporaryDirectory() as d:
        I.write_merge(pathlib.Path(d), SEED, new_nodes, new_ties, "")
        after = pathlib.Path(SEED).read_bytes()
        out_files = list(pathlib.Path(d).glob("*.kotoba.edn"))
    check("committed seed file NOT mutated by write_merge", before == after)
    check("merge writes artifacts to out dir only", len(out_files) == 2)

    # determinism (n2/t2 from second run of same synthetic fixture, captured above)
    check("determinism: identical ingest",
          [n[":pwr/id"] for n in new_nodes] == [n[":pwr/id"] for n in n2]
          and [t[":tie/id"] for t in new_ties] == [t[":tie/id"] for t in t2])

    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
