"""(2) fetch_dataset: pull SFT examples from registered sources.

Per ADR-2605250400 §1.3 — three signal sources, all weighted toward
weak categories from analyze():

  1. Local antipattern-corrective JSONL (hand-authored, Apache 2.0)
  2. HF Opus-distilled SFT (Apache 2.0 only)
  3. LangGraph-API-specific synthetic via judah LiteLLM Claude (governance-gated, future)
  4. Harvest from existing first-party LangGraph code in this repo (future)

For iter-00 / quick we enable (1) + (2). (3) and (4) come online
after ADR-2605250400 §3 Step 5.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..state import DistillState, TrainExample

_QWEN_TURN_RX = re.compile(
    r"<\|im_start\|>(system|user|assistant)\n(.*?)<\|im_end\|>",
    re.DOTALL,
)


def _parse_qwen_chat_text(text: str) -> tuple[str | None, str | None]:
    """Parse Qwen `<|im_start|>role\n...<|im_end|>` envelope, return (last_user, last_assistant)."""
    last_user: str | None = None
    last_assistant: str | None = None
    for m in _QWEN_TURN_RX.finditer(text):
        role, content = m.group(1), m.group(2).strip()
        if role == "user":
            last_user = content
        elif role == "assistant" and last_user is not None:
            last_assistant = content
    return last_user, last_assistant

# Apache/MIT-licensed only. license must be reviewed per ADR-2605250400 §2.
# kind: "hf" → datasets.load_dataset(name); "local-jsonl" → read file at path.
DATASET_REGISTRY: list[dict[str, str]] = [
    {
        "kind": "local-jsonl",
        "name": "antipattern-corrective",
        "path": "data/antipattern-corrective.jsonl",  # relative to gemma-coder-distill install root
        "license": "apache-2.0",
        "category": "interrupt+conditional",
        "rows": "20",
        "notes": "Hand-authored fixes for 4 antipatterns detected in gemma4:e4b baseline 2026-05-25",
    },
    {
        "kind": "hf",
        "name": "lordx64/reasoning-distill-opus-4-7-max-sft",
        "format": "qwen-text",
        "license": "apache-2.0",
        "category": "reasoning",
        "rows": "7823",
        "notes": "Opus-distilled general reasoning — indirect Opus signal per ADR-2605231300 §3a; "
                 "single `text` column with Qwen-style <|im_start|>/<|im_end|> envelope",
    },
]


def fetch_dataset(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[fetch] loading registered corpora")

    if state.get("dry_run"):
        state["notes"].append(
            f"[fetch] dry-run — would pull from {len(DATASET_REGISTRY)} sources, "
            f"weak={state.get('weak_categories', [])}"
        )
        # Emit one synthetic example (padded to clear validate's length check) so the rest walks
        state["training_examples"] = [
            TrainExample(
                prompt="dry-run placeholder prompt for pipeline walk-through verification",
                response="dry-run placeholder response",
                source="dry-run", category="dry-run",
            ),
        ]
        state["decision"] = "continue"
        return state

    examples: list[TrainExample] = []
    quick = state.get("quick", False)
    cap = 200 if quick else 5000

    for spec in DATASET_REGISTRY:
        kind = spec.get("kind", "hf")
        try:
            if kind == "local-jsonl":
                rows = _read_local_jsonl(Path(spec["path"]))
            elif kind == "hf":
                rows = _stream_hf(spec["name"], cap, fmt=spec.get("format", "auto"))
            else:
                state["notes"].append(f"[fetch] skip {spec['name']}: unknown kind={kind!r}")
                continue
        except Exception as e:
            state["notes"].append(f"[fetch] skip {spec['name']}: {e!r}")
            continue

        n = 0
        for prompt, response in rows:
            if not prompt or not response:
                continue
            examples.append(TrainExample(
                prompt=str(prompt), response=str(response),
                source=f"{kind}:{spec['name']}", category=spec["category"],
            ))
            n += 1
            if n >= cap:
                break
        state["notes"].append(f"[fetch] {kind}:{spec['name']}: +{n} examples")

    state["training_examples"] = examples
    state["notes"].append(f"[fetch] total examples={len(examples)}")
    state["decision"] = "continue" if examples else "abort"
    return state


def _read_local_jsonl(path: Path):
    if not path.is_absolute():
        # resolve relative to the gemma-coder-distill install root
        # (3 levels up: nodes → gemma_coder_distill → src → gemma-coder-distill)
        install_root = Path(__file__).resolve().parents[3]
        path = install_root / path
    if not path.exists():
        raise FileNotFoundError(f"local-jsonl not found: {path}")
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            yield row.get("prompt"), row.get("response")


def _stream_hf(name: str, cap: int, fmt: str = "auto"):
    """Stream (prompt, response) tuples from a HF dataset.

    fmt:
      - "auto"      try prompt/instruction/question + response/output/answer (default)
      - "qwen-text" single `text` column with Qwen chat envelope (Opus reasoning corpus)
      - "messages"  `messages` list of {role, content}
    """
    from datasets import load_dataset  # type: ignore
    ds = load_dataset(name, split="train", streaming=True)
    seen = 0
    for row in ds:
        if fmt == "qwen-text":
            prompt, response = _parse_qwen_chat_text(row.get("text", "") or "")
        elif fmt == "messages":
            msgs = row.get("messages") or []
            last_u, last_a = None, None
            for m in msgs:
                if m.get("role") == "user":
                    last_u = m.get("content")
                elif m.get("role") == "assistant" and last_u is not None:
                    last_a = m.get("content")
            prompt, response = last_u, last_a
        else:
            prompt = row.get("prompt") or row.get("instruction") or row.get("question")
            response = row.get("response") or row.get("output") or row.get("answer")
        yield prompt, response
        seen += 1
        if seen >= cap * 2:  # over-yield; caller caps
            break
