"""Mutable state for the LangGraph distill loop.

See ADR-2605231300 §"State shape".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, TypedDict


@dataclass
class CategorySpec:
    name: str                    # e.g. "Multilingual", "Reasoning"
    baien_score: float           # latest pass-rate (0..1)
    frontier_best: float | None  # best from §A of snapshot doc (None if proprietary)
    gap_score: float             # ranking score from analyze.py heuristic
    rationale: str               # human-readable explanation


@dataclass
class TeacherSpec:
    model_id: str                # e.g. "llama3.3:70b"
    endpoint_url: str            # OpenAI-compat base URL
    license: str                 # e.g. "llama3-community", "apache-2.0"
    throughput_tok_per_sec: float
    rationale: str


@dataclass
class TrainExample:
    prompt: str
    response: str
    category: str
    teacher_model: str
    seed: str | None = None
    scorer_spec: dict[str, Any] | None = None  # for IFEval-style verifiables

    def to_jsonl(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "response": self.response,
            "category": self.category,
            "teacher_model": self.teacher_model,
            "seed": self.seed,
            "scorer_spec": self.scorer_spec,
        }


Decision = Literal["pending", "commit", "retry", "abort"]
Source = Literal["hf", "teacher"]


class DistillState(TypedDict, total=False):
    # --- input / configuration ---
    bench_dir: Path                 # 90-docs/baien/
    max_iter: int                   # default 3
    n_per_category: int             # default 200 (ADR §3)
    source: Source                  # "hf" (default, public datasets) | "teacher" (on-fleet OSS gen)
    quick: bool                     # if True: N=50, epochs=1
    dry_run: bool                   # if True: skip teacher inference + training
    student_model_id: str           # override BASE_MODEL_ID (e.g. roso-quantized path)

    # --- mutated during loop ---
    iter: int                       # 0-indexed
    weak_categories: list[CategorySpec]
    teacher: TeacherSpec | None
    training_examples: list[TrainExample]
    lora_path: Path | None
    score_before: dict[str, float]  # category → pass rate (0..1)
    score_after: dict[str, float]
    score_history: list[dict[str, Any]]   # per-iter telemetry
    decision: Decision

    # --- explainability (ReAct trace) ---
    notes: list[str]


def new_state(bench_dir: Path, *, max_iter: int = 3, n_per_category: int = 200,
              source: Source = "hf",
              quick: bool = False, dry_run: bool = False,
              student_model_id: str = "microsoft/bitnet-b1.58-2B-4T-bf16") -> DistillState:
    """Initialize a DistillState for a fresh loop run."""
    if quick:
        n_per_category = min(n_per_category, 50)
    return DistillState(
        bench_dir=bench_dir,
        max_iter=max_iter,
        n_per_category=n_per_category,
        source=source,
        quick=quick,
        dry_run=dry_run,
        student_model_id=student_model_id,
        iter=0,
        weak_categories=[],
        teacher=None,
        training_examples=[],
        lora_path=None,
        score_before={},
        score_after={},
        score_history=[],
        decision="pending",
        notes=[],
    )
