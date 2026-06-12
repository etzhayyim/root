#!/usr/bin/env python3
"""build_cpt_full — gold-corpus + 増幅で収穫した ok-unit Clojure を CPT データへ統合。

CPT データ = (1) Fable gold 30本の全文 + (2) fleet 増幅で clj-kondo+bb を通った
ok-unit の Clojure スニペット (assistant message から ```clojure ブロックを抽出)。
どちらも検証済みの idiomatic Clojure。stub は含まない (ok-unit のみ収穫されている)。

Usage:
  python3 build_cpt_full.py GOLD_DIR SFT.jsonl OUT.jsonl
  python3 build_cpt_full.py ../gold-corpus ../fleet-refactor-sft.jsonl cpt-full.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CLJ_BLOCK = re.compile(r"```(?:clojure|clj)?\s*\n(.*?)```", re.DOTALL)


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: build_cpt_full.py GOLD_DIR SFT.jsonl OUT.jsonl", file=sys.stderr)
        return 2
    gold_dir, sft_path, out_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    docs = []

    # (1) gold full files
    for clj in sorted(gold_dir.glob("*.clj")):
        docs.append(f";; file: {clj.name}\n{clj.read_text(encoding='utf-8')}")

    # (2) harvested ok-unit clojure snippets (dedup by content)
    seen = set()
    n_units = 0
    if sft_path.exists():
        for line in sft_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            asst = next((m["content"] for m in r["messages"]
                         if m["role"] == "assistant"), "")
            m = CLJ_BLOCK.search(asst)
            if not m:
                continue
            code = m.group(1).strip()
            if code in seen or len(code) < 20:  # 全文で dedup (prefix だと別実装が衝突)
                continue
            seen.add(code)
            src = r.get("meta", {}).get("src", "?")
            unit = r.get("meta", {}).get("unit", "?")
            docs.append(f";; unit: {unit} (from {src})\n{code}")
            n_units += 1

    with out_path.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps({"text": d}, ensure_ascii=False) + "\n")
    chars = sum(len(d) for d in docs)
    n_gold = len(docs) - n_units
    print(f"CPT-full: {n_gold} gold files + {n_units} harvested units = "
          f"{len(docs)} docs, ~{chars} chars → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
