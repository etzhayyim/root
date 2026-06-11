"""Run lm-eval-harness with torch.compile / inductor probes fully suppressed.

The default `lm-eval` CLI triggers torch._inductor's CPU vec-ISA probe,
which on Windows tries to invoke MSVC `cl.exe` to compile a tiny test
file. EVO-X2 doesn't have MSVC installed, so the probe raises and the
run dies (even at `--num_fewshot 0` and with `TORCH_COMPILE_DISABLE=1`,
because the probe is a separate code path).

This wrapper pre-empts the probe, then dispatches to the same
`cli_evaluate` entry that `lm-eval` would have called.

Usage (drop-in replacement for `lm-eval run ...`):
  python lm_eval_wrapper.py run --model hf --model_args ... --tasks ...
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

import torch  # noqa: E402

try:
    import torch._dynamo as _dyn
    _dyn.config.suppress_errors = True
    _dyn.disable()
except Exception:  # pragma: no cover
    pass

# Skip the inductor cpu vec_isa probe entirely. Returning an empty list
# makes torch use a "Default" (scalar) ISA — slower per-op but safe and
# does not require any C++ compiler at startup.
try:
    from torch._inductor import cpu_vec_isa
    cpu_vec_isa.valid_vec_isa_list = lambda: []  # type: ignore[assignment]
except Exception:  # pragma: no cover
    pass

from lm_eval.__main__ import cli_evaluate  # noqa: E402

if __name__ == "__main__":
    sys.exit(cli_evaluate())
