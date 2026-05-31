"""Edge invariant attestation per ADR-2605241900 §Decision (8 ceilings).

Run-time RAM measurement:
  - packed_weights (from quantize manifest)
  - KV cache @ 4 k + 16 k contexts (from arch metadata)
  - activations scratch (estimated at 200 MB constant)
  - tokenizer + runtime overhead (50 MB constant)

For now this is the **calculated attestation**. A future Phase 2
runs the model on an actual iPhone 14 simulator + a Mac mini fleet
node and records measured RAM + first-token latency.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .state import BASE_CANDIDATES, RosoState, EDGE_INVARIANT


ACTIVATIONS_GB = 0.2
RUNTIME_GB = 0.05


def attest(state: RosoState) -> RosoState:
    cfg = state.cfg
    spec = BASE_CANDIDATES.get(cfg.base_model)
    if spec is None:
        state.notes.append("[attestation] unknown base — abort")
        state.decision = "abort"
        return state

    packed = state.packed_weights_gb if state.packed_weights_gb is not None \
             else float(spec["expected_1bit_gb"])
    kv_4k = float(spec["kv_at_16k_gb"]) / 4
    kv_16k = float(spec["kv_at_16k_gb"])

    ram_4k = packed + kv_4k + ACTIVATIONS_GB + RUNTIME_GB
    ram_16k = packed + kv_16k + ACTIVATIONS_GB + RUNTIME_GB

    state.attestation_ram_4k_gb = ram_4k
    state.attestation_ram_16k_gb = ram_16k

    tier = spec.get("tier", "edge")
    if tier == "server":
        state.notes.append(
            f"[attestation] tier=server ({spec.get('tier_doc', '')}) - "
            f"edge invariant ceiling check SKIPPED. packed={packed:.2f} GB | "
            f"RAM @4k={ram_4k:.2f} GB | @16k={ram_16k:.2f} GB"
        )
        state.attestation_passed = True
        checks = {"_skipped": "server tier per ADR-2605242100"}
    else:
        state.notes.append("[attestation] computing edge invariant RAM @ 4k + 16k")
        checks = {
            "trunk_params_max": spec["params"] <= EDGE_INVARIANT["trunk_params_max"],
            "packed_weights_max": packed <= EDGE_INVARIANT["packed_weights_gb_max"],
            "inference_4k_max": ram_4k <= EDGE_INVARIANT["inference_4k_gb_max"],
            "inference_16k_max": ram_16k <= EDGE_INVARIANT["inference_16k_gb_max"],
        }
        state.attestation_passed = all(checks.values())

    state.notes.append(
        f"[attestation] packed={packed:.2f} GB | RAM @4k={ram_4k:.2f} GB | "
        f"RAM @16k={ram_16k:.2f} GB | passed={state.attestation_passed}"
    )
    if tier != "server":
        for k, v in checks.items():
            if not v:
                state.notes.append(f"[attestation] FAIL {k}")

    if state.quantized_path is not None:
        out = Path(state.quantized_path) / "attestation.json"
        out.write_text(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "base_model": cfg.base_model,
            "method": cfg.quant_method,
            "iter": state.iter,
            "packed_gb": packed,
            "kv_4k_gb": kv_4k,
            "kv_16k_gb": kv_16k,
            "activations_gb": ACTIVATIONS_GB,
            "runtime_gb": RUNTIME_GB,
            "ram_4k_gb": ram_4k,
            "ram_16k_gb": ram_16k,
            "edge_invariant_checks": checks,
            "passed": state.attestation_passed,
            "note": (
                "calculated attestation; physical-device measurement on "
                "iPhone 14 + Android 4GB pending ADR-2605241900 §Enforcement Phase 2"
            ),
        }, indent=2), encoding="utf-8")

    if not state.attestation_passed:
        state.notes.append("[attestation] edge invariant violated — decision=abort")
        state.decision = "abort"

    return state
