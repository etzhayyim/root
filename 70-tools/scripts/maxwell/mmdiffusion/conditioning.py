"""DiffusionConditioner — backbone-agnostic cross-attention conditioning hook.

Takes the ProjectionAdapter's (L×C) context and presents it to a frozen diffusion
backbone (DiT / UNet) as cross-attention key/value context. Backbone-agnostic: the
real `denoise_step` binds to a concrete backbone at the gated M3.1 step.

Carries the Charter gates that apply at generation time:
  G1 Murakumo-only · G3 no-biometric · G4 internal-commerce firewall · G5 honest R0.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from joint_encoder import JointEncoder, MURAKUMO_ONLY
from projection import ProjectionAdapter


class BiometricUseError(RuntimeError):
    """G3 — the image modality must not be pointed at faces / biometric identification
    (manako on-device, no-biometric pattern). Raised when a caller flags biometric intent."""


def assert_no_biometric(intent: str) -> None:
    banned = {"face-id", "biometric", "person-id", "face-recognition", "gait-id"}
    if intent in banned:
        raise BiometricUseError(f"G3 no-biometric: refused intent {intent!r}")


@dataclass
class GenerationRequest:
    modality: str
    data: object
    intent: str = "general"          # checked against G3 banned set
    commercial_context: bool = False  # G4 — is this an SBT↔SBT internal-economy call?


@dataclass
class DiffusionConditioner:
    encoder: JointEncoder
    projection: ProjectionAdapter
    backbone: str = "dit-frozen"     # placeholder; bound at M3.1

    def assert_charter_gates(self, req: GenerationRequest) -> None:
        # G1
        if not MURAKUMO_ONLY:
            raise RuntimeError("G1: inference must be Murakumo-only (Rider §2(i)).")
        # G3
        assert_no_biometric(req.intent)
        # G4 — Path A firewall: a non-redistributable (CC-BY-NC) encoder's outputs may
        # NOT feed Charter-permitted internal commerce.
        if req.commercial_context and not self.encoder.redistributable:
            raise RuntimeError(
                "G4: CC-BY-NC outputs cannot feed the SBT↔SBT internal economy "
                f"(encoder {self.encoder.name}, license {self.encoder.output_license}). "
                "Use the LanguageBind/MIT path for commons-commercial contexts."
            )

    def build_context(self, req: GenerationRequest, *, fake: bool = False):
        """Encode → project → return the (L×C) cross-attn context + its license tag."""
        self.assert_charter_gates(req)
        z = self.encoder.embed(req.modality, req.data)
        ctx = (self.projection.fake_forward(z) if fake
               else self.projection.forward(z))
        return ctx, self.encoder.output_license

    def denoise_step(self, *args, **kwargs):
        raise NotImplementedError(
            "Frozen diffusion backbone binding is the gated M3.1 step (internal, "
            "Murakumo-only). R0 scaffold proves wiring/shapes via build_context(fake=True)."
        )
