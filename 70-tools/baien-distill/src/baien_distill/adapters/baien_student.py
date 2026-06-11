"""Load the baien bf16 master via transformers, with torch.compile suppressed.

Mirrors 70-tools/scripts/bench/baien-microbench/microbench.py load_hf().
"""

from __future__ import annotations

import os

os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")


def load_student(model_id: str = "microsoft/bitnet-b1.58-2B-4T-bf16"):
    import torch
    try:
        import torch._dynamo as _dyn
        _dyn.config.suppress_errors = True
        _dyn.disable()
    except Exception:
        pass
    # Best-effort: skip the inductor cpu vec_isa probe (it requires `cl` on Win)
    try:
        from torch._inductor import cpu_vec_isa
        cpu_vec_isa.valid_vec_isa_list = lambda: []  # type: ignore[assignment]
    except Exception:
        pass

    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.bfloat16)
    model.eval()
    return tok, model
