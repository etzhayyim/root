# aratame_repo_intake

**Cell**: `AratameRepoIntakeCell` (`magatama.cells.aratame_repo_intake`)
**Actor**: aratame (改め) — `did:web:aratame.etzhayyim.com`
**ADR**: ADR-2606024000 (R0 scaffold) — SSoT
**Status**: R0 scaffold — import-time `RuntimeError` until R1.

## Purpose

Validate the InspectionMandate (owner+authority dual-sig) and shallow READ-ONLY clone the attested repo@ref into the egress-restricted aratame-scan sandbox.

## Gates

G3 (read-only/static-only) + G4 (dual-sig mandate) + G6 (no platform-held key) + G11 (egress-restricted sandbox)

## Output Lexicon(s)

`com.etzhayyim.aratame.inspectionMandate`

## Ceiling (CRITICAL — IMMUTABLE)

READ-ONLY / STATIC-ONLY (never executes target code, never writes the repo) ·
OSS-TOOLING-ONLY (Charter Rider §2(e)) · NON-ADJUDICATING (evidence, not a
target-list) · NO PLATFORM-HELD KEY (ADR-2605231525) · Murakumo-only inference
(ADR-2605215000 — `gemma4-26b-a4b` via judah LiteLLM `127.0.0.1:4000`).
