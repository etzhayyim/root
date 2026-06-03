# aratame_triage_synthesis

**Cell**: `AratameTriageSynthesisCell` (`magatama.cells.aratame_triage_synthesis`)
**Actor**: aratame (改め) — `did:web:aratame.etzhayyim.com`
**ADR**: ADR-2606024000 (R0 scaffold) — SSoT
**Status**: R0 scaffold — import-time `RuntimeError` until R1.

## Purpose

Murakumo-only LLM (gemma4-26b-a4b via judah LiteLLM 127.0.0.1:4000) dedups, normalizes severity, and triages false-positives; emits NON-adjudicating contextual notes only.

## Gates

G8 (non-adjudicating) + G10 (Murakumo-only)

## Output Lexicon(s)

`com.etzhayyim.aratame.vulnFinding`

## Ceiling (CRITICAL — IMMUTABLE)

READ-ONLY / STATIC-ONLY (never executes target code, never writes the repo) ·
OSS-TOOLING-ONLY (Charter Rider §2(e)) · NON-ADJUDICATING (evidence, not a
target-list) · NO PLATFORM-HELD KEY (ADR-2605231525) · Murakumo-only inference
(ADR-2605215000 — `gemma4-26b-a4b` via judah LiteLLM `127.0.0.1:4000`).
