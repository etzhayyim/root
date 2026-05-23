"""(3) generate_training_data: call teacher to produce SFT pairs per category.

ADR-2605231300 §3.
"""

from __future__ import annotations

from ..adapters.ollama_teacher import OllamaTeacher
from ..state import DistillState, TrainExample

# Category-specific prompt templates per ADR §3 table.
GENERATORS: dict[str, str] = {
    "IFEval": (
        "Generate one instruction with a precise machine-checkable constraint "
        "(format / count / case / keyword / structure), followed by a single "
        "compliant response. Output JSON: {\"prompt\": <str>, \"response\": "
        "<str>, \"constraint_type\": <str>}.\n"
        "The constraint must be exactly verifiable by a regex or simple parser."
    ),
    "MMLU": (
        "Generate one 4-choice exam-style question on subject {seed_subject}. "
        "Output JSON: {\"q\": <str>, \"A\": <str>, \"B\": <str>, \"C\": <str>, "
        "\"D\": <str>, \"correct\": \"A\"|\"B\"|\"C\"|\"D\", "
        "\"explanation\": <one-sentence>}."
    ),
    "Reasoning": (
        "Generate one GSM8K-difficulty word problem and a step-by-step solution. "
        "End the solution with 'Answer: <number>'. "
        "Output JSON: {\"problem\": <str>, \"solution\": <str>, \"answer\": <number>}."
    ),
    "Multilingual": (
        "Translate the following English sentence into natural Japanese. "
        "Output JSON: {\"en\": <str>, \"ja\": <str>}.\n"
        "English: {seed_en}"
    ),
    "General": (
        "Generate one brief factual question and a one-sentence answer. "
        "Output JSON: {\"q\": <str>, \"a\": <str>}."
    ),
}

# Subject seeds for MMLU (subset of the 57 MMLU subjects).
MMLU_SUBJECTS = [
    "elementary_mathematics", "high_school_biology", "high_school_chemistry",
    "high_school_physics", "world_history", "global_facts",
    "computer_security", "machine_learning", "formal_logic", "moral_disputes",
]


def generate_training_data(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append(
        "[generate] teacher calls per category"
    )

    if state.get("dry_run"):
        state["training_examples"] = []
        state["notes"].append("[generate] dry-run — skipping teacher calls")
        return state

    teacher_spec = state["teacher"]
    if teacher_spec is None:
        state["notes"].append("[generate] no teacher — abort")
        state["decision"] = "abort"
        return state

    client = OllamaTeacher(
        base_url=teacher_spec.endpoint_url,
        model_id=teacher_spec.model_id,
    )

    n_per = state.get("n_per_category", 200)
    all_examples: list[TrainExample] = []

    for cat_spec in state["weak_categories"]:
        cat = cat_spec.name
        template = GENERATORS.get(cat)
        if template is None:
            state["notes"].append(f"[generate] no template for {cat} — skip")
            continue

        for i in range(n_per):
            seed = _seed_for(cat, i)
            prompt = template.format(**seed) if seed else template
            try:
                text = client.complete(prompt, max_tokens=512, temperature=0.7)
            except Exception as e:
                state["notes"].append(f"[generate] {cat} {i}: teacher err {e!r}")
                continue
            ex = TrainExample(
                prompt=prompt,
                response=text,
                category=cat,
                teacher_model=teacher_spec.model_id,
                seed=str(seed) if seed else None,
            )
            all_examples.append(ex)

    state["training_examples"] = all_examples
    state["notes"].append(
        f"[generate] produced {len(all_examples)} raw examples across "
        f"{len(state['weak_categories'])} categories"
    )
    return state


def _seed_for(category: str, index: int) -> dict | None:
    if category == "MMLU":
        return {"seed_subject": MMLU_SUBJECTS[index % len(MMLU_SUBJECTS)]}
    if category == "Multilingual":
        # TODO: feed from existing WMT24++ corpus / RisingWave v_training_text
        seeds = [
            "The cat sat on the mat.",
            "Renewable energy adoption is accelerating worldwide.",
            "Reading reduces stress and improves vocabulary.",
        ]
        return {"seed_en": seeds[index % len(seeds)]}
    return None
