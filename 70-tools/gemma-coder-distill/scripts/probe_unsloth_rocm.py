"""Probe whether Unsloth runs on EVO-X2 (Windows 11 + ROCm 7.2.1 + gfx1151)
with the gemma-3 architecture.

Decision gate for ADR-2605250400 §1.2: if all three checks pass, gemma-coder-distill
uses Unsloth as the primary trainer; otherwise falls back to peft+trl direct.

Run on EVO-X2:

  # 1) ROCm venv (the one baien-distill probe_rocm.py already validated)
  ssh evo "C:\\Users\\gad\\ComfyUI\\ComfyUI_windows_portable\\python_embeded\\python.exe ^
            -m pip install --upgrade unsloth"

  # 2) execute this probe (output JSON to stdout)
  ssh evo "C:\\Users\\gad\\ComfyUI\\ComfyUI_windows_portable\\python_embeded\\python.exe ^
            70-tools\\gemma-coder-distill\\scripts\\probe_unsloth_rocm.py"

  # 3) commit result to repo
  cp <stdout> 90-docs/baien/probe_unsloth_rocm.json
  git add 90-docs/baien/probe_unsloth_rocm.json
  git commit -m "probe(gemma-coder-distill): unsloth rocm probe result"

Exit code:
  0  = all 3 checks pass → use Unsloth (ADR §1.2 primary)
  1  = at least one check fails → use peft+trl fallback (ADR §1.2 fallback)
  2  = probe itself crashed (env broken) — investigate before deciding
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Any

os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

STUDENT_ID = "google/gemma-4-e4b-it"


def probe() -> dict[str, Any]:
    out: dict[str, Any] = {"adr": "2605250400", "checks": {}, "decision": "fallback"}

    # ── check 1: torch + ROCm baseline (mirrors baien-distill probe_rocm.py) ──
    try:
        import torch
        out["torch_version"] = torch.__version__
        out["hip_version"] = getattr(torch.version, "hip", None)
        out["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            out["device_names"] = [
                torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
            ]
            out["bf16_supported"] = torch.cuda.is_bf16_supported()
        out["checks"]["torch_rocm"] = "ok" if torch.cuda.is_available() else "FAIL: no cuda/hip"
    except Exception as e:
        out["checks"]["torch_rocm"] = f"FAIL: {e!r}"
        return out

    # ── check 2: unsloth import + version ──
    try:
        import unsloth
        out["unsloth_version"] = getattr(unsloth, "__version__", "unknown")
        out["checks"]["unsloth_import"] = "ok"
    except Exception as e:
        out["checks"]["unsloth_import"] = f"FAIL: {e!r}"
        # don't return — record remaining checks as N/A
        out["checks"]["unsloth_gemma3_load"] = "SKIP: unsloth not importable"
        out["checks"]["unsloth_tiny_lora_step"] = "SKIP: unsloth not importable"
        return out

    # ── check 3: gemma-3 architecture dry-instantiate via Unsloth ──
    try:
        from unsloth import FastLanguageModel  # type: ignore
        # max_seq_length intentionally tiny to keep probe under ~2 min
        model, tok = FastLanguageModel.from_pretrained(
            model_name=STUDENT_ID,
            max_seq_length=512,
            dtype=None,  # auto (bf16 on ROCm)
            load_in_4bit=False,  # full bf16 — we have 32 GiB VRAM
        )
        out["checks"]["unsloth_gemma3_load"] = "ok"
    except Exception as e:
        out["checks"]["unsloth_gemma3_load"] = f"FAIL: {e!r}"
        out["checks"]["unsloth_tiny_lora_step"] = "SKIP: gemma3 load failed"
        return out

    # ── check 4: tiny LoRA forward + backward step ──
    try:
        from unsloth import FastLanguageModel  # type: ignore
        model = FastLanguageModel.get_peft_model(
            model,
            r=8,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            lora_alpha=16,
            lora_dropout=0.05,
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=42,
        )
        import torch
        # synthetic batch
        text = "def hello():\n    return 'world'\n"
        enc = tok(text, return_tensors="pt").to(model.device)
        out_ = model(**enc, labels=enc["input_ids"])
        out_.loss.backward()
        out["checks"]["unsloth_tiny_lora_step"] = "ok"
        out["initial_loss"] = float(out_.loss.detach().cpu().item())
    except Exception as e:
        out["checks"]["unsloth_tiny_lora_step"] = f"FAIL: {e!r}"
        return out

    return out


if __name__ == "__main__":
    try:
        result = probe()
    except Exception:
        traceback.print_exc()
        sys.exit(2)

    all_ok = all(v == "ok" for v in result["checks"].values())
    result["decision"] = "primary-unsloth" if all_ok else "fallback-peft-trl"

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    sys.exit(0 if all_ok else 1)
