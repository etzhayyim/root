#!/usr/bin/env python3
"""tsumugi (A+B) coverage_scale.py tests.

Verifies:
  - all 7 SCALES are detected as exercised in the current seed
  - coverage result exposes per-scale, per-collective-kind, per-sector, and per-country dims
  - determinism (two runs identical)
"""
import sys, pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
import coverage_scale as C  # noqa: E402

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
results = []

def check(name, cond):
    results.append(cond)
    print(f"  [{PASS if cond else FAIL}] {name}")

def main():
    print("\n=== tsumugi coverage_scale tests ===")
    nodes, ties, banners, ents, flies = C.load_data()
    result = C.compute(nodes, ties, banners, ents, flies)

    # 1. all 7 SCALES exercised
    check("all 7 scales exercised", len(result["per_scale"]["exercised"]) == len(C.SCALES) and len(result["per_scale"]["missing"]) == 0)

    # 2. exposes dims
    check("exposes per-scale", "per_scale" in result)
    check("exposes per-kind", "per_kind" in result)
    check("exposes per-sector", "per_sector" in result)
    check("exposes per-country", "per_country" in result)

    # 3. determinism
    r2 = C.compute(nodes, ties, banners, ents, flies)
    check("determinism: identical report", C.render(result) == C.render(r2))

    if not all(results):
        sys.exit(1)

if __name__ == "__main__":
    main()
