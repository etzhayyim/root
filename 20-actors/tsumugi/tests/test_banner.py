#!/usr/bin/env python3
"""tsumugi (B / 旗 hata) analyze_banner.py tests — one per thought-policing gate.

Verifies (ADR-2606092000):
  - camps + bridges + genealogy compute from the seed
  - H1: an :inferred basis RAISES (no imputed ideology)
  - H2: a threat token (:過激) as :banner/kind RAISES
  - H3: a :ent/ideology-score node attr RAISES (no score-of-conviction)
  - H4: a :flies/who pointing at a non-institutional (private) entity RAISES
  - H6: an entity flying ≥2 banners appears as a BRIDGE (plural allowed)
  - H7: an under-sourced :flies (<2) RAISES
  - non-adjudicating: no threat token anywhere in the rendered output
  - determinism
"""
import sys, pathlib, tempfile

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
import analyze_banner as B  # noqa: E402

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
results = []

def check(name, cond):
    results.append(cond)
    print(f"  [{PASS if cond else FAIL}] {name}")

def expect_raise(name, edn_text):
    with tempfile.NamedTemporaryFile("w", suffix=".edn", delete=False, encoding="utf-8") as f:
        f.write(edn_text); path = f.name
    try:
        B.load(path); check(name, False)
    except ValueError:
        check(name, True)
    finally:
        pathlib.Path(path).unlink(missing_ok=True)


def main():
    print("\n=== tsumugi (B / 旗) banner tests ===")
    banners, ents, flies = B.load()
    result = B.analyze(banners, ents, flies)

    check("camps computed", len(result["camps"]) == len(banners))
    check("genealogy links banners to streams", len(result["genealogy"]) >= 4)

    # H6 — pluralism: the centrist party flies ≥2 banners → a bridge
    bridge_ids = {b["ent"] for b in result["bridges"]}
    check("H6: multi-banner entity is a bridge", "org.party.jp.c" in bridge_ids)

    # H5 — etzhayyim's own banner is inbound-only (not a camp it recruits others into)
    self_camp = next(c for c in result["camps"] if c["banner"] == "banner.etzhayyim.charter")
    check("H5: self banner has 0 projected members", self_camp["member_count"] == 0)

    # non-adjudicating — no threat token leaks into the rendered report
    report = B.render_report(result)
    check("non-adjudicating: no threat token in report",
          not any(tok.strip(":") in report for tok in B.THREAT_TOKENS))

    # gate breaches must RAISE
    ent_ok = '{:ent/id "e" :ent/label "e" :ent/standing :institutional}'
    ban_ok = '{:banner/id "b" :banner/label "b" :banner/kind :policy-stance}'
    expect_raise("H1: :inferred basis raises",
                 "[" + ban_ok + " " + ent_ok +
                 ' {:flies/id "f" :flies/who "e" :flies/banner "b" :flies/basis :inferred '
                 ':flies/weight 0.5 :flies/sources ["a" "b"] :flies/sourcing :representative}]')
    expect_raise("H2: threat token :過激 as :banner/kind raises",
                 '[{:banner/id "b" :banner/label "b" :banner/kind :過激}]')
    expect_raise("H3: :ent/ideology-score attr raises",
                 '[{:ent/id "e" :ent/label "e" :ent/standing :institutional :ent/ideology-score 9}]')
    expect_raise("H4: private-person :flies/who raises",
                 "[" + ban_ok +
                 ' {:ent/id "e" :ent/label "e" :ent/standing :private-person}'
                 ' {:flies/id "f" :flies/who "e" :flies/banner "b" :flies/basis :self-declared '
                 ':flies/weight 0.5 :flies/sources ["a" "b"] :flies/sourcing :representative}]')
    expect_raise("H7: under-sourced :flies (<2) raises",
                 "[" + ban_ok + " " + ent_ok +
                 ' {:flies/id "f" :flies/who "e" :flies/banner "b" :flies/basis :self-declared '
                 ':flies/weight 0.5 :flies/sources ["only-one"] :flies/sourcing :representative}]')

    # determinism
    r2 = B.analyze(*B.load())
    check("determinism: identical report", B.render_report(result) == B.render_report(r2))

    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
