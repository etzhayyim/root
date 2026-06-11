"""(3-hf) fetch_dataset: sample TrainExample from public HF SFT datasets.

This replaces the (2) select_teacher → (3) generate path when
`state.source == "hf"` (default). It is reachable directly from
analyze via the source-conditional edge in graph.py.

Per ADR-2605231300 §3a. Provenance + license are recorded on each
example so the validate step can enforce Charter Rider §2 + license
inheritance rules.
"""

from __future__ import annotations

from ..adapters.hf_dataset import DATASET_REGISTRY, load_examples
from ..state import DistillState, TrainExample


def fetch_dataset(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[fetch_dataset] pulling from HF registry")

    if state.get("dry_run"):
        state["training_examples"] = []
        state["notes"].append("[fetch_dataset] dry-run — skipping HF load")
        return state

    n_per = state.get("n_per_category", 200)
    all_examples: list[TrainExample] = []
    license_summary: dict[str, int] = {}

    for cat_spec in state["weak_categories"]:
        cat = cat_spec.name
        specs = DATASET_REGISTRY.get(cat, [])
        if not specs:
            state["notes"].append(
                f"[fetch_dataset] no HF dataset registered for {cat} — skip"
            )
            continue

        for spec in specs:
            try:
                got = list(load_examples(spec, cat, limit=n_per))
            except Exception as e:
                state["notes"].append(
                    f"[fetch_dataset] {spec.id} load failed: {e!r}"
                )
                continue
            all_examples.extend(got)
            license_summary[spec.license] = (
                license_summary.get(spec.license, 0) + len(got)
            )
            state["notes"].append(
                f"[fetch_dataset] {spec.id} ({spec.license}): +{len(got)} {cat} rows"
            )
            if len(got) >= n_per:
                break  # next category

    state["training_examples"] = all_examples
    state["notes"].append(
        f"[fetch_dataset] total {len(all_examples)} rows; "
        f"licenses: {license_summary}"
    )

    # If the loop only produced Apache-permissive licenses, nothing to flag.
    # Non-permissive licenses surface as a `pending_license_review` note that
    # the human reviewer must satisfy before commit_node can flip available.
    # CC-BY-* and ODC-BY are permissive *but require attribution*; CC-BY-SA
    # additionally requires the derivative to share alike. Both classes get
    # surfaced to the human reviewer before publish (Charter Rider §2).
    non_permissive = [lic for lic in license_summary
                      if lic not in ("apache-2.0", "mit", "cc0-1.0",
                                     "bsd-2-clause", "bsd-3-clause")]
    if non_permissive:
        state["notes"].append(
            f"[fetch_dataset] pending_license_review for: {non_permissive} "
            f"(per ADR-2605192200 + ADR-2605231300 §license)"
        )
    return state
