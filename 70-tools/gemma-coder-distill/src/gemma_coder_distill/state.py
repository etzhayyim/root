"""DistillState — shared TypedDict across LangGraph nodes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict


@dataclass
class TrainExample:
    prompt: str
    response: str
    source: str  # "hf:<dataset>" / "harvest:<repo-path>" / "synthetic:judah"
    category: str  # langgraph-coding category (stategraph / reducer / ...)

    def to_jsonl(self) -> dict[str, str]:
        return {
            "prompt": self.prompt,
            "response": self.response,
            "source": self.source,
            "category": self.category,
        }


class DistillState(TypedDict, total=False):
    bench_dir: Path
    max_iter: int
    quick: bool
    dry_run: bool
    iter: int
    student_model_id: str

    baseline_pass_pct: float
    weak_categories: list[str]
    training_examples: list[TrainExample]
    lora_path: Path
    new_pass_pct: float
    delta_pp: float

    decision: str  # "continue" / "commit" / "abort"
    notes: list[str]


def init_state(*, bench_dir: Path, max_iter: int, quick: bool, dry_run: bool,
               student_model_id: str) -> DistillState:
    return DistillState(
        bench_dir=bench_dir,
        max_iter=max_iter,
        quick=quick,
        dry_run=dry_run,
        iter=0,
        student_model_id=student_model_id,
        notes=[],
    )
