"""Pull a base model from HF Hub with license-gate enforcement.

Per ADR-2605242000 §License inheritance chain — only Apache-2.0 / MIT
bases pass the auto-gate. Others require an explicit reviewer override
captured in the manifest at commit time.
"""

from __future__ import annotations

from pathlib import Path

from .state import BASE_CANDIDATES, RosoState


PERMISSIVE = {"apache-2.0", "mit", "cc0-1.0", "bsd-2-clause", "bsd-3-clause"}


def pull(state: RosoState) -> RosoState:
    cfg = state.cfg
    if cfg.base_model not in BASE_CANDIDATES:
        state.notes.append(f"[pull] base {cfg.base_model!r} not in BASE_CANDIDATES — abort")
        state.decision = "abort"
        return state

    spec = BASE_CANDIDATES[cfg.base_model]
    if spec["license"] not in PERMISSIVE:
        state.notes.append(
            f"[pull] base {cfg.base_model} license={spec['license']} — non-permissive, "
            f"requires explicit reviewer override at commit_node. Continuing for download "
            f"but commit_node will gate."
        )

    state.base_fp16_size_gb = float(spec["fp16_gb"])

    if cfg.dry_run:
        state.base_local_path = cfg.out_root / "bases" / cfg.base_model.replace("/", "__")
        state.notes.append(
            f"[pull] dry-run — would snapshot_download {cfg.base_model} "
            f"({spec['fp16_gb']} GB FP16) to {state.base_local_path}"
        )
        return state

    from huggingface_hub import snapshot_download
    local = cfg.out_root / "bases" / cfg.base_model.replace("/", "__")
    local.mkdir(parents=True, exist_ok=True)
    state.notes.append(f"[pull] snapshot_download → {local}")
    snapshot_download(repo_id=cfg.base_model, local_dir=local, local_dir_use_symlinks=False)
    state.base_local_path = local
    return state
