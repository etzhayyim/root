"""AratameTriageSynthesisCell — aratame R0 Pregel cell.

Per ADR-2606024000 (aratame 改め — authorized GitHub-repo source-code
vulnerability-inspection actor; the static-source diagnosis sibling of akuma 悪魔
(ADR-2605151400) and the upstream finding source for tsukuroi 繕い
(ADR-2605291500)).

Purpose: Murakumo-only LLM (gemma4-26b-a4b via judah LiteLLM 127.0.0.1:4000) dedups, normalizes severity, and triages false-positives; emits NON-adjudicating contextual notes only.

Constitutional ceiling (CRITICAL — IMMUTABLE): READ-ONLY / STATIC-ONLY (never
executes target code, never writes to the repo) + OSS-TOOLING-ONLY (Charter Rider
§2(e)) + NON-ADJUDICATING (findings are evidence, not an exploitation target-list)
+ NO PLATFORM-HELD KEY (ADR-2605231525) + Murakumo-only inference (ADR-2605215000,
gemma4-26b-a4b via judah LiteLLM 127.0.0.1:4000). Gates: G8 (non-adjudicating) + G10 (Murakumo-only).
Output Lexicon(s): com.etzhayyim.aratame.vulnFinding.

R0 scaffold — import-time RuntimeError until R1.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# R1 activation gate (ADR-2606024000 §"R0 → R3")
# ─────────────────────────────────────────────────────────────────────────────
#
# This cell is scaffold-only until ALL of the following hold:
#
#   1. Council Lv6+ ≥3 multisig has attested the aratame master charter
#      ADR-2606024000 (post Bootstrap Council Seat 2-5 RFP close 2026-06-19).
#   2. the Murakumo judah LiteLLM endpoint is registered AND the gemma4-26b-a4b
#      model is provisioned on the fleet (G10 Murakumo-only inference; no vendor API).
#
# Any None below → import-time RuntimeError.

COUNCIL_CHARTER_ATTESTATION_TX_HASH: str | None = None
MURAKUMO_JUDAH_ENDPOINT: str | None = None
MURAKUMO_MODEL_ID: str | None = None  # target "gemma4-26b-a4b"

if (
    COUNCIL_CHARTER_ATTESTATION_TX_HASH is None
    or MURAKUMO_JUDAH_ENDPOINT is None
    or MURAKUMO_MODEL_ID is None
):
    raise RuntimeError(
        "aratame R0 scaffold: activate via Council ADR-2606024000 "
        "post-ratification — Council has not attested the aratame master "
        "charter (Lv6+ ≥3), and/or MURAKUMO_JUDAH_ENDPOINT / MURAKUMO_MODEL_ID "
        "is unset (G10 Murakumo-only inference: gemma4-26b-a4b via judah LiteLLM "
        "127.0.0.1:4000; no vendor API). Do not deploy. READ-ONLY / STATIC-ONLY "
        "/ OSS-TOOLING-ONLY / NON-ADJUDICATING / NO-PLATFORM-HELD-KEY ceiling is "
        "constitutional."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pregel super-step skeleton (only reached after the Council gate is removed)
# ─────────────────────────────────────────────────────────────────────────────
#
# from pymagatama.organism import PregelCell
#
# class AratameTriageSynthesisCell(PregelCell):
#     process_step = "aratame_triage_synthesis"
#     pregel_tier = "B"
#     murakumo_node = "levi"   # proposed; security-review tribe
#
#     def super_step(self, msg, prior):
#         raise NotImplementedError("aratame R1")


__all__ = ["AratameTriageSynthesisCell"]
