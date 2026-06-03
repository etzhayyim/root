# aratame_sca_scan

**Cell**: `AratameScaScanCell` (`magatama.cells.aratame_sca_scan`)
**Actor**: aratame (改め) — `did:web:aratame.etzhayyim.com`
**ADR**: ADR-2606024000 (R0 scaffold) — SSoT
**Status**: R0 scaffold — import-time `RuntimeError` until R1.

## Purpose

Run OSS SCA (OSV-Scanner / Trivy) and reuse giemon purl_vuln_match (purl→CVE, ADR-2605312330) over the dependency manifests; emit dependencyFindings.

## Gates

G3 (read-only) + G5 (OSS-tooling-only)

## Output Lexicon(s)

`com.etzhayyim.aratame.dependencyFinding`

## Ceiling (CRITICAL — IMMUTABLE)

READ-ONLY / STATIC-ONLY (never executes target code, never writes the repo) ·
OSS-TOOLING-ONLY (Charter Rider §2(e)) · NON-ADJUDICATING (evidence, not a
target-list) · NO PLATFORM-HELD KEY (ADR-2605231525) · Murakumo-only inference
(ADR-2605215000 — `gemma4-26b-a4b` via judah LiteLLM `127.0.0.1:4000`).
