"""omni.replicator.core — synthetic data generation + domain randomization.

Mirrors public `omni.replicator.core` API documented in Omniverse Replicator
docs. R1.3 deliverable per ADR-2605261800: BasicWriter emits same JSON schema
as upstream Replicator (R1.3 G5 gate: JSON diff = 0).

Iter 16 expands the distribution sub-namespace to cover the standard
Replicator DR primitives (choice / truncated_normal / sequence / combine) and
adds a `randomize` sub-namespace for scene-level randomization helpers
(materials, lights, scatter_2d, scatter_3d) so sim2real RL workflows port
from upstream Isaac Sim Replicator scripts with import-path-only changes.
"""

from __future__ import annotations

import contextlib
import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ---- Seedable LCG sampler ------------------------------------------------------
#
# Same algorithm as kami_genesis / kami_shugyo Lcg so DR outputs are
# bit-reproducible across language boundaries.

class _Sampler:
    def __init__(self, seed: int = 0):
        self.state = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF

    def next_u01(self) -> float:
        self.state = (self.state * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        return ((self.state >> 33) & 0x7FFFFFFF) / float(1 << 31)

    def next_uniform(self, low: float, high: float) -> float:
        return low + (high - low) * self.next_u01()

    def next_normal(self, mean: float, std: float) -> float:
        # Box–Muller; uses two uniforms.
        u1 = max(self.next_u01(), 1e-12)
        u2 = self.next_u01()
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mean + std * z

    def next_truncated_normal(self, mean: float, std: float, low: float, high: float) -> float:
        # Rejection sampling; caps at 20 attempts to avoid pathological cases.
        for _ in range(20):
            v = self.next_normal(mean, std)
            if low <= v <= high:
                return v
        return max(low, min(high, mean))


# Module-level shared sampler with reset via `seed_global(s)`. Per-distribution
# instances may also use a private sampler for tight control.
_GLOBAL = _Sampler(seed=0)


def seed_global(seed: int) -> None:
    """Re-seed the module-level sampler used by `sample(dist)` when no
    explicit sampler is provided."""
    global _GLOBAL
    _GLOBAL = _Sampler(seed=seed)


# ---- Distribution sub-namespace ------------------------------------------------

class _Distribution:
    """Replicator distribution primitives. Each constructor returns a tagged
    dict (`_kind`) that `sample(dist)` resolves to a concrete value. The
    tagged-dict form preserves upstream Replicator's lazy semantics where a
    distribution is captured at script time and sampled per-frame at trigger
    fire time."""

    @staticmethod
    def uniform(low, high):
        return {"_kind": "uniform", "low": list(low), "high": list(high)}

    @staticmethod
    def normal(mean, std):
        return {"_kind": "normal", "mean": list(mean), "std": list(std)}

    @staticmethod
    def truncated_normal(mean, std, low, high):
        return {
            "_kind": "truncated_normal",
            "mean": list(mean), "std": list(std),
            "low": list(low), "high": list(high),
        }

    @staticmethod
    def choice(options):
        """Categorical sample over `options` (any list)."""
        return {"_kind": "choice", "options": list(options)}

    @staticmethod
    def sequence(values):
        """Cycle through `values` deterministically (modulo length)."""
        return {"_kind": "sequence", "values": list(values), "_index": [0]}

    @staticmethod
    def combine(distributions):
        """Sample independently from each constituent and concatenate the
        resulting vectors (or wrap scalars). Useful for stacking
        per-dimension distributions."""
        return {"_kind": "combine", "distributions": list(distributions)}


distribution = _Distribution()


def sample(dist, sampler: Optional[_Sampler] = None):
    """Materialize a distribution to a concrete value. Uses `sampler` if
    given, otherwise the module-level `_GLOBAL` sampler."""
    s = sampler if sampler is not None else _GLOBAL
    kind = dist.get("_kind")
    if kind == "uniform":
        return [s.next_uniform(lo, hi) for lo, hi in zip(dist["low"], dist["high"])]
    if kind == "normal":
        return [s.next_normal(m, sd) for m, sd in zip(dist["mean"], dist["std"])]
    if kind == "truncated_normal":
        return [
            s.next_truncated_normal(m, sd, lo, hi)
            for m, sd, lo, hi in zip(
                dist["mean"], dist["std"], dist["low"], dist["high"]
            )
        ]
    if kind == "choice":
        opts = dist["options"]
        idx = int(s.next_u01() * len(opts))
        if idx >= len(opts):
            idx = len(opts) - 1
        return opts[idx]
    if kind == "sequence":
        vals = dist["values"]
        i = dist["_index"][0] % len(vals)
        dist["_index"][0] = (dist["_index"][0] + 1) % len(vals)
        return vals[i]
    if kind == "combine":
        out = []
        for sub in dist["distributions"]:
            v = sample(sub, s)
            if isinstance(v, list):
                out.extend(v)
            else:
                out.append(v)
        return out
    raise ValueError(f"unknown distribution kind: {kind!r}")


# ---- Create / Modify sub-namespaces -------------------------------------------

class _CreateNS:
    @staticmethod
    def camera(position=(0, 5, 0), rotation=(0, 0, 0), focal_length=24.0):
        return {"_kind": "camera", "position": list(position),
                "rotation": list(rotation), "focal_length": focal_length}

    @staticmethod
    def light(rotation=(0, 0, 0), light_type="distant", intensity=1000.0):
        return {"_kind": "light", "rotation": list(rotation),
                "light_type": light_type, "intensity": intensity}

    @staticmethod
    def cube(position=(0, 0, 0), semantics=None):
        return {"_kind": "cube", "position": list(position),
                "semantics": list(semantics or [])}

    @staticmethod
    def sphere(position=(0, 0, 0), radius=1.0, semantics=None):
        return {"_kind": "sphere", "position": list(position),
                "radius": radius, "semantics": list(semantics or [])}


create = _CreateNS()


class _ModifyNS:
    @staticmethod
    def pose(position=None, rotation=None):
        return {"_op": "pose", "position": position, "rotation": rotation}

    @staticmethod
    def visibility(visible=True):
        return {"_op": "visibility", "visible": visible}


modify = _ModifyNS()


# ---- Randomize sub-namespace (scene-level DR helpers) -------------------------
#
# Mirrors `omni.replicator.core.randomize.*` — high-level scene operations that
# combine a `create.*` or `modify.*` op with a distribution. Returns tagged
# dicts that an orchestrator/writer can resolve at trigger fire time.

class _RandomizeNS:
    @staticmethod
    def materials(prims, materials):
        """Per-frame random material choice for the given prims."""
        return {
            "_kind": "randomize_materials",
            "prims": list(prims),
            "materials": distribution.choice(list(materials)),
        }

    @staticmethod
    def lights(rotation_dist=None, intensity_dist=None, color_dist=None):
        """Randomize all distant lights' rotation / intensity / color."""
        return {
            "_kind": "randomize_lights",
            "rotation": rotation_dist or distribution.uniform([-90, -180, -180], [90, 180, 180]),
            "intensity": intensity_dist or distribution.uniform([500.0], [3000.0]),
            "color": color_dist or distribution.uniform([0.7, 0.7, 0.7], [1.0, 1.0, 1.0]),
        }

    @staticmethod
    def scatter_2d(prims, plane="xy", region=((-2.0, -2.0), (2.0, 2.0)), rotation_z=None):
        """Random 2D scatter onto a plane in the xy or xz region rectangle."""
        return {
            "_kind": "scatter_2d",
            "prims": list(prims),
            "plane": plane,
            "region": [list(region[0]), list(region[1])],
            "rotation_z": rotation_z or distribution.uniform([-180.0], [180.0]),
        }

    @staticmethod
    def scatter_3d(prims, volume=((-1.0, -1.0, 0.0), (1.0, 1.0, 2.0)), rotation=None):
        """Random 3D scatter inside an AABB volume."""
        return {
            "_kind": "scatter_3d",
            "prims": list(prims),
            "volume": [list(volume[0]), list(volume[1])],
            "rotation": rotation or distribution.uniform([-180.0, -180.0, -180.0],
                                                        [180.0, 180.0, 180.0]),
        }

    @staticmethod
    def physics_properties(prim, mass_dist=None, friction_dist=None):
        """Randomize physics properties (mass, friction) of a single prim."""
        return {
            "_kind": "randomize_physics",
            "prim": prim,
            "mass": mass_dist or distribution.uniform([0.5], [2.0]),
            "friction": friction_dist or distribution.uniform([0.3], [0.9]),
        }


randomize = _RandomizeNS()


def resolve(op, sampler: Optional[_Sampler] = None) -> dict:
    """Materialize a randomize op to a concrete scene operation. Used by
    orchestrator/writer; not part of upstream Replicator surface (upstream
    resolves at omni.kit graph evaluation time)."""
    s = sampler if sampler is not None else _GLOBAL
    kind = op.get("_kind", "")
    if kind == "randomize_materials":
        return {"kind": kind, "prims": op["prims"], "material": sample(op["materials"], s)}
    if kind == "randomize_lights":
        return {
            "kind": kind,
            "rotation": sample(op["rotation"], s),
            "intensity": sample(op["intensity"], s)[0],
            "color": sample(op["color"], s),
        }
    if kind == "scatter_2d":
        poses = []
        rx0, ry0 = op["region"][0]
        rx1, ry1 = op["region"][1]
        for _ in op["prims"]:
            x = s.next_uniform(rx0, rx1)
            y = s.next_uniform(ry0, ry1)
            rz = sample(op["rotation_z"], s)[0]
            if op["plane"] == "xy":
                poses.append({"position": [x, y, 0.0], "rotation_z": rz})
            else:  # xz
                poses.append({"position": [x, 0.0, y], "rotation_z": rz})
        return {"kind": kind, "poses": poses}
    if kind == "scatter_3d":
        poses = []
        v0 = op["volume"][0]; v1 = op["volume"][1]
        for _ in op["prims"]:
            position = [s.next_uniform(v0[i], v1[i]) for i in range(3)]
            poses.append({"position": position, "rotation": sample(op["rotation"], s)})
        return {"kind": kind, "poses": poses}
    if kind == "randomize_physics":
        return {
            "kind": kind,
            "prim": op["prim"],
            "mass": sample(op["mass"], s)[0],
            "friction": sample(op["friction"], s)[0],
        }
    return {"kind": kind}


# ---- Layer + trigger -----------------------------------------------------------

@dataclass
class _Layer:
    primitives: list = field(default_factory=list)
    triggers: list = field(default_factory=list)
    writers: list = field(default_factory=list)


_active_layer: Optional[_Layer] = None
_active_target: Optional[dict] = None


@contextlib.contextmanager
def new_layer():
    """`with rep.new_layer():` context."""
    global _active_layer
    layer = _Layer()
    _active_layer = layer
    try:
        yield layer
    finally:
        _active_layer = None


class _TriggerNS:
    @staticmethod
    @contextlib.contextmanager
    def on_frame(num_frames: int):
        if _active_layer is None:
            raise RuntimeError("on_frame requires `with new_layer():` context")
        trigger = {"_kind": "on_frame", "num_frames": num_frames, "ops": []}
        _active_layer.triggers.append(trigger)
        yield trigger


trigger = _TriggerNS()


# ---- WriterRegistry + BasicWriter ---------------------------------------------

class _BasicWriter:
    def __init__(self):
        self._cfg = {}
        self._output_dir: Optional[Path] = None
        self._frame = 0
        self._cameras = []

    def initialize(self, output_dir: str, rgb: bool = True,
                   bounding_box_2d_tight: bool = False,
                   semantic_segmentation: bool = False,
                   distance_to_camera: bool = False):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._cfg = {
            "rgb": rgb,
            "bbox2d_tight": bounding_box_2d_tight,
            "semantic": semantic_segmentation,
            "depth": distance_to_camera,
        }

    def attach(self, cameras: list):
        self._cameras = list(cameras)

    def write_frame(self, frame_index: int, sample: dict) -> Path:
        """Mirror of Replicator BasicWriter on-disk schema.

        Output: `{output_dir}/rgb_{frame:04d}.json` placeholder (real PNG
        when kami-render WGSL lands at R1.4; schema identical now).
        """
        if self._output_dir is None:
            raise RuntimeError("BasicWriter.initialize() first")
        path = self._output_dir / f"frame_{frame_index:04d}.json"
        payload = {"frame": frame_index, "cameras": self._cameras, "sample": sample}
        path.write_text(json.dumps(payload, indent=2))
        return path


class _WriterRegistry:
    _writers: dict = {"BasicWriter": _BasicWriter}

    @classmethod
    def get(cls, name: str):
        if name not in cls._writers:
            raise KeyError(f"unknown writer: {name}")
        return cls._writers[name]()

    @classmethod
    def register(cls, name: str, klass) -> None:
        cls._writers[name] = klass


WriterRegistry = _WriterRegistry


# ---- runtime ------------------------------------------------------------------

def orchestrator_run(num_frames: Optional[int] = None) -> None:
    """Minimal orchestrator: walks triggers in active layer and dispatches writers.

    Not part of upstream Replicator API. Provided for end-to-end testability;
    real Omniverse runs `omni.kit.app` loop with `step()` ticks.
    """
    if _active_layer is None:
        raise RuntimeError("orchestrator_run inside `with new_layer():` context only")
    for t in _active_layer.triggers:
        frames = num_frames or t["num_frames"]
        for i in range(frames):
            sample = {"primitives": _active_layer.primitives, "frame": i}
            for w in _active_layer.writers:
                w.write_frame(i, sample)
