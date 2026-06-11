#!/usr/bin/env python3
"""MoE-aware LoRA target resolver for gemma-4-26B-A4B (ADR-2605302359 §2).

The QLoRA target set is chosen from the expert-activation profiling:
  - TRAIN: attention q/k/v/o + the SHARED/dense FFN (gate/up/down) — 535M,
    always-active, highest leverage per adapter param.
  - FREEZE: the 128 routed experts (`*.experts.*`, 22.84B) — the knowledge mass.
  - ROUTER (`mlp.gate` / `gate_inp`): optional, low-rank, OFF by default
    (training it risks expert collapse; the profiler is the guardrail).

CRITICAL: `gate_proj` / `up_proj` / `down_proj` appear in BOTH the shared FFN
AND inside every routed expert. peft matches target_modules by name-suffix, so
naming the bare leaves would adapt all 22.84B routed-expert params too. We
therefore return FULL module paths and exclude anything under `.experts.`,
so only the shared/dense FFN + attention linears get adapters.
"""
from __future__ import annotations

ATTN_TOKENS = ("q_proj", "k_proj", "v_proj", "o_proj")
SHARED_FFN_TOKENS = ("gate_proj", "up_proj", "down_proj")
ROUTER_LEAVES = ("gate", "router", "gate_inp", "ffn_gate_inp")


def _linear_types():
    import torch.nn as nn
    types = [nn.Linear]
    try:  # bitsandbytes 4-bit linear (QLoRA base)
        from bitsandbytes.nn import Linear4bit
        types.append(Linear4bit)
    except Exception:
        pass
    return tuple(types)


def resolve_targets(model, train_router: bool = False) -> list[str]:
    """Return FULL module names to attach LoRA to: attention + shared FFN,
    excluding the 128 routed experts. Optionally include the router."""
    lin = _linear_types()
    out: list[str] = []
    for name, mod in model.named_modules():
        if not isinstance(mod, lin):
            continue
        if ".experts." in name:          # FREEZE routed experts (22.84B)
            continue
        leaf = name.rsplit(".", 1)[-1]
        if any(t in name for t in ATTN_TOKENS) or any(t in name for t in SHARED_FFN_TOKENS):
            out.append(name)             # full path → exact, expert-safe
        elif train_router and leaf in ROUTER_LEAVES:
            out.append(name)
    return out


def summarize(model, train_router: bool = False) -> dict:
    """Param accounting: trainable (adapter target) vs frozen (experts)."""
    targets = set(resolve_targets(model, train_router))
    trainable = frozen_experts = other = 0
    for name, mod in model.named_modules():
        if not hasattr(mod, "weight") or mod.weight is None:
            continue
        n = mod.weight.numel()
        if name in targets:
            trainable += n
        elif ".experts." in name:
            frozen_experts += n
        else:
            other += n
    return {
        "n_target_modules": len(targets),
        "target_base_params": trainable,
        "frozen_routed_expert_params": frozen_experts,
        "other_frozen_params": other,
        "train_router": train_router,
    }


if __name__ == "__main__":
    # Dry-run: load a model and print the resolved target set + accounting.
    import sys, json
    model_id = sys.argv[1] if len(sys.argv) > 1 else "google/gemma-4-26b-a4b-it"
    train_router = "--router" in sys.argv
    from transformers import AutoModelForCausalLM
    print(f"loading {model_id} (meta/CPU for introspection)…", file=sys.stderr)
    model = AutoModelForCausalLM.from_pretrained(model_id, device_map="meta",
                                                 trust_remote_code=True)
    tgts = resolve_targets(model, train_router)
    print(json.dumps({"n_targets": len(tgts), "sample": tgts[:8],
                      "accounting": summarize(model, train_router)}, indent=2))
