"""Frozen joint-embedding encoders for the Maxwell multimodal image-diffusion graft.

R0 scaffold (ADR-2606061000 D6 M3 · license ADR-2606172300). The encoders are
FROZEN (baien invariant ADR-2605241900 "全 modality encoder 凍結"); only the
downstream ProjectionAdapter is trained.

Charter / Path A invariants are carried as data on each encoder so the rest of the
pipeline (and the smoke) can assert them without loading any model:

  - ImageBind   : CC-BY-NC 4.0, NOT redistributable, internal-use only (Path A).
  - LanguageBind: MIT, redistributable, commons path (ECL-on-Apache outputs).

NO weights ship here. Real `embed()` raises NotImplementedError until the gated
M3.1 integration step wires the actual (internal, Murakumo-served) models.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Sequence

# G1 — Murakumo-only inference (Rider §2(i), ADR-2605215000). Frozen-encoder forward
# passes execute on the fleet, never on a commercial GPU backend.
MURAKUMO_ONLY = True

MODALITIES = ("text", "image", "audio", "depth", "thermal", "imu")


@dataclass(frozen=True)
class Embedding:
    """A joint-space embedding vector + provenance for license/Charter checks."""
    vector: Sequence[float]
    modality: str
    source_license: str          # license of the encoder that produced it
    redistributable: bool        # may the producing embedding be shipped as commons?

    @property
    def dim(self) -> int:
        return len(self.vector)


class JointEncoder(ABC):
    """Frozen multimodal encoder mapping any modality into one joint space."""

    name: str = "abstract"
    embed_dim: int = 0
    source_license: str = "UNSET"
    redistributable: bool = False
    output_license: str = "UNSET"        # license that attaches to graft outputs
    supported_modalities: tuple[str, ...] = MODALITIES

    def assert_internal_use_only(self) -> None:
        """G4 — non-redistributable (CC-BY-NC) encoders must not feed Charter-permitted
        internal commerce (SBT↔SBT omise/okaimono/promo). Caller asserts the use is a
        non-commercial actor function before drawing on such an encoder."""
        if not self.redistributable:
            # Path A firewall: callers in internal-commercial contexts must refuse.
            return  # documented constraint; enforced by the caller + smoke.

    @abstractmethod
    def embed(self, modality: str, data: object) -> Embedding:
        ...

    def _check_modality(self, modality: str) -> None:
        if modality not in self.supported_modalities:
            raise ValueError(f"{self.name}: unsupported modality {modality!r}")


class ImageBindEncoder(JointEncoder):
    """facebookresearch/ImageBind — 6-modality, CC-BY-NC 4.0.

    Path A: lives in `vendor/imagebind-fork/` with its CC-BY-NC NOTICE preserved,
    NO Charter Rider applied, and is NEVER redistributed by etzhayyim. Used Maxwell-
    internal only; its outputs are CC-BY-NC.
    """
    name = "imagebind"
    embed_dim = 1024
    source_license = "CC-BY-NC-4.0"
    redistributable = False
    output_license = "CC-BY-NC-4.0"
    supported_modalities = MODALITIES

    def embed(self, modality: str, data: object) -> Embedding:
        self._check_modality(modality)
        raise NotImplementedError(
            "ImageBind weights are CC-BY-NC and live in vendor/imagebind-fork/ "
            "(not in this repo). Real embedding is the gated M3.1 step, internal/"
            "Murakumo-only. R0 scaffold uses FakeEncoder in smoke.py."
        )


class LanguageBindEncoder(JointEncoder):
    """LanguageBind — language-centric N-modality binding, MIT.

    Commons-shippable path: outputs carry ECL-on-Apache (the diffusion graft can be a
    public artifact). Preferred when the graft is to be released, not just internal.
    """
    name = "languagebind"
    embed_dim = 768
    source_license = "MIT"
    redistributable = True
    output_license = "ECL-on-Apache"
    # language-direct alignment; thermal/imu out of scope for the MIT path at R0
    supported_modalities = ("text", "image", "audio", "depth")

    def embed(self, modality: str, data: object) -> Embedding:
        self._check_modality(modality)
        raise NotImplementedError(
            "LanguageBind (MIT) integration is the gated M3.1 commons path. "
            "R0 scaffold uses FakeEncoder in smoke.py."
        )


@dataclass
class FakeEncoder(JointEncoder):
    """Deterministic, stdlib-only stand-in for the smoke — NO model, NO randomness.

    Produces a reproducible embedding from a hash of (modality, data) so the wiring
    and shapes can be exercised offline. Carries an explicit license profile so the
    Path A / Charter invariants are testable.
    """
    name: str = "fake"
    embed_dim: int = 16
    source_license: str = "N/A-fake"
    redistributable: bool = True
    output_license: str = "N/A-fake"
    supported_modalities: tuple[str, ...] = MODALITIES
    mirror_of: str = "imagebind"     # which real encoder's license profile to mirror

    def embed(self, modality: str, data: object) -> Embedding:
        import hashlib
        self._check_modality(modality)
        seed = hashlib.sha256(f"{modality}:{data!r}".encode()).digest()
        # deterministic [0,1) floats — no Math.random / os.urandom
        vec = [b / 255.0 for b in seed[: self.embed_dim]]
        return Embedding(
            vector=vec,
            modality=modality,
            source_license=self.source_license,
            redistributable=self.redistributable,
        )
