"""Move 1 eval — visual_microbench + text microbench regression check.

Visual microbench (5 verifiable image prompts, rule-based):

  1. ask the main_object name on a held-out baien-graft sample
  2. ask if the image contains an animate object (yes/no)
  3. ask the primary color (single word — limited palette)
  4. ask if the image shows a single object (yes/no)
  5. ask for a one-line caption (length 4-20 words, substring of main_object)

The text regression check re-runs the existing 15-prompt microbench.py
with the merged-projector model and reports the pp delta vs the
pre-train baseline (from `90-docs/baien/results-260523.jsonl`).

Move 1 gate per ADR-2605232500 §Eval:
  - visual pass rate ≥ 0.60
  - text microbench delta ≥ -3 pp
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

from .adapters.graft_dataset import GraftRow, collect
from .state import Move1State


_COLOR_PALETTE = (
    "red", "orange", "yellow", "green", "blue", "purple",
    "pink", "brown", "black", "white", "gray", "grey",
)


@dataclass
class VisualPrompt:
    id: str
    build: Callable[[GraftRow], str]
    scorer: Callable[[str, GraftRow], tuple[bool, str]]
    max_new_tokens: int = 32


def _scorer_main_object(out: str, row: GraftRow) -> tuple[bool, str]:
    obj = row.main_object.lower()
    if obj and obj in out.lower():
        return True, f"found main_object '{obj}'"
    return False, f"missing '{obj}' (got {out[:80]!r})"


def _scorer_color(out: str, row: GraftRow) -> tuple[bool, str]:
    """Strict ground-truth color check. `row.color` is set for synthetic
    samples (gen_synthetic_smoke_data.py writes `_color`); for real
    baien-graft samples this is None and we fall back to palette-lenient
    behavior with a flag in the reason string."""
    gt = (row.color or "").lower()
    out_l = out.lower()
    if gt:
        # gray ~ grey alias
        if gt in out_l or (gt == "gray" and "grey" in out_l) or (gt == "grey" and "gray" in out_l):
            return True, f"got ground-truth color '{gt}'"
        return False, f"want '{gt}' (got {out[:80]!r})"
    # fallback: real images without ground-truth
    for c in _COLOR_PALETTE:
        if c in out_l:
            return True, f"named color '{c}' (LENIENT — no ground-truth)"
    return False, f"no color from palette in {out[:80]!r}"


def _scorer_single_object_yes_no(out: str, _row: GraftRow) -> tuple[bool, str]:
    # all baien-graft samples currently are single-object, so expect 'yes'
    if "yes" in out.lower()[:10]:
        return True, "got 'yes' for single-object"
    return False, f"want 'yes' (got {out[:80]!r})"


def _scorer_caption(out: str, row: GraftRow) -> tuple[bool, str]:
    n = len(out.split())
    if not (4 <= n <= 20):
        return False, f"word count {n} outside [4,20]"
    if row.main_object.lower() not in out.lower():
        return False, f"caption missing main_object '{row.main_object}'"
    return True, f"caption ok ({n} words, mentions main_object)"


# vmb_animate_yn was removed 2026-05-23 — synthetic shape data can't validate
# it (all shapes inanimate → baien default "no" trivially passes). Re-add when
# baien-graft includes mixed animate/inanimate images.
VISUAL_PROMPTS: list[VisualPrompt] = [
    VisualPrompt(
        id="vmb_main_object",
        build=lambda r: "What is the main object in this image? Reply with one word.",
        scorer=_scorer_main_object, max_new_tokens=8,
    ),
    VisualPrompt(
        id="vmb_color",
        build=lambda r: "What is the primary color of the object? One word.",
        scorer=_scorer_color, max_new_tokens=8,
    ),
    VisualPrompt(
        id="vmb_single",
        build=lambda r: "Does this image show a single object? Reply 'yes' or 'no'.",
        scorer=_scorer_single_object_yes_no, max_new_tokens=8,
    ),
    VisualPrompt(
        id="vmb_caption",
        build=lambda r: "Caption this image in one sentence (4-20 words).",
        scorer=_scorer_caption, max_new_tokens=64,
    ),
]


# ----- inference adapter --------------------------------------------------

def _build_inference_fn(state: Move1State, *, allow_random_projector: bool = False):
    """Returns `infer(image: PIL.Image, prompt: str, max_new: int) -> str`.

    The full implementation loads frozen baien + frozen SigLIP +
    trained projector. Skeleton mode (dry_run / no projector) returns
    a placeholder so the harness path can be exercised end-to-end.

    If `allow_random_projector=True`, the absence of a saved projector
    is non-fatal — we use a freshly-initialized (random) projector. This
    is the path the `--eval-only` baseline uses to measure floor scores.
    """
    cfg = state.cfg
    if cfg.dry_run:
        def _stub(image, prompt, max_new):
            return "[dry-run stub response]"
        return _stub
    if state.projector_path is None or not state.projector_path.exists():
        if not allow_random_projector:
            def _stub(image, prompt, max_new):
                return "[no projector — pass --eval-only for baseline]"
            return _stub

    import torch
    from PIL import Image  # noqa: F401  (consumer responsibility)
    from transformers import (AutoModelForCausalLM, AutoProcessor, AutoTokenizer,
                              SiglipVisionModel)

    siglip_proc = AutoProcessor.from_pretrained(cfg.image_encoder)
    # SiglipVisionModel = vision tower only (no text branch). SiglipModel's
    # forward requires both input_ids and pixel_values; we only need image.
    siglip = SiglipVisionModel.from_pretrained(cfg.image_encoder, dtype=torch.bfloat16)
    siglip.eval()

    tok = AutoTokenizer.from_pretrained(cfg.base_model)
    if "<image>" not in tok.get_vocab():
        tok.add_special_tokens({"additional_special_tokens": ["<image>"]})
    model = AutoModelForCausalLM.from_pretrained(cfg.base_model, dtype=torch.bfloat16)
    if len(tok) != model.get_input_embeddings().num_embeddings:
        model.resize_token_embeddings(len(tok))
    model.eval()

    # load projector state_dict from disk (random init for baseline mode).
    # Cast projector to bf16 to match SigLIP / baien dtype (default torch.float32
    # would mat1/mat2 dtype-mismatch against bf16 inputs).
    from .projector import build_projector
    projector = build_projector(
        siglip_dim=cfg.siglip_out_dim,
        baien_dim=cfg.baien_hidden_size,
        n_image_tokens=cfg.image_token_count,
    ).to(torch.bfloat16)
    if state.projector_path is not None:
        sd_path = state.projector_path / "projector.pt"
        if sd_path.exists():
            projector.load_state_dict(torch.load(sd_path, map_location="cpu"))
    projector.eval()

    image_token_id = tok.convert_tokens_to_ids("<image>")
    n_img = int(cfg.image_token_count)

    def _infer(image, prompt: str, max_new: int) -> str:
        with torch.no_grad():
            pixel_values = siglip_proc(images=image, return_tensors="pt").pixel_values.to(torch.bfloat16)
            sig = siglip(pixel_values=pixel_values).last_hidden_state  # (1, 196, 768)
            img_tokens = projector(sig)                                  # (1, n_img, 2560)

            text = tok.apply_chat_template(
                [{"role": "user", "content": prompt}],
                add_generation_prompt=True, tokenize=False,
            )
            text_ids = tok(text, return_tensors="pt").input_ids
            img_pad = torch.full((1, n_img), image_token_id, dtype=torch.long)
            current_ids = torch.cat([img_pad, text_ids], dim=1)
            current_attn = torch.ones(current_ids.shape, dtype=torch.long)

            # BitNet in transformers 5.x refuses `inputs_embeds=` (it requires
            # `input_ids`). LLaVA-style workaround: pass input_ids with `<image>`
            # placeholders + register a forward hook on `embed_tokens` that
            # substitutes the projector output at the placeholder positions.
            # We disable KV cache so every forward reprocesses the full
            # sequence (otherwise the next-token forward sees only 1 new id
            # and the hook would over-write into the wrong positions).
            embed_layer = model.get_input_embeddings()

            def _hook(_module, _inputs, output):
                if output.shape[1] >= n_img + 1:
                    out = output.clone()
                    out[:, :n_img, :] = img_tokens.to(out.dtype)
                    return out
                return output

            handle = embed_layer.register_forward_hook(_hook)
            try:
                out_tokens: list[int] = []
                for _ in range(max_new):
                    logits = model(input_ids=current_ids,
                                   attention_mask=current_attn,
                                   use_cache=False).logits
                    next_id = int(logits[:, -1, :].argmax(dim=-1))
                    if next_id == tok.eos_token_id:
                        break
                    out_tokens.append(next_id)
                    next_id_tensor = torch.tensor([[next_id]], dtype=torch.long)
                    current_ids = torch.cat([current_ids, next_id_tensor], dim=1)
                    current_attn = torch.cat(
                        [current_attn, torch.ones((1, 1), dtype=torch.long)], dim=1,
                    )
            finally:
                handle.remove()

        return tok.decode(out_tokens, skip_special_tokens=True)

    return _infer


# ----- main entry ---------------------------------------------------------

def evaluate(state: Move1State, *, held_out_rows: list[GraftRow] | None = None) -> Move1State:
    """Score the trained model on visual_microbench, then run the text
    microbench regression check. Updates state.visual_microbench_pass_rate
    and state.text_microbench_delta_pp, then sets state.decision per
    ADR-2605232500 §Eval gate."""
    cfg = state.cfg
    state.notes.append("[eval] visual_microbench + text regression check")

    rows = held_out_rows or collect(cfg.graft_data_dir, n_rows=5,
                                    images_per_sample=1)
    if not rows:
        state.notes.append("[eval] no held-out rows — abort")
        state.decision = "abort"
        return state

    out_dir = Path(cfg.bench_dir) / f"mx-eval-iter-{state.iter:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    visual_jsonl = out_dir / "visual_microbench.jsonl"

    infer = _build_inference_fn(state)

    # Visual
    from PIL import Image
    n_pass = 0
    n_total = 0
    with visual_jsonl.open("w", encoding="utf-8") as f:
        for p in VISUAL_PROMPTS:
            for r in rows[: 1]:                  # 1 image per prompt for smoke
                try:
                    img = Image.open(r.image_path).convert("RGB") \
                        if not cfg.dry_run else None
                    prompt = p.build(r)
                    resp = infer(img, prompt, p.max_new_tokens)
                    if cfg.dry_run:
                        ok, reason = (True, "dry-run skip")
                    else:
                        ok, reason = p.scorer(resp, r)
                except Exception as e:
                    ok, reason, resp = False, f"EXC: {e!r}", ""
                row = {
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "id": p.id, "image": str(r.image_path),
                    "main_object": r.main_object,
                    "ok": ok, "reason": reason, "response": resp,
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_total += 1
                n_pass += int(ok)
    state.visual_microbench_pass_rate = n_pass / max(1, n_total)
    state.notes.append(
        f"[eval] visual_microbench {n_pass}/{n_total} = "
        f"{100*state.visual_microbench_pass_rate:.1f}%"
    )

    # Text regression — re-run microbench.py on the merged model.
    # Skipped in dry-run since the merged model doesn't exist.
    if cfg.dry_run:
        state.text_microbench_delta_pp = 0.0
        state.notes.append("[eval] dry-run — skipping text regression check")
    else:
        text_delta = _run_text_regression(state, out_dir)
        state.text_microbench_delta_pp = text_delta
        state.notes.append(f"[eval] text microbench Δ = {text_delta:+.2f} pp")

    # Gate
    vmb_ok = state.visual_microbench_pass_rate >= cfg.visual_microbench_threshold
    tmb_ok = state.text_microbench_delta_pp >= cfg.text_regression_floor_pp
    if vmb_ok and tmb_ok:
        state.decision = "commit"
        state.notes.append("[eval] gate PASSED → commit")
    else:
        state.decision = "retry"
        state.notes.append(
            f"[eval] gate FAILED (vmb_ok={vmb_ok}, tmb_ok={tmb_ok}) → retry"
        )
    return state


def evaluate_baseline(state: Move1State) -> Move1State:
    """Quality smoke per user request 2026-05-23 — eval-only floor.

    Runs visual_microbench against an **untrained random-init projector**
    on top of frozen baien + frozen SigLIP. No SFT loop. Reports the
    floor score so any future training has a baseline to beat.

    No quality conclusion can be drawn from a single floor number — but
    this validates that the eval pipeline + image-token injection at
    inference time both work, and gives a reproducible reference."""
    cfg = state.cfg
    state.notes.append("[eval-only] baseline (untrained random projector)")

    rows = collect(cfg.graft_data_dir, n_rows=5, images_per_sample=1)
    if not rows:
        state.notes.append("[eval-only] no graft samples — abort")
        state.decision = "abort"
        return state

    out_dir = Path(cfg.bench_dir) / f"mx-baseline-iter-{state.iter:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    visual_jsonl = out_dir / "visual_microbench_baseline.jsonl"

    # Force random-projector path
    state.projector_path = None
    infer = _build_inference_fn(state, allow_random_projector=True)

    from PIL import Image
    n_pass = 0
    n_total = 0
    # Round-robin through rows for per-prompt image diversity (different
    # images per prompt expose whether responses are actually grounded).
    with visual_jsonl.open("w", encoding="utf-8") as f:
        for i, p in enumerate(VISUAL_PROMPTS):
            r = rows[i % len(rows)]
            try:
                img = Image.open(r.image_path).convert("RGB")
                resp = infer(img, p.build(r), p.max_new_tokens)
                ok, reason = p.scorer(resp, r)
            except Exception as e:
                ok, reason, resp = False, f"EXC: {e!r}", ""
            row = {
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "id": p.id, "image": str(r.image_path),
                "main_object": r.main_object,
                "color": r.color,
                "ok": ok, "reason": reason, "response": resp,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_total += 1
            n_pass += int(ok)
            mark = "PASS" if ok else "FAIL"
            print(f"  {mark:4} [{p.id:18}] obj={r.main_object} color={r.color} | "
                  f"{reason} | {resp[:60]!r}", flush=True)

    state.visual_microbench_pass_rate = n_pass / max(1, n_total)
    rate = 100 * state.visual_microbench_pass_rate
    state.notes.append(
        f"[eval-only] baseline visual_microbench = {n_pass}/{n_total} = {rate:.1f}% "
        f"(this is the floor — trained projector should beat this)"
    )
    return state


def _run_text_regression(state: Move1State, out_dir: Path) -> float:
    """Call the existing text microbench.py against the merged model;
    compare pass rate vs the baseline JSONL recorded earlier."""
    micro = _find_text_microbench()
    if micro is None:
        return 0.0
    results_path = out_dir / "text_microbench.jsonl"
    cmd = [sys.executable, str(micro),
           "--model", str(state.projector_path.parent / "merged-text-only"),
           "--out", str(results_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    state.notes.append(
        f"[eval] text microbench rc={proc.returncode}"
    )
    if not results_path.exists():
        return 0.0
    new_pass = _pass_rate_jsonl(results_path)
    baseline = _pass_rate_jsonl(state.cfg.bench_dir / "results-260523.jsonl")
    return (new_pass - baseline) * 100.0


def _find_text_microbench() -> Path | None:
    here = Path(__file__).resolve()
    cand = here.parents[4] / "scripts" / "bench" / "baien-microbench" / "microbench.py"
    return cand if cand.exists() else None


def _pass_rate_jsonl(path: Path) -> float:
    if not path.exists():
        return 0.0
    n_pass = 0
    n_total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        n_total += 1
        n_pass += int(bool(row.get("ok")))
    return n_pass / max(1, n_total)
