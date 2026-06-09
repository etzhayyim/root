#!/usr/bin/env python3
"""tsumugi narrate.py tests — Murakumo-only narration setup (ADR-2606092000 + 2605215000).

Verifies:
  - build_prompt produces aggregate intel (localities + camps) and NO private-person marker
  - G6: infer() against an EXTERNAL host RAISES (Murakumo-only)
  - G6: infer() against the fleet host with gate=False is a clean dry-run (no network)
  - run() works OFFLINE (dry-run/unreachable), published=False, writes the dry-run artifact
  - non-adjudicating: no verdict token leaks into the built prompt
  - determinism: build_prompt is identical across runs
"""
import sys, pathlib, tempfile

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
import narrate as N        # noqa: E402
import analyze_scale as A  # noqa: E402
import analyze_banner as B # noqa: E402

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
results = []

def check(name, cond):
    results.append(cond)
    print(f"  [{PASS if cond else FAIL}] {name}")


def main():
    print("\n=== tsumugi narrate (Murakumo-only) tests ===")
    scale = A.analyze(*A.load())
    banner = B.analyze(*B.load())
    prompt = N.build_prompt(scale, banner)

    check("prompt carries (A) locality intel", "jp.nagasaki" in prompt and "産官学報" in prompt)
    check("prompt carries (B) camp intel", "reach" in prompt and "bridges" in prompt)
    check("prompt is aggregate-only (no private-person marker)",
          ":private-person" not in prompt and "private-person" not in prompt)

    # non-adjudicating — the built USER prompt must not contain verdict tokens
    verdicts = ["corruption", "collusion", "癒着", "談合", "extremist", "過激"]
    check("non-adjudicating: no verdict token in prompt",
          not any(v in prompt for v in verdicts))

    # G6 — external host must RAISE even in dry-run
    raised = False
    try:
        N.infer("x", gate=False, base_url="https://api.openai.com")
    except ValueError:
        raised = True
    check("G6: external inference host raises", raised)

    # G6 — fleet host, gate=False → clean dry-run, no network
    text, status = N.infer("x", gate=False, base_url="http://127.0.0.1:4000")
    check("G6: fleet host dry-run returns (None,'dry-run')", text is None and status == "dry-run")

    # run() offline — published False, dry-run artifact written
    with tempfile.TemporaryDirectory() as d:
        st = N.run(gate=False, out=pathlib.Path(d))
        check("run(): published is False (G7)", st["published"] is False)
        check("run(): dry-run artifact written", (pathlib.Path(d) / "narration.dryrun.md").exists())

    # determinism
    check("determinism: identical prompt", N.build_prompt(scale, banner) == prompt)

    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
