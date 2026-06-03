# aratame_charter_rider_scan

**Cell**: `AratameCharterRiderScanCell` (`magatama.cells.aratame_charter_rider_scan`)
**Actor**: aratame (改め) — `did:web:aratame.etzhayyim.com`
**ADR**: ADR-2606024000 (R0 scaffold) — SSoT
**Status**: R0 scaffold — import-time `RuntimeError` until R1.

## Purpose

Run the Charter Rider §2(a)..(h) scan on every emitted text and reject any exploit/PoC content.

## Gates

G1 (Charter Rider scan) + G9 (defensive-only / no exploit)

## Output Lexicon(s)

`(gate cell — no new lexicon)`

## Ceiling (CRITICAL — IMMUTABLE)

READ-ONLY / STATIC-ONLY (never executes target code, never writes the repo) ·
OSS-TOOLING-ONLY (Charter Rider §2(e)) · NON-ADJUDICATING (evidence, not a
target-list) · NO PLATFORM-HELD KEY (ADR-2605231525) · Murakumo-only inference
(ADR-2605215000 — `gemma4-26b-a4b` via judah LiteLLM `127.0.0.1:4000`).
