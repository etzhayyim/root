# aratame_sast_scan

**Cell**: `AratameSastScanCell` (`magatama.cells.aratame_sast_scan`)
**Actor**: aratame (改め) — `did:web:aratame.etzhayyim.com`
**ADR**: ADR-2606024000 (R0 scaffold) — SSoT
**Status**: R0 scaffold — import-time `RuntimeError` until R1.

## Purpose

Run OSS SAST (Semgrep OSS / CodeQL OSS terms) over the cloned source and emit candidate SAST vulnFindings.

## Gates

G3 (read-only) + G5 (OSS-tooling-only) + G9 (defensive-only)

## Output Lexicon(s)

`com.etzhayyim.aratame.vulnFinding`

## Ceiling (CRITICAL — IMMUTABLE)

READ-ONLY / STATIC-ONLY (never executes target code, never writes the repo) ·
OSS-TOOLING-ONLY (Charter Rider §2(e)) · NON-ADJUDICATING (evidence, not a
target-list) · NO PLATFORM-HELD KEY (ADR-2605231525) · Murakumo-only inference
(ADR-2605215000 — `gemma4-26b-a4b` via judah LiteLLM `127.0.0.1:4000`).
