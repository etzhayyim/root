"""Mitsuba 3 differentiable rendering (LLVM autodiff backend).

Requires libLLVM (e.g. /opt/homebrew/opt/llvm/lib/libLLVM.dylib).

Per ADR-2605261600 §3 non-symmetric advantages (b):
  > Mitsuba 3 differentiable rendering (inverse rendering for camera-attestation
  > consistency verification — not in Omniverse stack)

This demo: optimize chassis BSDF reflectance (color) so the rendered image
matches a target image. PRB handles continuous BSDF parameters (light-position
optimization is discontinuous and needs a different integrator). 6 iterations.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DRJIT_LIBLLVM_PATH", "/opt/homebrew/opt/llvm/lib/libLLVM.dylib")

import drjit as dr
import mitsuba as mi
import numpy as np

mi.set_variant("llvm_ad_rgb")

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)


def make_scene(chassis_rgb=(0.2, 0.55, 0.2)):
    return mi.load_dict({
        "type": "scene",
        "integrator": {"type": "prb", "max_depth": 4},
        "sensor": {
            "type": "perspective", "fov": 45,
            "to_world": mi.ScalarTransform4f().look_at(
                origin=[3.5, -3.0, 2.0], target=[0, 0, 0.3], up=[0, 0, 1]),
            "film": {"type": "hdrfilm", "width": 128, "height": 96, "pixel_format": "rgb"},
            "sampler": {"type": "independent", "sample_count": 8},
        },
        "light": {
            "type": "point",
            "position": [4.0, -1.0, 5.0],
            "intensity": {"type": "spectrum", "value": 80.0},
        },
        "ground": {
            "type": "rectangle",
            "to_world": mi.ScalarTransform4f().scale([10, 10, 1]),
            "bsdf": {"type": "diffuse", "reflectance": {"type": "rgb", "value": [0.3, 0.45, 0.2]}},
        },
        "chassis": {
            "type": "cube",
            "to_world": (mi.ScalarTransform4f().translate([0, 0, 0.30])
                         @ mi.ScalarTransform4f().scale([0.70, 0.45, 0.10])),
            "bsdf": {"type": "diffuse",
                     "reflectance": {"type": "rgb", "value": list(chassis_rgb)}},
        },
    })


def main() -> int:
    print(f"Mitsuba {mi.MI_VERSION}, variant: {mi.variant()}")

    # Target: bright orange-ish chassis
    target = make_scene(chassis_rgb=(0.85, 0.40, 0.10))
    target_img = mi.render(target, spp=16)
    mi.util.write_bitmap(str(OUT / "diff_target.png"), target_img)
    print(f"Target rendered: mean = {dr.mean(dr.ravel(target_img))[0]:.4f}")

    # Scene starts green; we optimize chassis color to match target (orange).
    scene = make_scene(chassis_rgb=(0.2, 0.55, 0.2))
    params = mi.traverse(scene)
    all_keys = list(params.keys())
    key = next((k for k in all_keys if "chassis" in k and "reflectance" in k and "value" in k), None)
    if key is None:
        chassis_keys = [k for k in all_keys if "chassis" in k]
        print("could not find chassis reflectance; chassis keys:", chassis_keys)
        return 1
    print(f"Optimizing parameter: '{key}'  init = {params[key]}")

    opt = mi.ad.Adam(lr=0.05)
    opt[key] = mi.Color3f(params[key])

    for it in range(8):
        params[key] = dr.clip(opt[key], 0.001, 0.999)
        params.update()
        img = mi.render(scene, params, spp=8, seed=it)
        loss = dr.mean(dr.square(dr.ravel(img) - dr.ravel(target_img)))
        dr.backward(loss)
        opt.step()
        c = opt[key]
        print(f"  iter {it}: chassis_rgb=({c.x[0]:.3f}, {c.y[0]:.3f}, {c.z[0]:.3f})  loss={loss[0]:.5f}")

    final_img = mi.render(scene, params, spp=32)
    mi.util.write_bitmap(str(OUT / "diff_final.png"), final_img)
    final_color = opt[key]
    print(f"\nFinal chassis color: ({final_color.x[0]:.3f}, {final_color.y[0]:.3f}, {final_color.z[0]:.3f})")
    print(f"Target chassis color: (0.850, 0.400, 0.100)")
    print(f"Wrote: {OUT / 'diff_target.png'}  +  {OUT / 'diff_final.png'}")
    print("\nMitsuba 3 differentiable rendering (PRB): OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
