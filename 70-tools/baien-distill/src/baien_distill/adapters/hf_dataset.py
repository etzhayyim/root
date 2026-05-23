"""HuggingFace dataset adapter.

Loads SFT-ready public datasets, normalizes their format to TrainExample.

The default category-to-dataset registry mirrors §3a of ADR-2605231300.
Each registry row records the dataset id, license, and *format* tag so
that the loader knows how to extract prompt+response pairs.

Supported format tags:

  - "qwen-text"   single `text` column with the full
                  `<|im_start|>role\\n…<|im_end|>` envelope (e.g.
                  lordx64/reasoning-distill-opus-4-7-max-sft).
  - "messages"    `messages: [{role, content}, ...]` (OpenAI / Tulu).
  - "ifeval"      `prompt` + free-form response in `responses` /
                  `output` (IFEval-style verifiables).
  - "oasst"       OpenAssistant conversation tree
                  (`text`, `role`, `lang`, `parent_id`, `message_id`).
                  Loader walks `parent_id` to assemble user→assistant pairs;
                  supports `lang_filter` to restrict to e.g. "ja".
  - "alpaca"      Alpaca-style `instruction` + optional `input` + `output`
                  (Stanford Alpaca / Dolly-ja).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ..state import TrainExample


@dataclass(frozen=True)
class DatasetSpec:
    id: str                  # HF dataset id, e.g. "lordx64/reasoning-distill-opus-4-7-max-sft"
    license: str             # SPDX-ish: "apache-2.0" / "cc-by-4.0" / "cc-by-sa-3.0" / "odc-by-1.0" / ...
    format: str              # "qwen-text" | "messages" | "ifeval" | "oasst" | "alpaca"
    split: str = "train"     # default split
    note: str = ""           # human note (license caveat, language, etc.)
    lang_filter: str | None = None   # for OASST / multi-lang, keep only this lang code


# Per ADR-2605231300 §3a. Keep small + curated; add datasets via PR.
DATASET_REGISTRY: dict[str, list[DatasetSpec]] = {
    "Reasoning": [
        DatasetSpec(
            id="lordx64/reasoning-distill-opus-4-7-max-sft",
            license="apache-2.0",
            format="qwen-text",
            note="Claude Opus 4.7 extended-thinking traces, 7,823 rows, Qwen3 tokenizer chat template.",
        ),
    ],
    "MMLU": [
        # MMLU itself is not SFT data; rely on the Opus reasoning set as a
        # general STEM uplift instead, until a curated MC distill lands.
    ],
    "IFEval": [
        DatasetSpec(
            id="aisingapore/Instruction-Following-IFEval",
            license="cc-by-4.0",
            format="ifeval",
            note="SEA-IFEval translations; English subset usable, others map to Multilingual.",
        ),
    ],
    "Multilingual": [
        DatasetSpec(
            id="OpenAssistant/oasst1",
            license="apache-2.0",
            format="oasst",
            lang_filter="ja",
            note="OpenAssistant conversation tree; filter to lang=ja for JP carve-out. "
                 "Walks parent_id to assemble user→assistant pairs. ~600 ja rows after filter.",
        ),
        DatasetSpec(
            id="OpenAssistant/oasst2",
            license="apache-2.0",
            format="oasst",
            lang_filter="ja",
            note="oasst2 expands oasst1; ~1.4k ja rows. Same Apache-2.0 terms.",
        ),
        DatasetSpec(
            id="kunishou/databricks-dolly-15k-ja",
            license="cc-by-sa-3.0",
            format="alpaca",
            note="**ShareAlike caveat** — derived weights inherit CC-BY-SA-3.0; "
                 "review per Charter Rider §2 + ADR-2605192200 before publishing. "
                 "OK for internal experimentation. 15k JP instructions, DeepL-translated Dolly.",
        ),
        # Tulu mixture is ODC-BY-1.0 with NC subsets — wire only after a
        # subset-by-subset review per ADR-2605192200. Left empty by design.
    ],
    "General": [
        DatasetSpec(
            id="lordx64/reasoning-distill-opus-4-7-max-sft",
            license="apache-2.0",
            format="qwen-text",
            note="Reuse Opus reasoning as general-quality SFT (high signal).",
        ),
    ],
}


# ----- format parsers -----------------------------------------------------

_QWEN_TURN_RX = re.compile(
    r"<\|im_start\|>(system|user|assistant)\n(.*?)<\|im_end\|>",
    re.DOTALL,
)


def parse_qwen_chat_text(text: str) -> list[dict[str, str]]:
    """Reverse the `<|im_start|>role\\n…<|im_end|>` envelope into
    [{role, content}, ...]. Used to re-apply the *student's* chat template
    (baien has its own tokens; we can't just feed raw Qwen chat to it)."""
    turns: list[dict[str, str]] = []
    for m in _QWEN_TURN_RX.finditer(text):
        role, content = m.group(1), m.group(2).strip()
        turns.append({"role": role, "content": content})
    return turns


def _user_assistant_pair(turns: list[dict[str, str]]) -> tuple[str, str] | None:
    """Pick the last user-prompt + assistant-response pair for SFT."""
    last_user: str | None = None
    last_assistant: str | None = None
    for t in turns:
        if t["role"] == "user":
            last_user = t["content"]
        elif t["role"] == "assistant" and last_user is not None:
            last_assistant = t["content"]
    if last_user is None or last_assistant is None:
        return None
    return last_user, last_assistant


# ----- loader -------------------------------------------------------------

def load_examples(spec: DatasetSpec, category: str, *,
                  limit: int | None = None,
                  hf_token: str | None = None) -> Iterable[TrainExample]:
    """Stream TrainExample from one HF dataset spec.

    `limit=None` loads the full dataset; set a positive int for smoke runs.

    For "oasst" format we first stream-collect rows into an in-memory
    conversation tree, then walk parent_id to extract user→assistant pairs.
    This is more expensive than the row-by-row formats but works on the
    smallest oasst1/2 splits without external state.
    """
    from datasets import load_dataset

    ds = load_dataset(spec.id, split=spec.split, token=hf_token)

    if spec.format == "oasst":
        yield from _oasst_pairs(ds, spec, category, limit=limit)
        return

    yielded = 0
    for row in ds:
        ex = _row_to_example(row, spec, category)
        if ex is None:
            continue
        yield ex
        yielded += 1
        if limit is not None and yielded >= limit:
            break


def _oasst_pairs(ds, spec: DatasetSpec, category: str, *,
                 limit: int | None) -> Iterable[TrainExample]:
    """Walk OpenAssistant tree (message_id + parent_id + role + lang)
    and yield (prompter, assistant) pairs in `spec.lang_filter`."""
    rows: dict[str, dict] = {}
    children: dict[str, list[str]] = {}
    for row in ds:
        mid = row.get("message_id")
        if not mid:
            continue
        if spec.lang_filter and row.get("lang") != spec.lang_filter:
            continue
        rows[mid] = row
        pid = row.get("parent_id")
        if pid:
            children.setdefault(pid, []).append(mid)

    yielded = 0
    for mid, row in rows.items():
        if row.get("role") != "prompter":
            continue
        # take the lowest-rank-number (=best) assistant child if present.
        # Use sentinel comparison rather than `(rank or 99)` because rank=0
        # is the canonical "best" rank and `0 or 99` evaluates to 99.
        def _rank(k: dict) -> int:
            r = k.get("rank")
            return r if isinstance(r, (int, float)) else 99

        asst: dict | None = None
        for kid_id in children.get(mid, []):
            kid = rows.get(kid_id)
            if kid and kid.get("role") == "assistant":
                if asst is None or _rank(kid) < _rank(asst):
                    asst = kid
        if asst is None:
            continue
        prompt = (row.get("text") or "").strip()
        response = (asst.get("text") or "").strip()
        if not prompt or not response:
            continue
        yield TrainExample(
            prompt=prompt, response=response,
            category=category, teacher_model=f"hf:{spec.id}",
            seed=mid,
        )
        yielded += 1
        if limit is not None and yielded >= limit:
            return


def _row_to_example(row: dict, spec: DatasetSpec, category: str) -> TrainExample | None:
    if spec.format == "qwen-text":
        text = row.get("text") or ""
        turns = parse_qwen_chat_text(text)
        pair = _user_assistant_pair(turns)
        if pair is None:
            return None
        prompt, response = pair
        return TrainExample(
            prompt=prompt, response=response,
            category=category, teacher_model=f"hf:{spec.id}",
            seed=None,
        )

    if spec.format == "messages":
        msgs = row.get("messages") or []
        pair = _user_assistant_pair(msgs)
        if pair is None:
            return None
        prompt, response = pair
        return TrainExample(
            prompt=prompt, response=response,
            category=category, teacher_model=f"hf:{spec.id}",
            seed=None,
        )

    if spec.format == "alpaca":
        instr = (row.get("instruction") or "").strip()
        inp = (row.get("input") or "").strip()
        out_str = (row.get("output") or "").strip()
        if not instr or not out_str:
            return None
        prompt = f"{instr}\n\n{inp}" if inp else instr
        return TrainExample(
            prompt=prompt, response=out_str,
            category=category, teacher_model=f"hf:{spec.id}",
            seed=None,
        )

    if spec.format == "ifeval":
        # IFEval rows typically have prompt + verifiable instructions; response
        # is not in the dataset (it's a benchmark). For SFT we need to skip
        # and rely on a separate response source.
        # For now, skip IFEval rows when there's no response field.
        resp = (row.get("response") or row.get("output") or "").strip()
        prompt = (row.get("prompt") or row.get("instruction") or "").strip()
        if not prompt or not resp:
            return None
        return TrainExample(
            prompt=prompt, response=resp,
            category=category, teacher_model=f"hf:{spec.id}",
            seed=None,
        )

    return None
