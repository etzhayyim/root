#!/usr/bin/env python3
"""Wiring smoke for the Maxwell multimodal image-diffusion graft (R0).

Builds the pipeline with a deterministic FakeEncoder (stdlib-only — no torch/numpy/
models, no randomness) and asserts:
  - shapes flow encoder → projection → (L×C) context;
  - Path A / Charter invariants hold (license tags, G1/G3/G4 gates);
  - real model paths honestly raise NotImplementedError at R0.

Run:  python3 70-tools/scripts/maxwell/mmdiffusion/smoke.py
Exits non-zero on any failed assertion.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from joint_encoder import (  # noqa: E402
    FakeEncoder, ImageBindEncoder, LanguageBindEncoder, MURAKUMO_ONLY,
)
from projection import ProjectionAdapter  # noqa: E402
from conditioning import (  # noqa: E402
    DiffusionConditioner, GenerationRequest, BiometricUseError,
)

PASS, FAIL = 0, 0


def check(name: str, cond: bool) -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}")


def expect_raises(name: str, fn, exc) -> None:
    try:
        fn()
    except exc:
        check(name, True)
    except Exception as e:  # noqa: BLE001
        check(f"{name} (wrong exc {type(e).__name__})", False)
    else:
        check(f"{name} (did not raise)", False)


def main() -> int:
    print("maxwell mmdiffusion — R0 wiring smoke\n")

    # ── 1. wiring + shapes (FakeEncoder, mirrors ImageBind license profile) ──
    enc = FakeEncoder(embed_dim=16, redistributable=False,
                      source_license="CC-BY-NC-4.0(mirror)",
                      output_license="CC-BY-NC-4.0(mirror)")
    proj = ProjectionAdapter(in_dim=enc.embed_dim, context_len=4, context_dim=8)
    cond = DiffusionConditioner(encoder=enc, projection=proj)

    z = enc.embed("image", b"a-test-tile")
    check("embed dim == encoder.embed_dim", z.dim == 16)
    z2 = enc.embed("image", b"a-test-tile")
    check("encoder is deterministic", list(z.vector) == list(z2.vector))

    ctx, lic = cond.build_context(GenerationRequest("image", b"a-test-tile"), fake=True)
    check("context rows == context_len", len(ctx) == 4)
    check("context cols == context_dim", all(len(r) == 8 for r in ctx))
    check("output license propagated", lic == "CC-BY-NC-4.0(mirror)")

    # ── 2. Charter gate G1 — Murakumo-only flag present ──
    check("G1 MURAKUMO_ONLY is True", MURAKUMO_ONLY is True)

    # ── 3. G3 no-biometric refusal ──
    expect_raises(
        "G3 refuses biometric intent",
        lambda: cond.build_context(
            GenerationRequest("image", b"x", intent="face-id"), fake=True),
        BiometricUseError,
    )

    # ── 4. G4 Path A firewall — NC outputs cannot feed internal commerce ──
    expect_raises(
        "G4 refuses CC-BY-NC output in commercial context",
        lambda: cond.build_context(
            GenerationRequest("image", b"x", commercial_context=True), fake=True),
        RuntimeError,
    )

    # ── 5. license profiles of the real encoders (Path A) ──
    ib, lb = ImageBindEncoder(), LanguageBindEncoder()
    check("ImageBind is CC-BY-NC", ib.source_license == "CC-BY-NC-4.0")
    check("ImageBind NOT redistributable (Path A)", ib.redistributable is False)
    check("ImageBind outputs CC-BY-NC", ib.output_license == "CC-BY-NC-4.0")
    check("LanguageBind is MIT", lb.source_license == "MIT")
    check("LanguageBind redistributable (commons path)", lb.redistributable is True)
    check("LanguageBind outputs ECL-on-Apache", lb.output_license == "ECL-on-Apache")

    # ── 6. honest R0 — real model paths raise NotImplementedError ──
    expect_raises("ImageBind.embed honestly unimplemented",
                  lambda: ib.embed("image", b"x"), NotImplementedError)
    expect_raises("ProjectionAdapter.forward honestly unimplemented",
                  lambda: proj.forward(z), NotImplementedError)
    expect_raises("DiffusionConditioner.denoise_step honestly unimplemented",
                  lambda: cond.denoise_step(), NotImplementedError)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
