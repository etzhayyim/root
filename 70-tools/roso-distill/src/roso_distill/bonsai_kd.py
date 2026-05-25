"""Multi-epoch logit-KL knowledge distillation for 1-bit quantization.

Implements the MISSING STEP from Bonsai-8B paper — Phase B+C+D (calibrate)
yields exact_match 0/15 on Qwen3-1.7B (wall 4 confirmed); paper's ~89%
retention requires this post-quantization distillation step.

Pipeline:
  1. Load teacher = original bf16 Qwen3 (no_grad)
  2. Build student = same Qwen3, but every Linear (except embed/lm_head) is
     wrapped in TrainableBinaryLinear (master_weight fp32 + per-row α + STE)
  3. α initialized from `calibrated_alphas.json` (Phase C optimal scale)
  4. Train with KL(student || teacher) on small text corpus (wikitext-2)
  5. Save master_weights + alphas
  6. Re-pack via pack_calibrated → packed checkpoint
  7. packed_minibench → expect exact_match >> 0
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F


# Same skip set as bonsai_calibrate Phase C
SKIP_FOR_KD = ("embed_tokens", "lm_head", "router", "gate.weight", "mtp")


class TrainableBinaryLinear(nn.Module):
    """1-bit Linear with master weights (fp32) and per-row α, STE backward."""

    def __init__(self, master_init: torch.Tensor, alpha_init: torch.Tensor):
        super().__init__()
        # master_weight [d_out, d_in] fp32 trainable
        self.master_weight = nn.Parameter(master_init.to(torch.float32))
        # alpha [d_out] fp32 trainable
        self.alpha = nn.Parameter(alpha_init.to(torch.float32))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Quantize: sign(master) * α per row
        w_q = torch.sign(self.master_weight) * self.alpha.view(-1, 1)
        # STE: forward = w_q (1-bit), backward grad flows through master
        w_q = self.master_weight + (w_q - self.master_weight).detach()
        return F.linear(x, w_q.to(x.dtype), None)

    @property
    def out_features(self) -> int:
        return self.master_weight.shape[0]

    @property
    def in_features(self) -> int:
        return self.master_weight.shape[1]


def replace_linears_with_trainable(model: nn.Module,
                                    calibrated_alphas: dict[str, list]) -> tuple[int, int]:
    """Replace nn.Linear with TrainableBinaryLinear, init α from Phase C dict.

    Returns (n_replaced, n_skipped_no_alpha).
    """
    n_replaced = 0
    n_no_alpha = 0
    # Collect first to avoid mutating during iteration
    targets = []
    for name, mod in model.named_modules():
        if not isinstance(mod, nn.Linear):
            continue
        if any(s in name for s in SKIP_FOR_KD):
            continue
        targets.append((name, mod))

    for name, mod in targets:
        # Init α from calibrated dict (try both prefix conventions)
        alpha_list = (calibrated_alphas.get(name)
                       or calibrated_alphas.get(name.replace("model.", "", 1))
                       or calibrated_alphas.get("model." + name))
        if alpha_list is None:
            # Fallback: init α = mean(|W|) per row
            alpha = mod.weight.abs().mean(dim=-1).detach()
            n_no_alpha += 1
        else:
            alpha = torch.tensor(alpha_list, dtype=torch.float32)
            if alpha.shape[0] != mod.weight.shape[0]:
                # mismatched shape — fall back
                alpha = mod.weight.abs().mean(dim=-1).detach()
                n_no_alpha += 1

        new_mod = TrainableBinaryLinear(mod.weight.detach().clone(), alpha)

        # Navigate to parent + setattr
        parent_path, attr = name.rsplit(".", 1)
        parent = model.get_submodule(parent_path)
        setattr(parent, attr, new_mod)
        n_replaced += 1

    return n_replaced, n_no_alpha


def make_dataset(tokenizer, n_samples: int, seq_len: int):
    """Build a small text dataset (wikitext-2 if available, else fall back to
    calibration prompts from bonsai_calibrate)."""
    try:
        from datasets import load_dataset
        ds = load_dataset("wikitext", "wikitext-2-raw-v1", split="train",
                          streaming=False)
        rows = []
        for row in ds:
            t = row.get("text", "")
            if len(t.strip()) > 100:
                rows.append(t)
            if len(rows) >= n_samples:
                break
        print(f"[kd] wikitext-2 loaded {len(rows)} rows >100 chars", flush=True)
    except Exception as e:
        print(f"[kd] wikitext-2 load failed ({e!r}); using fallback prompts", flush=True)
        from .bonsai_calibrate import DEFAULT_CALIB_PROMPTS
        rows = (DEFAULT_CALIB_PROMPTS * (n_samples // len(DEFAULT_CALIB_PROMPTS) + 1))[:n_samples]

    # Pre-tokenize
    encoded = []
    for txt in rows:
        ids = tokenizer(txt, return_tensors="pt", truncation=True,
                       max_length=seq_len).input_ids
        if ids.shape[1] >= 32:    # skip tiny ones
            encoded.append(ids)
    print(f"[kd] tokenized {len(encoded)} samples (>=32 tokens)", flush=True)
    return encoded


def kd_step(teacher, student, input_ids: torch.Tensor, T: float) -> torch.Tensor:
    """One KD step. Returns the scalar loss (with backward implicit)."""
    with torch.no_grad():
        teacher_logits = teacher(input_ids).logits   # [B, T, V]
    student_logits = student(input_ids).logits

    # KL(student || teacher) with temperature
    # Standard KD: KL(softmax(t_logits/T), softmax(s_logits/T)) * T^2
    log_p_s = F.log_softmax(student_logits / T, dim=-1)
    p_t = F.softmax(teacher_logits / T, dim=-1)
    loss = F.kl_div(log_p_s, p_t, reduction="batchmean") * (T * T)
    return loss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orig-ckpt", required=True, type=Path,
                    help="Original bf16 base (= teacher)")
    ap.add_argument("--calibrated-dir", required=True, type=Path,
                    help="Phase B+C+D output dir (provides calibrated_alphas.json)")
    ap.add_argument("--out", required=True, type=Path,
                    help="Output dir for trained student master_weights + alphas")
    ap.add_argument("--n-samples", type=int, default=200,
                    help="Training samples from wikitext-2")
    ap.add_argument("--seq-len", type=int, default=512)
    ap.add_argument("--n-epochs", type=int, default=1)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--temperature", type=float, default=2.0)
    ap.add_argument("--save-every", type=int, default=50)
    ap.add_argument("--max-steps", type=int, default=0,
                    help="If >0, cap training to this many steps")
    ap.add_argument("--resume-from", type=Path, default=None,
                    help="If set, load student master_weight + α from this prior "
                         "KD output dir (uses per_shard/kd_step.safetensors.W_q.safetensors "
                         "+ calibrated_alphas.json) instead of Phase C init")
    args = ap.parse_args()

    from transformers import AutoModelForCausalLM, AutoTokenizer

    args.out.mkdir(parents=True, exist_ok=True)

    print(f"[kd] tokenizer + teacher (bf16)", flush=True)
    tok = AutoTokenizer.from_pretrained(args.orig_ckpt)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    teacher = AutoModelForCausalLM.from_pretrained(
        args.orig_ckpt, dtype=torch.bfloat16)
    teacher.eval()
    for p in teacher.parameters():
        p.requires_grad_(False)

    print(f"[kd] student (= teacher init, then replace Linears with TrainableBinaryLinear)",
          flush=True)
    student = AutoModelForCausalLM.from_pretrained(
        args.orig_ckpt, dtype=torch.bfloat16)
    # Load Phase C calibrated alphas
    calib_alphas_path = args.calibrated_dir / "calibrated_alphas.json"
    if not calib_alphas_path.exists():
        raise FileNotFoundError(f"Missing {calib_alphas_path}; run bonsai_calibrate.py first")
    calib_alphas = json.loads(calib_alphas_path.read_text(encoding="utf-8"))
    print(f"[kd] loaded {len(calib_alphas)} calibrated α dicts", flush=True)

    n_repl, n_no_a = replace_linears_with_trainable(student, calib_alphas)
    print(f"[kd] replaced {n_repl} Linears with TrainableBinaryLinear "
          f"(no-α fallback: {n_no_a})", flush=True)

    # Resume from prior KD run if requested — overwrite master_weight + α
    # with the saved KD-trained values (recover student state without rerunning Phase C).
    if args.resume_from is not None:
        from safetensors.torch import load_file
        rwq = args.resume_from / "per_shard" / "kd_step.safetensors.W_q.safetensors"
        rdict = load_file(str(rwq))
        ralphas = json.loads(
            (args.resume_from / "calibrated_alphas.json").read_text(encoding="utf-8"))
        n_restored = 0
        for name, mod in student.named_modules():
            if not isinstance(mod, TrainableBinaryLinear):
                continue
            wq_key = f"{name}.W_q"
            if wq_key in rdict and name in ralphas:
                # master_weight = W_q (= sign(prev_master) * α) is a fine init;
                # subsequent training continues from this signed state
                with torch.no_grad():
                    mod.master_weight.copy_(rdict[wq_key].to(torch.float32))
                    mod.alpha.copy_(torch.tensor(ralphas[name], dtype=torch.float32))
                n_restored += 1
        print(f"[kd] RESUMED from {args.resume_from}: restored {n_restored} TrainableBinaryLinears",
              flush=True)

    # Freeze everything NOT in a TrainableBinaryLinear so optimizer only
    # updates the master_weight + α (embed/lm_head/norms stay teacher-exact)
    n_frozen = 0
    n_train = 0
    for name, p in student.named_parameters():
        if ".master_weight" in name or ".alpha" in name:
            p.requires_grad_(True)
            n_train += 1
        else:
            p.requires_grad_(False)
            n_frozen += 1
    print(f"[kd] froze {n_frozen} non-binary params, training {n_train} master+α params",
          flush=True)

    # Dataset
    dataset = make_dataset(tok, args.n_samples, args.seq_len)

    # Optimizer over student parameters
    opt = torch.optim.AdamW(
        [p for p in student.parameters() if p.requires_grad],
        lr=args.lr, betas=(0.9, 0.95), weight_decay=0.0)
    print(f"[kd] AdamW lr={args.lr}, "
          f"trainable params={sum(p.numel() for p in student.parameters() if p.requires_grad)/1e9:.2f}B",
          flush=True)

    student.train()
    step = 0
    t0 = time.time()
    losses = []
    for epoch in range(args.n_epochs):
        for sample_idx, input_ids in enumerate(dataset):
            if args.max_steps > 0 and step >= args.max_steps:
                break
            ts0 = time.time()
            loss = kd_step(teacher, student, input_ids, T=args.temperature)
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(float(loss.item()))
            dt = time.time() - ts0
            step += 1
            print(f"[kd] ep{epoch} step{step}/{len(dataset)*args.n_epochs} "
                  f"sample={sample_idx} ids={tuple(input_ids.shape)} "
                  f"loss={float(loss):.4f} ({dt:.1f}s)", flush=True)

            if step % args.save_every == 0:
                _save_checkpoint(student, args.out, step, losses)
        if args.max_steps > 0 and step >= args.max_steps:
            break

    total = time.time() - t0
    print(f"\n[kd] DONE {step} steps in {total/60:.1f} min, "
          f"final loss={losses[-1]:.4f} (smoothed last-10 avg={sum(losses[-10:])/min(10,len(losses)):.4f})",
          flush=True)
    _save_checkpoint(student, args.out, step, losses)


def _save_checkpoint(student, out_dir: Path, step: int, losses: list):
    """Save TrainableBinaryLinear master_weights + alphas as Phase D-compatible
    output that pack_calibrated.py can consume.

    Writes:
      - per_shard/student_step{N}.safetensors — single file with all `master.W_q` (sign×α) and α
      - calibrated_alphas.json — current α values
      - kd_loss_curve.jsonl — append-only loss log
    """
    from safetensors.torch import save_file
    per_shard_dir = out_dir / "per_shard"
    per_shard_dir.mkdir(parents=True, exist_ok=True)

    # Collect W_q + alphas for all TrainableBinaryLinears
    wq_dict = {}
    alpha_dict = {}
    for name, mod in student.named_modules():
        if not isinstance(mod, TrainableBinaryLinear):
            continue
        with torch.no_grad():
            w_q = torch.sign(mod.master_weight) * mod.alpha.view(-1, 1)
            wq_dict[f"{name}.W_q"] = w_q.to(torch.bfloat16).cpu()
            alpha_dict[name] = mod.alpha.cpu().tolist()
    # Save single file (matches pack_calibrated's single-shard expectation)
    save_file(wq_dict, str(per_shard_dir / "kd_step.safetensors.W_q.safetensors"))
    (out_dir / "calibrated_alphas.json").write_text(
        json.dumps(alpha_dict), encoding="utf-8")
    # Loss curve
    with (out_dir / "kd_loss_curve.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "step": step,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "loss_recent_10_avg": sum(losses[-10:]) / min(10, len(losses)),
            "loss_last": losses[-1] if losses else None,
            "n_linears_saved": len(wq_dict),
        }) + "\n")
    print(f"  [save] step={step} wrote {len(wq_dict)} W_q tensors + α dict", flush=True)


if __name__ == "__main__":
    main()
