#!/usr/bin/env python3
"""build_cpt_dataset — gold-corpus の .clj を CPT (継続事前学習) データセットへ整形。

CPT は生テキストの causal-LM 継続学習なので、各 .clj をそのままドキュメントとして
1 行 1 JSON ({"text": "<file 全文>"}) に落とす。SFT (input→output ペア) とは別物 —
ここではモデルに「Clojure / kotoba-Datomic イディオムの分布」を浴びせる。

Usage:
  python3 build_cpt_dataset.py GOLD_DIR OUT.jsonl
  python3 build_cpt_dataset.py ../gold-corpus cpt-gold.jsonl
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: build_cpt_dataset.py GOLD_DIR OUT.jsonl", file=sys.stderr)
        return 2
    gold_dir, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    files = sorted(gold_dir.glob("*.clj"))
    n = 0
    with out_path.open("w", encoding="utf-8") as f:
        for clj in files:
            text = clj.read_text(encoding="utf-8")
            # 軽い header でファイル境界をモデルに示す (パス → 内容)
            doc = f";; file: {clj.name}\n{text}"
            f.write(json.dumps({"text": doc}, ensure_ascii=False) + "\n")
            n += 1
    chars = sum(len(json.loads(l)["text"]) for l in out_path.read_text().splitlines())
    print(f"CPT dataset: {n} docs, ~{chars} chars → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
