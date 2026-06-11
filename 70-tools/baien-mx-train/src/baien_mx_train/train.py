"""Move 1 image graft trainer.

Skeleton — implements the wiring + dry-run path completely; the heavy
training loop is gated behind `cfg.dry_run` so the smoke run can be
validated before we sink ROCm GPU time into Phase A.

Heavily mirrors `70-tools/baien-distill/src/baien_distill/nodes/train.py`
(ADR-2605231300 §5), with the additions:

  - frozen SigLIP image encoder
  - 1.58-bit Move1Projector trainable
  - image-token injection collator
  - `<image>` special token added to baien tokenizer
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

from .adapters.graft_dataset import GraftRow, collect
from .projector import build_projector, count_trainable
from .state import Move1Config, Move1State, resolve_phase

IMAGE_PLACEHOLDER_TOKEN = "<image>"


def train(state: Move1State) -> Move1State:
    cfg = state.cfg
    state.notes.append(f"[mx-train] phase={cfg.phase} dry_run={cfg.dry_run}")

    phase = resolve_phase(cfg)
    state.notes.append(
        f"[mx-train] target n_samples={phase['n_samples']} epochs={phase['epochs']}"
    )

    # Stage 1: harvest training rows from baien-graft sample.json tree
    rows = collect(cfg.graft_data_dir, n_rows=phase["n_samples"],
                   images_per_sample=cfg.images_per_sample)
    if not rows and not cfg.dry_run:
        state.notes.append(
            f"[mx-train] no graft samples found under {cfg.graft_data_dir} — abort"
        )
        state.decision = "abort"
        return state
    state.n_train_rows = len(rows)
    state.notes.append(f"[mx-train] collected {len(rows)} (image, caption) rows")

    iter_dir = cfg.out_root / f"mx-move1-iter-{state.iter:02d}"
    iter_dir.mkdir(parents=True, exist_ok=True)

    # Persist the training manifest so checkpoint lineage can hash-pin it.
    train_jsonl = iter_dir / "train.jsonl"
    _write_manifest(train_jsonl, rows)
    state.train_jsonl_path = train_jsonl
    state.train_dataset_hash = _sha256(train_jsonl)

    if cfg.dry_run:
        state.projector_path = iter_dir / "projector_dryrun"
        _write_checkpoint_row(iter_dir, cfg, state, final_loss=None,
                              status="dry-run")
        state.notes.append(
            f"[mx-train] dry-run — manifest hashed ({state.train_dataset_hash[:8]}), "
            f"skipping SigLIP / baien load + training"
        )
        return state

    # ─── Real training path (gated behind dry_run=False) ──────────────
    import torch
    from torch.optim import AdamW

    # Pick the best available device. transformers ROCm reports as "cuda".
    device = "cuda" if torch.cuda.is_available() else "cpu"
    state.notes.append(f"[mx-train] device = {device}")

    # frozen image encoder (vision-only tower; SiglipModel needs text too)
    from transformers import (AutoProcessor, AutoModelForCausalLM, AutoTokenizer,
                              SiglipVisionModel)
    siglip_proc = AutoProcessor.from_pretrained(cfg.image_encoder)
    siglip = SiglipVisionModel.from_pretrained(cfg.image_encoder, dtype=torch.bfloat16).to(device)
    siglip.eval()
    for p in siglip.parameters():
        p.requires_grad = False

    # frozen baien trunk + add <image> special token
    tok = AutoTokenizer.from_pretrained(cfg.base_model)
    if IMAGE_PLACEHOLDER_TOKEN not in tok.get_vocab():
        tok.add_special_tokens({"additional_special_tokens": [IMAGE_PLACEHOLDER_TOKEN]})
    model = AutoModelForCausalLM.from_pretrained(cfg.base_model, dtype=torch.bfloat16).to(device)
    if len(tok) != model.get_input_embeddings().num_embeddings:
        model.resize_token_embeddings(len(tok))
    model.eval()
    for p in model.parameters():
        p.requires_grad = False

    # trainable projector (bf16 to match SigLIP / baien dtypes)
    projector = build_projector(
        siglip_dim=cfg.siglip_out_dim,
        baien_dim=cfg.baien_hidden_size,
        n_image_tokens=cfg.image_token_count,
    ).to(torch.bfloat16).to(device)
    n_train = count_trainable(projector)
    state.notes.append(f"[mx-train] projector trainable params = {n_train:,}")

    opt = AdamW(projector.parameters(), lr=cfg.lr)

    # ─── SFT loop ─────────────────────────────────────────────────────
    # LLaVA-style "prepended image tokens" pattern (ADR-2605232500
    # §Architecture, simplified — no `<image>` placeholder in text;
    # image tokens always come first, then chat-template-formatted
    # user/assistant turn):
    #
    #   inputs_embeds = [img_tokens (B, 16, D); text_embeds (B, T, D)]
    #   labels        = [-100 × 16            ; -100 × n_prompt ; resp_ids]
    #   attn_mask     = ones across (16 + T)
    #
    # Loss is cross-entropy on the assistant turn only; everything else
    # is masked to -100.
    from PIL import Image
    from transformers import AutoProcessor
    siglip_proc = AutoProcessor.from_pretrained(cfg.image_encoder)
    eos_id = int(tok.eos_token_id)
    n_img = int(cfg.image_token_count)

    phase_cfg = resolve_phase(cfg)
    epochs = int(phase_cfg["epochs"])
    grad_accum = int(cfg.grad_accum)

    losses: list[float] = []
    step = 0
    projector.train()
    state.notes.append(
        f"[mx-train] entering SFT loop: n_rows={len(rows)} epochs={epochs} "
        f"grad_accum={grad_accum}"
    )

    for ep in range(epochs):
        opt.zero_grad()
        for i, row in enumerate(rows):
            image = Image.open(row.image_path).convert("RGB")
            pixel_values = siglip_proc(
                images=image, return_tensors="pt"
            ).pixel_values.to(torch.bfloat16).to(device)

            with torch.no_grad():
                sig_out = siglip(pixel_values=pixel_values).last_hidden_state  # (1, 196, 768)
            img_tokens = projector(sig_out)  # (1, n_img, 2560)

            # build chat-template-formatted prompt + response, separately,
            # so we can compute the labels (only response tokens contribute).
            user_text = "What is the main object in this image?"
            response_text = row.main_object
            prompt_str = tok.apply_chat_template(
                [{"role": "user", "content": user_text}],
                add_generation_prompt=True, tokenize=False,
            )
            full_str = prompt_str + response_text + tok.eos_token

            prompt_ids = tok(prompt_str, return_tensors="pt", add_special_tokens=False).input_ids.to(device)
            full_ids = tok(full_str, return_tensors="pt", add_special_tokens=False).input_ids.to(device)
            n_prompt = int(prompt_ids.shape[1])
            n_full = int(full_ids.shape[1])

            text_embeds = model.get_input_embeddings()(full_ids)  # (1, T, 2560)
            inputs_embeds = torch.cat([img_tokens, text_embeds], dim=1)  # (1, 16+T, 2560)

            labels = full_ids.clone()
            labels[:, :n_prompt] = -100   # mask prompt
            # prepend -100 for image tokens (they don't contribute to loss)
            img_label_pad = torch.full((1, n_img), -100, dtype=labels.dtype, device=device)
            labels = torch.cat([img_label_pad, labels], dim=1)

            attn = torch.ones(inputs_embeds.shape[:2], dtype=torch.long, device=device)

            outputs = model(
                inputs_embeds=inputs_embeds,
                attention_mask=attn,
                labels=labels,
                use_cache=False,
            )
            loss = outputs.loss / grad_accum
            loss.backward()

            if (i + 1) % grad_accum == 0 or (i + 1) == len(rows):
                opt.step()
                opt.zero_grad()
                step += 1
                losses.append(float(outputs.loss.detach()))
                if step <= 5 or step % 10 == 0:
                    state.notes.append(
                        f"[mx-train] ep={ep} step={step} loss={losses[-1]:.4f}"
                    )

    state.final_loss = sum(losses[-min(10, len(losses)):]) / max(1, min(10, len(losses)))
    state.notes.append(
        f"[mx-train] SFT done. final_loss (last≤10 mean) = {state.final_loss:.4f}"
    )

    # Persist projector state_dict + a separate "merged-text-only" dir for
    # the text-microbench regression check (where the merged model behaves
    # like baien-text since no image tokens are present).
    adapter_dir = iter_dir / "projector"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    torch.save(projector.state_dict(), adapter_dir / "projector.pt")
    state.projector_path = adapter_dir
    # save the (resized-vocab) base model + tokenizer once so eval's
    # text-only path can load it without re-resizing.
    txt_dir = iter_dir / "merged-text-only"
    txt_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(txt_dir))
    tok.save_pretrained(str(txt_dir))

    _write_checkpoint_row(iter_dir, cfg, state,
                          final_loss=state.final_loss, status="trained")
    return state


def _write_manifest(path: Path, rows: list[GraftRow]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({
                "image_path": str(r.image_path),
                "caption": r.caption,
                "main_object": r.main_object,
                "source_sample": r.source_sample,
            }, ensure_ascii=False) + "\n")


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _write_checkpoint_row(out_dir: Path, cfg: Move1Config,
                          state: Move1State, *, final_loss: float | None,
                          status: str) -> None:
    row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": "baien-mx-move1-projector",
        "parent_kind": "bitnet-b1.58-2B-4T-bf16",
        "image_encoder": cfg.image_encoder,
        "status": status,
        "phase": cfg.phase,
        "n_train_rows": state.n_train_rows,
        "dataset_hash": state.train_dataset_hash,
        "lr": cfg.lr,
        "warmup_steps": cfg.warmup_steps,
        "per_device_batch": cfg.per_device_batch,
        "grad_accum": cfg.grad_accum,
        "image_token_count": cfg.image_token_count,
        "final_loss": final_loss,
        "iter": state.iter,
    }
    (out_dir / "vertex_training_checkpoint.json").write_text(
        json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8"
    )
