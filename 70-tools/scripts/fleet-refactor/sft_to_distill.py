#!/usr/bin/env python3
"""fleet-refactor-sft.jsonl → gemma-coder-distill TrainExample jsonl 変換。

ハーネスが収穫する chat-messages 形式 (system/user/assistant + meta) を
70-tools/gemma-coder-distill の train ノードが食う
{prompt, response, source, category} に落とす。

train.py は単一 user turn に chat template を当てるので、system 指示は
user prompt 先頭へ畳み込む (推論時のハーネスと同じ全文が見える)。

Usage:
  python3 sft_to_distill.py fleet-refactor-sft.jsonl > distill-clojure-port.jsonl
"""

from __future__ import annotations

import json
import sys


def convert(line: str) -> dict[str, str] | None:
    r = json.loads(line)
    msgs = {m["role"]: m["content"] for m in r["messages"]}
    if not {"user", "assistant"} <= msgs.keys():
        return None
    prompt = msgs["user"]
    if "system" in msgs:
        prompt = msgs["system"] + "\n\n" + prompt
    return {
        "prompt": prompt,
        "response": msgs["assistant"],
        "source": f"harvest:{r.get('meta', {}).get('src', '?')}"
                  f"@{r.get('meta', {}).get('teacher', '?')}",
        "category": "clojure-port",
    }


def main() -> int:
    n = 0
    for path in sys.argv[1:]:
        for line in open(path, encoding="utf-8"):
            if not line.strip():
                continue
            ex = convert(line)
            if ex:
                print(json.dumps(ex, ensure_ascii=False))
                n += 1
    print(f"converted {n} examples", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
