from __future__ import annotations

import json
import pathlib

from electrolysis import kotoba_datoms, render_report, run_comparison

OUT = pathlib.Path(__file__).resolve().parent / "out"


def main() -> int:
    comparison = run_comparison()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "comparison.json").write_text(json.dumps(comparison, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "comparison.md").write_text(render_report(comparison), encoding="utf-8")
    (OUT / "kotoba-datoms.json").write_text(json.dumps(kotoba_datoms(comparison), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(render_report(comparison))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
