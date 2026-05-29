#!/usr/bin/env python3
"""rlvr_train.py — minimal GRPO-style RL with verifiable rewards on MoE adapter.

Group-Relative Policy Optimization (DeepSeek-Math/R1 simplified, on-policy):
  for each prompt p in batch:
    sample G rollouts r_1..r_G from current policy
    reward_g = verifier(p, r_g) in {0, 1}  (binary: passes all tests or not)
    advantage_g = (reward_g - mean_g(reward)) / (std_g(reward) + 1e-4)
    logprob_g = sum log p_theta(token_t | prompt+tokens<t)  over sampled tokens

  loss = -1/(N*G) * sum_{n,g} advantage * logprob_g
       (+ optional β * KL(p_theta || p_ref) — skipped in v0 since adapter is residual
        and α=0 gives reference, but double-forward cost is high; v1 adds KL)

Frozen backbone; only MoE adapter + alpha receive gradients (same param-groups as SFT).

Verifier: MBPP-style. Extract function from generation, run task_id's test list in
subprocess with timeout. reward=1 iff all asserts pass within timeout.

Usage:
  python3 rlvr_train.py \\
    --start-ckpt /workspace/moe-ckpt-c105-ultramem-2048/final.pt \\
    --n-experts 2048 --top-k 8 --expert-kind memory --routing-mode learned \\
    --rl-problems 20 --rollouts 4 --rl-steps 10 \\
    --output-dir /workspace/moe-ckpt-c107-rlvr \\
    --runlog-out /workspace/r2-c107-rlvr.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import torch
import torch.nn.functional as F


def run_one_test(code: str, test_list: list[str], timeout_sec: int = 8) -> bool:
    """Execute candidate `code` then assert each test. True iff all pass within timeout.

    test_list entries look like:  "assert candidate(1, 2) == 3"
    or                            "assert solve([1,2]) == [2,1]"
    so we splice the candidate code first, then the test asserts.
    """
    src = code + "\n\n" + "\n".join(test_list) + "\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(src)
        path = f.name
    try:
        r = subprocess.run(
            ["python3", path],
            timeout=timeout_sec, capture_output=True, text=True,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def extract_python(text: str) -> str:
    """Pull the largest python code block, or raw text if no fence."""
    import re
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if blocks:
        return max(blocks, key=len)
    # Fall back: keep up to first triple-quote/EOS marker
    cutoff = len(text)
    for m in ("```", "<|eot_id|>", "<|end_of_text|>"):
        idx = text.find(m)
        if idx > 0:
            cutoff = min(cutoff, idx)
    return text[:cutoff]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    p.add_argument("--start-ckpt", required=True,
                   help="MoE adapter ckpt to start RLVR from (cycle 105 UltraMem etc.)")
    p.add_argument("--moemoekyun-src", default="/workspace/baien-moemoekyun-train/src")
    p.add_argument("--n-experts", type=int, default=2048)
    p.add_argument("--top-k", type=int, default=8)
    p.add_argument("--expert-hidden-ratio", type=int, default=32)
    p.add_argument("--layers-fraction", type=float, default=0.10)
    p.add_argument("--routing-mode", default="learned", choices=["learned", "distance"])
    p.add_argument("--expert-kind", default="memory", choices=["ffn", "memory"])
    p.add_argument("--rl-dataset", default="mbpp",
                   help="HF dataset name (mbpp uses sanitized split)")
    p.add_argument("--rl-problems", type=int, default=20,
                   help="Number of unique prompts per RL step (small for smoke)")
    p.add_argument("--rollouts", type=int, default=4,
                   help="Generations per prompt (group size G)")
    p.add_argument("--rl-steps", type=int, default=10)
    p.add_argument("--max-new-tokens", type=int, default=256)
    p.add_argument("--temperature", type=float, default=0.7,
                   help="Sampling temperature for rollouts (exploration)")
    p.add_argument("--lr-router", type=float, default=1e-5)
    p.add_argument("--lr-experts", type=float, default=2e-5)
    p.add_argument("--lr-alpha", type=float, default=5e-6)
    p.add_argument("--grad-clip", type=float, default=1.0)
    p.add_argument("--verifier-timeout-sec", type=int, default=8)
    p.add_argument("--kl-beta", type=float, default=0.0,
                   help="KL penalty coefficient β·KL(current||reference). 0 disables (v0 = c108/c111). "
                        "Recommended 0.01-0.1 for v1 stability.")
    p.add_argument("--reference-ckpt", default=None,
                   help="Reference adapter ckpt for KL term (default = start-ckpt itself, snapshotted)")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--runlog-out", required=True)
    args = p.parse_args()

    sys.path.insert(0, args.moemoekyun_src)
    from baien_moemoekyun.attach import attach_moe_to_model, freeze_backbone_verify
    from baien_moemoekyun.trainer import build_optimizer

    device = torch.device("cuda")
    print(f"[env] {torch.cuda.get_device_name(0)}")
    print(f"[env] free VRAM: {torch.cuda.mem_get_info()[0] / 1e9:.2f} GB")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    print(f"[load] {args.model}")
    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16,
                                                 trust_remote_code=False)
    model.to(device)
    print(f"[load] {time.perf_counter()-t0:.1f}s  vram={torch.cuda.memory_allocated()/1e9:.2f} GB")

    cfg = model.config
    n_layers = cfg.num_hidden_layers
    n_moe = max(1, int(round(n_layers * args.layers_fraction)))
    moe_layer_indices = list(range(n_layers - n_moe, n_layers))
    print(f"[moe] attaching layers {moe_layer_indices[0]}..{moe_layer_indices[-1]} ({n_moe}/{n_layers})")

    moe_wrappers = attach_moe_to_model(
        model,
        moe_layer_indices=moe_layer_indices,
        hidden_size=cfg.hidden_size, intermediate_size=cfg.intermediate_size,
        num_experts=args.n_experts, top_k=args.top_k,
        expert_hidden_ratio=args.expert_hidden_ratio, ffn_attribute_name="mlp",
        routing_mode=args.routing_mode, expert_kind=args.expert_kind,
    )
    for w in moe_wrappers.values():
        w.to(device=device, dtype=torch.bfloat16)
    print(f"[moe] routing_mode={args.routing_mode} expert_kind={args.expert_kind}")

    # Load adapter state from start-ckpt
    print(f"[ckpt] loading {args.start_ckpt}")
    sd = torch.load(args.start_ckpt, map_location=device)
    for fqn, wrapper in moe_wrappers.items():
        # state dict written as fqn -> wrapper.state_dict()
        if fqn in sd:
            wrapper.load_state_dict(sd[fqn])
        else:
            print(f"  [warn] {fqn} missing in ckpt, keeping fresh init")

    # Freeze backbone, keep adapter trainable
    freeze_backbone_verify(model, moe_wrappers)
    n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[freeze] trainable params: {n_trainable/1e6:.2f}M")

    # KL reference snapshot — for β·KL(current || reference) regularization in v1
    # Reference = adapter state at start (or external --reference-ckpt).
    # We snapshot once into CPU memory, then swap in/out per rollout for ref logprobs.
    reference_adapter_state = None
    if args.kl_beta > 0:
        ref_src = args.reference_ckpt or args.start_ckpt
        print(f"[kl] β={args.kl_beta}  reference={ref_src}")
        ref_sd = torch.load(ref_src, map_location="cpu")
        reference_adapter_state = {}
        for fqn, wrapper in moe_wrappers.items():
            if fqn in ref_sd:
                reference_adapter_state[fqn] = {k: v.clone().detach()
                                                 for k, v in ref_sd[fqn].items()}
            else:
                print(f"  [warn] reference missing {fqn}, will use current state at step 0 instead")
                reference_adapter_state[fqn] = {k: v.clone().detach().cpu()
                                                  for k, v in wrapper.state_dict().items()}

    opt = build_optimizer(moe_wrappers, lr_router=args.lr_router,
                          lr_experts=args.lr_experts, lr_alpha=args.lr_alpha)

    # Load RL dataset
    from datasets import load_dataset
    print(f"[data] {args.rl_dataset}")
    if args.rl_dataset == "mbpp":
        ds = load_dataset("google-research-datasets/mbpp", "sanitized", split="train")
        problems = [{"prompt": r["prompt"], "test_list": r["test_list"], "task_id": r["task_id"]}
                    for r in ds][: args.rl_problems]
    else:
        raise ValueError(f"unsupported rl_dataset={args.rl_dataset}")
    print(f"[data] {len(problems)} unique RL prompts, {args.rollouts} rollouts each")

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    runlog = {
        "schema": "etzhayyim.baien.rlvr.v1",
        "adr": "ADR-2605262100-RLVR-extension",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "model": args.model,
        "start_ckpt": args.start_ckpt,
        "phase": ("rlvr-grpo-v1-onpolicy-kl-beta" if args.kl_beta > 0
                  else "rlvr-grpo-v0-onpolicy-no-kl"),
        "kl_beta": args.kl_beta,
        "reference_ckpt": (args.reference_ckpt or args.start_ckpt) if args.kl_beta > 0 else None,
        "rl_dataset": args.rl_dataset,
        "rl_problems": args.rl_problems,
        "rollouts": args.rollouts,
        "rl_steps": args.rl_steps,
        "max_new_tokens": args.max_new_tokens,
        "temperature": args.temperature,
        "n_experts": args.n_experts, "top_k": args.top_k,
        "routing_mode": args.routing_mode, "expert_kind": args.expert_kind,
        "trainable_params_count": n_trainable,
        "lr_router": args.lr_router, "lr_experts": args.lr_experts, "lr_alpha": args.lr_alpha,
        "step_metrics": [],
    }

    eos_id = tok.eos_token_id

    for step in range(args.rl_steps):
        t_step = time.perf_counter()
        model.eval()  # rollouts in eval mode (no dropout)

        # Build instruction prompts (chat template, MBPP-style coding task)
        all_prompts_text = []
        for p in problems:
            instruction = (
                f"Write a Python function that solves the following problem. "
                f"Output only the function code in a ```python``` block.\n\n"
                f"Problem: {p['prompt']}\n\n"
                f"Tests this function will be checked against:\n"
                + "\n".join(p["test_list"][:2])
            )
            messages = [{"role": "user", "content": instruction}]
            prompt_text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            all_prompts_text.append(prompt_text)

        # Roll out: G generations per prompt
        rollout_data = []  # list of dicts: prompt_tokens, gen_tokens, reward, prompt_idx
        with torch.no_grad():
            for pi, ptxt in enumerate(all_prompts_text):
                enc = tok(ptxt, return_tensors="pt").to(device)
                prompt_len = enc.input_ids.shape[1]
                for g in range(args.rollouts):
                    out = model.generate(
                        **enc,
                        max_new_tokens=args.max_new_tokens,
                        do_sample=True, temperature=args.temperature,
                        top_p=0.95, pad_token_id=eos_id,
                    )
                    full_ids = out[0]
                    gen_ids = full_ids[prompt_len:].tolist()
                    # Stop at first EOS
                    if eos_id in gen_ids:
                        gen_ids = gen_ids[: gen_ids.index(eos_id)]
                    gen_text = tok.decode(gen_ids, skip_special_tokens=True)
                    code = extract_python(gen_text)
                    passed = run_one_test(code, problems[pi]["test_list"],
                                          timeout_sec=args.verifier_timeout_sec)
                    rollout_data.append({
                        "prompt_idx": pi,
                        "prompt_ids": enc.input_ids[0].tolist(),
                        "gen_ids": gen_ids,
                        "reward": 1.0 if passed else 0.0,
                        "ref_token_logprobs": None,  # filled below if kl_beta > 0
                    })

        # If KL-regularized: compute reference logprobs for every rollout's gen tokens.
        # Swap reference adapter state in, forward, capture, swap current back.
        if reference_adapter_state is not None:
            # Save current adapter state
            current_adapter_state = {
                fqn: {k: v.detach().clone() for k, v in w.state_dict().items()}
                for fqn, w in moe_wrappers.items()
            }
            # Load reference state into wrappers (in-place, keep on device)
            for fqn, wrapper in moe_wrappers.items():
                ref_sd_on_dev = {k: v.to(device=device, dtype=torch.bfloat16)
                                  for k, v in reference_adapter_state[fqn].items()}
                wrapper.load_state_dict(ref_sd_on_dev)
            # Forward each rollout under reference, capture per-token logprobs
            model.eval()
            with torch.no_grad():
                for rd in rollout_data:
                    if len(rd["gen_ids"]) < 2:
                        continue
                    full_ids = rd["prompt_ids"] + rd["gen_ids"]
                    input_ids = torch.tensor([full_ids], dtype=torch.long, device=device)
                    out = model(input_ids=input_ids)
                    logits = out.logits[0]
                    gen_start = len(rd["prompt_ids"])
                    shift_logits = logits[gen_start - 1 : len(full_ids) - 1]
                    ref_logprobs = F.log_softmax(shift_logits.float(), dim=-1)
                    target_tokens = torch.tensor(rd["gen_ids"], dtype=torch.long, device=device)
                    rd["ref_token_logprobs"] = ref_logprobs.gather(
                        -1, target_tokens.unsqueeze(-1)
                    ).squeeze(-1).detach().cpu()
            # Restore current state
            for fqn, wrapper in moe_wrappers.items():
                cur_sd_on_dev = {k: v.to(device=device, dtype=torch.bfloat16)
                                  for k, v in current_adapter_state[fqn].items()}
                wrapper.load_state_dict(cur_sd_on_dev)

        # Compute group-normalized advantage per prompt
        rewards_by_prompt: dict[int, list[float]] = {}
        for rd in rollout_data:
            rewards_by_prompt.setdefault(rd["prompt_idx"], []).append(rd["reward"])
        mean_reward = sum(r["reward"] for r in rollout_data) / max(1, len(rollout_data))
        n_pass = sum(1 for r in rollout_data if r["reward"] > 0.5)
        print(f"[step {step}] rollouts={len(rollout_data)} pass={n_pass}/{len(rollout_data)} "
              f"mean_reward={mean_reward:.3f}")

        for rd in rollout_data:
            grp = rewards_by_prompt[rd["prompt_idx"]]
            mu = sum(grp) / len(grp)
            sd = (sum((x - mu) ** 2 for x in grp) / len(grp)) ** 0.5
            rd["advantage"] = (rd["reward"] - mu) / (sd + 1e-4)

        # Policy update: for each rollout, compute logprob of generated tokens under current model,
        # backprop with -A * logprob
        model.train()
        # Re-enable trainable params (eval mode doesn't change requires_grad but be explicit)
        for w in moe_wrappers.values():
            for p in w.parameters():
                if p.requires_grad:
                    p.requires_grad = True
        opt.zero_grad()
        loss_accum = 0.0
        kl_accum = 0.0
        n_accum = 0
        for rd in rollout_data:
            if abs(rd["advantage"]) < 1e-6 and args.kl_beta == 0:
                continue  # zero advantage AND no KL = no signal
            full_ids = rd["prompt_ids"] + rd["gen_ids"]
            if len(rd["gen_ids"]) < 2:
                continue
            input_ids = torch.tensor([full_ids], dtype=torch.long, device=device)
            out = model(input_ids=input_ids)
            logits = out.logits[0]
            gen_start = len(rd["prompt_ids"])
            target_tokens = torch.tensor(rd["gen_ids"], dtype=torch.long, device=device)
            shift_logits = logits[gen_start - 1 : len(full_ids) - 1]
            logprobs = F.log_softmax(shift_logits.float(), dim=-1)
            token_logprobs = logprobs.gather(-1, target_tokens.unsqueeze(-1)).squeeze(-1)
            avg_lp = token_logprobs.mean()

            # Policy gradient term
            pg_loss = -rd["advantage"] * avg_lp if abs(rd["advantage"]) >= 1e-6 else 0.0 * avg_lp

            # KL term: β · mean_t (current_logprob_t - ref_logprob_t)
            # Approximates KL(current || reference) per-token, sampled at gen positions.
            kl_loss = 0.0 * avg_lp
            if args.kl_beta > 0 and rd["ref_token_logprobs"] is not None:
                ref_lp = rd["ref_token_logprobs"].to(device=device, dtype=token_logprobs.dtype)
                kl_term = (token_logprobs - ref_lp).mean()
                kl_loss = args.kl_beta * kl_term
                kl_accum += float(kl_loss)

            loss_g = pg_loss + kl_loss
            loss_g.backward()
            loss_accum += float(loss_g)
            n_accum += 1

        if n_accum > 0:
            # Gradient clip on trainable params
            torch.nn.utils.clip_grad_norm_(
                [p for p in model.parameters() if p.requires_grad], args.grad_clip
            )
            opt.step()
        wall = time.perf_counter() - t_step
        runlog["step_metrics"].append({
            "step": step, "rollouts": len(rollout_data),
            "n_pass": n_pass, "pass_rate": n_pass / max(1, len(rollout_data)),
            "mean_reward": mean_reward, "loss_accum": loss_accum,
            "kl_accum": kl_accum,
            "n_grad_terms": n_accum, "wall_sec": round(wall, 2),
        })
        print(f"[step {step}] loss={loss_accum:.4f} kl={kl_accum:.4f} grad_terms={n_accum} wall={wall:.1f}s")

    # Save final adapter ckpt
    final_path = Path(args.output_dir) / "final.pt"
    sd = {fqn: w.state_dict() for fqn, w in moe_wrappers.items()}
    torch.save(sd, final_path)
    runlog["checkpoint_final"] = str(final_path)
    runlog["wall_sec_total"] = sum(s["wall_sec"] for s in runlog["step_metrics"])
    Path(args.runlog_out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.runlog_out, "a") as f:
        f.write(json.dumps(runlog, ensure_ascii=False) + "\n")
    print(f"[done] ckpt={final_path}  runlog={args.runlog_out}")
    print(f"[done] total wall {runlog['wall_sec_total']:.1f}s "
          f"final_pass_rate={runlog['step_metrics'][-1]['pass_rate']:.3f}")


if __name__ == "__main__":
    main()
