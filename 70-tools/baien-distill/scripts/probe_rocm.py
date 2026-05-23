"""Probe whether torch + ROCm (gfx1151) is usable for baien LoRA fine-tune.

Run on EVO-X2:
  python scripts/probe_rocm.py

Reports:
  - torch version + build tag
  - CUDA / HIP availability (HIP == ROCm on this hardware)
  - GPU device name(s)
  - bf16 / fp16 support
  - peft import OK
  - A tiny matmul on the GPU to confirm a tensor actually round-trips
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Any

os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")


def probe() -> dict[str, Any]:
    out: dict[str, Any] = {"ok": False, "checks": {}}
    try:
        import torch
    except Exception as e:
        out["checks"]["import_torch"] = f"FAIL: {e!r}"
        return out
    out["checks"]["import_torch"] = "ok"
    out["torch_version"] = torch.__version__
    out["torch_build"] = getattr(torch.version, "git_version", "?")
    out["cuda_available"] = bool(torch.cuda.is_available())
    out["cuda_version"] = getattr(torch.version, "cuda", None)
    out["hip_version"] = getattr(torch.version, "hip", None)

    device = None
    if torch.cuda.is_available():
        device = "cuda"
        try:
            out["device_count"] = torch.cuda.device_count()
            out["device_names"] = [
                torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
            ]
            out["bf16_supported"] = torch.cuda.is_bf16_supported()
        except Exception as e:
            out["checks"]["cuda_meta"] = f"FAIL: {e!r}"

        try:
            a = torch.randn(64, 64, device=device, dtype=torch.bfloat16)
            b = torch.randn(64, 64, device=device, dtype=torch.bfloat16)
            c = (a @ b).sum().item()
            out["checks"]["gpu_bf16_matmul"] = (
                "ok" if isinstance(c, float) else f"unexpected: {c!r}"
            )
        except Exception as e:
            out["checks"]["gpu_bf16_matmul"] = f"FAIL: {e!r}"
    else:
        out["checks"]["cuda_available"] = "cpu-only"

    # peft is installed unconditionally
    try:
        import peft
        out["checks"]["import_peft"] = "ok"
        out["peft_version"] = peft.__version__
    except Exception as e:
        out["checks"]["import_peft"] = f"FAIL: {e!r}"

    try:
        import trl
        out["checks"]["import_trl"] = "ok"
        out["trl_version"] = trl.__version__
    except Exception as e:
        out["checks"]["import_trl"] = f"FAIL: {e!r}"

    out["ok"] = all(
        v == "ok" or v == "cpu-only"
        for v in out["checks"].values()
    )
    return out


if __name__ == "__main__":
    try:
        result = probe()
    except Exception:
        traceback.print_exc()
        sys.exit(2)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    sys.exit(0 if result.get("ok") else 1)
