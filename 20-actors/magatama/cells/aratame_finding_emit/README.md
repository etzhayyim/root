# aratame_finding_emit

**Cell**: `AratameFindingEmitCell` (`magatama.cells.aratame_finding_emit`)
**Actor**: aratame (改め) — `did:web:aratame.etzhayyim.com`
**ADR**: ADR-2606024000 (R0 scaffold) — SSoT
**Status**: R0 scaffold — import-time `RuntimeError` until R1.

## Purpose

Emit tsukuroi-compatible com.etzhayyim.aratame.vulnFinding plus an aggregate inspectionReport to kotoba datom + MST; remediation handoff to tsukuroi (propose-only).

## Gates

G2 (append-only datom) + G13 (propose-only handoff)

## Output Lexicon(s)

`com.etzhayyim.aratame.inspectionReport`

## Ceiling (CRITICAL — IMMUTABLE)

READ-ONLY / STATIC-ONLY (never executes target code, never writes the repo) ·
OSS-TOOLING-ONLY (Charter Rider §2(e)) · NON-ADJUDICATING (evidence, not a
target-list) · NO PLATFORM-HELD KEY (ADR-2605231525) · Murakumo-only inference
(ADR-2605215000 — `gemma4-26b-a4b` via judah LiteLLM `127.0.0.1:4000`).
