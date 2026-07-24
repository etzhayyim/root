#!/usr/bin/env python3
"""cascade — e4b 高速一次処理 → 失敗のみ 12b へエスカレーション。

Pass 1: gemma4:e4b-it-qat (2 req/node, 速い, ~33%)
Pass 2: pass1 の fail/error のみ gemma4:12b-it-qat (1 req/node, ~44%)

Usage:
  rg --files orgs/etzhayyim -g '*.py' | python3 cascade.py -
  python3 cascade.py FILE [FILE...]

結果: fleet-refactor-results.jsonl (pass 列付き) / SFT は通常どおり収穫。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
HARNESS = HERE / "fleet_refactor.py"
RESULTS = Path("fleet-refactor-results.jsonl")


def run_pass(files: list[str], model: str, per_node: int, timeout: int) -> None:
    subprocess.run(
        [sys.executable, str(HARNESS), "--model", model,
         "--per-node", str(per_node), "--timeout", str(timeout), "-"],
        input="\n".join(files), text=True, check=False)


def statuses_since(line_offset: int) -> dict[str, str]:
    out = {}
    if RESULTS.exists():
        for line in RESULTS.read_text().splitlines()[line_offset:]:
            r = json.loads(line)
            out[r["src"]] = r["status"]
    return out


def main() -> int:
    args = sys.argv[1:]
    files = []
    for a in args:
        if a == "-":
            files += [l.strip() for l in sys.stdin if l.strip()]
        else:
            files.append(a)
    if not files:
        print("no input files", file=sys.stderr)
        return 2

    offset0 = len(RESULTS.read_text().splitlines()) if RESULTS.exists() else 0
    print(f"=== pass 1: e4b-it-qat ({len(files)} files) ===")
    run_pass(files, "gemma4:e4b-it-qat", per_node=2, timeout=420)

    st = statuses_since(offset0)
    failed = [f for f in files if st.get(f) not in ("ok", "skip")]
    ok1 = sum(1 for f in files if st.get(f) == "ok")
    print(f"\n=== pass 1 done: {ok1}/{len(files)} ok; escalating {len(failed)} to 12b ===")

    if failed:
        offset1 = len(RESULTS.read_text().splitlines())
        run_pass(failed, "gemma4:12b-it-qat", per_node=1, timeout=600)
        st2 = statuses_since(offset1)
        ok2 = sum(1 for f in failed if st2.get(f) == "ok")
        print(f"\n=== pass 2 done: +{ok2} ok ===")
        total_ok = ok1 + ok2
    else:
        total_ok = ok1

    skipped = sum(1 for f in files if st.get(f) == "skip")
    print(f"\n=== cascade summary: {total_ok}/{len(files)} ok "
          f"({skipped} skip, {len(files) - total_ok - skipped} unported) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
