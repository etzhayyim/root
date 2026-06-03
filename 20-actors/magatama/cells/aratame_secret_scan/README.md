# aratame_secret_scan

**Cell**: `AratameSecretScanCell` (`magatama.cells.aratame_secret_scan`)
**Actor**: aratame (改め) — `did:web:aratame.etzhayyim.com`
**ADR**: ADR-2606024000 (R0 scaffold) — SSoT
**Status**: R0 scaffold — import-time `RuntimeError` until R1.

## Purpose

Run OSS secret detection (gitleaks / trufflehog OSS); store any detected secret ONLY as an encrypted envelope ref (com.etzhayyim.encrypted.*, ADR-2605181100), never plaintext.

## Gates

G3 (read-only) + G7 (secret-encryption)

## Output Lexicon(s)

`com.etzhayyim.aratame.secretFinding`

## Ceiling (CRITICAL — IMMUTABLE)

READ-ONLY / STATIC-ONLY (never executes target code, never writes the repo) ·
OSS-TOOLING-ONLY (Charter Rider §2(e)) · NON-ADJUDICATING (evidence, not a
target-list) · NO PLATFORM-HELD KEY (ADR-2605231525) · Murakumo-only inference
(ADR-2605215000 — `gemma4-26b-a4b` via judah LiteLLM `127.0.0.1:4000`).
