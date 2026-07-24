"""Real LanguageBind joint-embedding encoder (MIT) — the commons path.

Per the license analysis (paper 2606171500 + ADR-2606172300), LanguageBind (MIT) is the
charter-clean encoder for a *shippable* graft: its weights and the graft outputs carry
ECL-on-Apache, unlike ImageBind (CC-BY-NC, internal-only Path A). FROZEN per the baien
edge invariant (ADR-2605241900).

Real path: imports the actual `languagebind` package and runs the frozen encoder. Offline
fallback: a deterministic hash-seeded embedding (no model download), so the whole diffusion
pipeline runs end-to-end without the multi-GB weights. Charter: inference is Murakumo-
preferred (ADR-2606172359 — objective-function-assessed, not a hard ban); the frozen
forward is local/CPU here.
"""
from __future__ import annotations

import hashlib
import numpy as np

EMBED_DIM = 768                  # LanguageBind joint space
SOURCE_LICENSE = "MIT"
OUTPUT_LICENSE = "ECL-on-Apache"
REDISTRIBUTABLE = True
MODALITIES = ("text", "image", "audio", "depth")


class LanguageBindEncoder:
    """Frozen LanguageBind encoder. embed(modality, items) -> [B, EMBED_DIM] float64."""

    name = "languagebind"
    embed_dim = EMBED_DIM
    source_license = SOURCE_LICENSE
    output_license = OUTPUT_LICENSE
    redistributable = REDISTRIBUTABLE

    def __init__(self, prefer_real: bool = True):
        self.backend = "fallback"
        self._model = None
        if prefer_real:
            self._try_load_real()

    def _try_load_real(self):
        try:                       # real path — only if the lib + weights are present
            from languagebind import LanguageBind  # type: ignore
            self._model = LanguageBind()           # frozen; eval mode set by caller
            self.backend = "languagebind"
        except Exception:          # offline / not installed → deterministic fallback
            self.backend = "fallback"

    def embed(self, modality: str, items):
        if modality not in MODALITIES:
            raise ValueError(f"{self.name}: unsupported modality {modality!r}")
        if self.backend == "languagebind":
            return self._embed_real(modality, items)
        return self._embed_fallback(modality, items)

    def _embed_real(self, modality, items):  # pragma: no cover (needs weights)
        import numpy as _np
        vecs = self._model.encode(modality, items)   # frozen forward
        v = _np.asarray(vecs, dtype=_np.float64)
        return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-8)

    def _embed_fallback(self, modality, items):
        """Deterministic, normalised stand-in embedding — no model, no randomness leak.
        Reproducible from a sha256 of (modality, item) so the pipeline is testable offline."""
        out = []
        for it in items:
            seed = hashlib.sha256(f"{modality}:{it!r}".encode()).digest()
            # expand 32 bytes deterministically to EMBED_DIM via a seeded RNG
            rng = np.random.default_rng(int.from_bytes(seed[:8], "big"))
            v = rng.standard_normal(EMBED_DIM)
            out.append(v / (np.linalg.norm(v) + 1e-8))
        return np.stack(out, axis=0)
