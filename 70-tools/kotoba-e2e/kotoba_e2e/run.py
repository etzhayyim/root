"""CLI entrypoint for the browser-only-kotoba e2e harness.

    python -m kotoba_e2e.run                         # https://etzhayyim.com, headless, agent on
    python -m kotoba_e2e.run --url https://yoro.etzhayyim.com --headed
    python -m kotoba_e2e.run --no-agent              # deterministic layer only (no Murakumo)
    python -m kotoba_e2e.run --json                  # machine-readable report

Exit code 0 iff the deterministic browser-only CORE checks pass.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from .graph import run_pipeline


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="kotoba-e2e")
    ap.add_argument("--url", default="https://etzhayyim.com")
    ap.add_argument("--headed", action="store_true", help="show the browser (default headless)")
    ap.add_argument("--no-agent", action="store_true", help="skip the browser-use agentic layer")
    ap.add_argument("--json", action="store_true", help="emit JSON only")
    args = ap.parse_args(argv)

    try:
        report = asyncio.run(run_pipeline(
            args.url, headless=not args.headed, use_agent=not args.no_agent,
        ))
    except Exception as e:
        msg = f"e2e harness failed to run: {e}"
        if args.json:
            print(json.dumps({"error": msg}))
        else:
            print("✗ " + msg)
            print("  (need: pip install -r requirements.txt && playwright install chromium;"
                  " agentic layer also needs the Murakumo gateway up at 127.0.0.1:4000)")
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
        return 0 if report.get("browser_only_ok") else 1

    ok = report.get("browser_only_ok")
    print(f"\n{'✓' if ok else '✗'} browser-only kotoba: {report['url']}\n")
    for c in report.get("checks", []):
        mark = "✓" if c["passed"] else "✗"
        print(f"  {mark} {c['name']:22} {c['detail']}")
    print(f"\n  murakumo_up: {report.get('murakumo_up')}")
    if report.get("llm_verdict"):
        print(f"  llm_judge:   {report['llm_verdict']}")
    av = report.get("agent_verdict") or {}
    if av:
        print(f"  agent:       ran={av.get('ran')} — {str(av.get('summary'))[:200]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
