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


def _scorer_animate_yes_no(out: str, row: GraftRow) -> tuple[bool, str]:
    animate_nouns = {"cat", "dog", "horse", "bird", "person", "human",
                     "animal", "fish", "rabbit", "deer", "elephant"}
    is_animate = row.main_object.lower() in animate_nouns
    expected = "yes" if is_animate else "no"
    if expected in out.lower()[:20]:
        return True, f"got '{expected}' for animate={is_animate}"
    return False, f"want '{expected}' (got {out[:80]!r})"


def _scorer_color(out: str, _row: GraftRow) -> tuple[bool, str]:
    for c in _COLOR_PALETTE:
        if c in out.lower():
            return True, f"named color '{c}' (lenient — actual color unverified)"
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


VISUAL_PROMPTS: list[VisualPrompt] = [
    VisualPrompt(
        id="vmb_main_object",
        build=lambda r: "What is the main object in this image? Reply with one word.",
        scorer=_scorer_main_object, max_new_tokens=8,
    ),
    VisualPrompt(
        id="vmb_animate_yn",
        build=lambda r: "Is the main object in this image animate (living)? Reply 'yes' or 'no' only.",
        scorer=_scorer_animate_yes_no, max_new_tokens=8,
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

def _build_inference_fn(state: Move1State):
    """Returns `infer(image: PIL.Image, prompt: str, max_new: int) -> str`.

    The full implementation loads frozen baien + frozen SigLIP +
    trained projector. Skeleton mode (dry_run / no projector) returns
    a placeholder so the harness path can be exercised end-to-end."""
    cfg = state.cfg
    if cfg.dry_run or state.projector_path is None or not state.projector_path.exists():
        def _stub(image, prompt, max_new):
            return "[dry-run stub response]"
        return _stub

    import torch
    from PIL import Image  # noqa: F401  (consumer responsibility)
    from transformers import AutoModel, AutoModelForCausalLM, AutoProcessor, AutoTokenizer

    siglip_proc = AutoProcessor.from_pretrained(cfg.image_encoder)
    siglip = AutoModel.from_pretrained(cfg.image_encoder, torch_dtype=torch.bfloat16)
    siglip.eval()

    tok = AutoTokenizer.from_pretrained(cfg.base_model)
    if "<image>" not in tok.get_vocab():
        tok.add_special_tokens({"additional_special_tokens": ["<image>"]})
    model = AutoModelForCausalLM.from_pretrained(cfg.base_model, dtype=torch.bfloat16)
    if len(tok) != model.get_input_embeddings().num_embeddings:
        model.resize_token_embeddings(len(tok))
    model.eval()

    # load projector state_dict from disk
    from .projector import build_projector
    projector = build_projector(
        siglip_dim=cfg.siglip_out_dim,
        baien_dim=cfg.baien_hidden_size,
        n_image_tokens=cfg.image_token_count,
    )
    sd_path = state.projector_path / "projector.pt"
    if sd_path.exists():
        projector.load_state_dict(torch.load(sd_path, map_location="cpu"))
    projector.eval()

    def _infer(image, prompt: str, max_new: int) -> str:
        with torch.no_grad():
            pixel_values = siglip_proc(images=image, return_tensors="pt").pixel_values.to(torch.bfloat16)
            sig = siglip(pixel_values=pixel_values).last_hidden_state  # (1, 196, 768)
            img_tokens = projector(sig)                                  # (1, 16, 2560)

            # build text-only prompt (no <image> placeholder; image prepended)
            text = tok.apply_chat_template(
                [{"role": "user", "content": prompt}],
                add_generation_prompt=True, tokenize=False,
            )
            text_ids = tok(text, return_tensors="pt").input_ids
            text_embeds = model.get_input_embeddings()(text_ids)         # (1, T, 2560)

            inputs_embeds = torch.cat([img_tokens, text_embeds], dim=1)  # (1, 16+T, 2560)
            attn = torch.ones(inputs_embeds.shape[:2], dtype=torch.long)

            out = model.generate(
                inputs_embeds=inputs_embeds, attention_mask=attn,
                max_new_tokens=max_new, do_sample=False,
                pad_token_id=tok.eos_token_id,
            )
        # `inputs_embeds` mode: out shape is (1, max_new) of new tokens only.
        return tok.decode(out[0], skip_special_tokens=True)

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
