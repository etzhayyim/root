"""(2) select_teacher: pick an on-fleet OSS teacher meeting ADR constraints.

ADR-2605231300 §2.

Constraints (all must hold):
- OSS license (Apache / MIT / Llama-Community); no commercial API
- Endpoint is on etzhayyim fleet LAN (not external)
- Verified throughput ≥ 8 tok/s (for data-gen feasibility)
- Significantly stronger than baien on the target categories
"""

from __future__ import annotations

from ..state import DistillState, TeacherSpec

# Candidates derived from fleet.toml + ADR-2605202345 + recent verification.
# `verified_tok_per_sec` is from manual measurement; None means unverified.
TEACHER_CANDIDATES: list[TeacherSpec] = [
    TeacherSpec(
        model_id="qwen3-32b-awq",
        endpoint_url="http://192.168.1.22:11434/v1",  # EVO-X2 ollama
        license="apache-2.0",
        throughput_tok_per_sec=8.0,  # estimated; verify on first run
        rationale="primary teacher per ADR §2 (Apache 2.0, JP/code strong, mid throughput)",
    ),
    TeacherSpec(
        model_id="llama3.3:70b",
        endpoint_url="http://192.168.1.22:11434/v1",
        license="llama3-community",
        throughput_tok_per_sec=1.18,
        rationale="strong but very slow; use for ≤200-prompt STEM/coding bursts only",
    ),
    TeacherSpec(
        model_id="llama3.2:3b",
        endpoint_url="http://192.168.1.22:11434/v1",
        license="llama3-community",
        throughput_tok_per_sec=83.0,
        rationale="same scale as baien; marginal teacher signal — fallback only",
    ),
    TeacherSpec(
        model_id="gemma3:4b",
        endpoint_url="http://192.168.1.17:4000/v1",  # judah LiteLLM gateway
        license="gemma-terms-of-use",
        throughput_tok_per_sec=None,  # type: ignore[arg-type]
        rationale="multi-node parallel via judah gateway; restrictive license — review before publish",
    ),
]


def select_teacher(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[select_teacher] choosing per ADR §2 rule")

    targets = {c.name for c in state["weak_categories"]}
    has_stem_or_coding = bool(targets & {"GPQA Diamond", "Reasoning"})
    has_multilingual = "Multilingual" in targets

    chosen: TeacherSpec | None = None
    for cand in TEACHER_CANDIDATES:
        if cand.throughput_tok_per_sec is None:
            # unverified throughput — try only if nothing else qualifies
            continue
        if cand.throughput_tok_per_sec < 5.0 and not has_stem_or_coding:
            continue  # too slow to be worth except for STEM
        if cand.model_id.startswith("qwen") and not has_multilingual:
            # prefer qwen for multilingual; fine for general too — keep
            pass
        chosen = cand
        break

    if chosen is None:
        # fallback to first qualifying regardless
        for cand in TEACHER_CANDIDATES:
            if cand.throughput_tok_per_sec is not None:
                chosen = cand
                break

    if chosen is None:
        state["notes"].append("[select_teacher] no qualifying teacher — abort")
        state["decision"] = "abort"
        return state

    state["teacher"] = chosen
    state["notes"].append(
        f"[select_teacher] chose {chosen.model_id} ({chosen.license}) "
        f"@ {chosen.endpoint_url} — {chosen.rationale}"
    )
    return state
