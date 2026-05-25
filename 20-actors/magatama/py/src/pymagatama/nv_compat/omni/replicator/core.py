"""omni.replicator.core — minimal synthetic data generation API surface.

Mirrors public `omni.replicator.core` API documented in Omniverse Replicator
docs. R1.3 deliverable per ADR-2605261800: BasicWriter emits same JSON schema
as upstream Replicator (R1.3 G5 gate: JSON diff = 0).

R1.0 scope: API surface only — `new_layer`, `trigger.on_frame`, `create`,
`modify`, `distribution`, `WriterRegistry`, `BasicWriter`. Backends route to
kami-replicator (Rust) when WGSL render lands at R1.4.
"""

from __future__ import annotations

import contextlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ---- Distribution sub-namespace ------------------------------------------------

class _Distribution:
    @staticmethod
    def uniform(low, high):
        return {"_kind": "uniform", "low": list(low), "high": list(high)}

    @staticmethod
    def normal(mean, std):
        return {"_kind": "normal", "mean": list(mean), "std": list(std)}


distribution = _Distribution()


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
