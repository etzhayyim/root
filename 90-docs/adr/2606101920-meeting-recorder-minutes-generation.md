---
id: adr-2606101920
title: meeting-recorder 議事録 (meeting minutes) generation — E2E minutes record + Murakumo-gated generator
status: proposed
doc_type: adr
topic: meeting-recorder minutes generation
authoritative: true
last_verified: 2026-06-10
related:
  - 90-docs/260422-meeting-recorder-session-summary.md
  - ADR-2605181100 (kotoba E2E encrypted-record envelope)
  - ADR-2605215000 (Murakumo-only inference, no commercial GPU)
  - ADR-2606011400 (Consensys product-front / infra-back)
depends_on:
  - ADR-2605181100
  - ADR-2605215000
---

# meeting-recorder 議事録 generation — E2E minutes record + Murakumo-gated generator

## Context

The 2026-04-22 meeting-recorder session (`90-docs/260422-meeting-recorder-session-summary.md`)
delivered the recorder actor R0: consent-gated join, audio/video chunking to B2,
whisper transcription (Murakumo MLX), `signal:v1:` transcript encryption, and a
mock-path E2E smoke. **Minutes / action-item generation (議事録) was designed in
intent only — never coded.** The 2026-06-02 migration classification
(`90-docs/MIGRATION-STATUS.md`, PR #844) confirmed meeting-recorder as
**vendor-resident** for execution (bot join/capture, GPU/MLX whisper, B2 media
custody, consentToken custody), while the WAVE 2 rw-free front
(`60-apps/etzhayyim-project-meeting-recorder/rw-free/`) carries the
etzhayyim-aligned data layer: plaintext provider catalog + kotoba-E2E
session / recordingChunk / transcriptSegment records (ADR-2605181100).

The missing 議事録 layer is a pure data + inference transform over transcript
segments the caller can already decrypt — it belongs in the rw-free front, not
in the vendor execution plane.

## Decision

1. **Fourth E2E inner type** —
   `com.etzhayyim.apps.meetingRecorder.meetingMinutes` (lexicon added beside the
   existing 7): `summary` + `decisions[]` + `actionItems[{description,
   ownerHash?, dueDate?}]` + `topics[]` + `participantHashes[]` + provenance
   (`generator`, `model?`, `sourceSegmentCount`, `generatedAt`). The whole body
   is sealed via `sdk.encryptedWrite` (read-cap = owner DID + explicit
   `recipients`), same envelope as the transcript it derives from. PII posture
   is inherited: only `speakerHash`-derived owner attribution, no display
   names, no provider IDs. AT-Lexicon no-float rule respected (all integers).
   rkey = `minutes-{sessionId}`; regeneration re-seals under the same rkey and
   reads resolve to the latest record.

2. **Two generators, no silent downgrade** (implemented in
   `rw-free/src/minutes.ts`):
   - **extractive** (default, canonical R0): deterministic, hermetic,
     stdlib-only. Sentence split (ja + en punctuation), marker-based decision
     extraction (決定/合意/承認/agreed/approved/…), marker-based action items
     (お願いします/対応します/will do/action item/…) with `ownerHash` from the
     segment speaker and ISO `dueDate` capture, keyword topics
     (latin ≥3 chars + kanji/katakana runs ≥2, stopword-filtered), lead +
     keyword-overlap summary. Offline-safe; never reaches the network.
   - **murakumo** (gated): Murakumo LLM through the LiteLLM loopback gateway
     (`127.0.0.1:4000`, default model `gemma3:4b`) per ADR-2605215000 (G4
     Murakumo-only). Refused-by-default membrane, same shape as karakuri
     `nl_plan`: requires BOTH the caller's `allowLive` flag AND the operator
     gate env `MEETING_RECORDER_LIVE_LLM=1`. A refused or failed live call is
     an honest `rejected` — never a quiet fallback to extractive. Non-loopback
     `MURAKUMO_ENDPOINT` is a hard G4 violation (tested).

3. **Lexicons** — `meetingMinutes.json` (record), `generateMinutes.json`
   (procedure: sessionId / lang / allowLive / maxSegments / recipients),
   `getMinutes.json` (query), in
   `00-contracts/lexicons/com/etzhayyim/etzhayyim/apps/meetingRecorder/`.

4. **API surface** (rw-free barrel): `generateMinutes` / `getMinutes` /
   `listMinutes` / `countMinutes` + pure `extractiveMinutes` /
   `murakumoMinutes`. `coverage()` now reports `meetingMinutesCount` as its own
   inner-type count.

5. **Stays vendor-side (out of scope here)** — wiring `generateMinutes` into
   the vendor control-plane Worker/appview (Kysely/Hyperdrive substrate is
   vendor-resident per the 06-02 classification), auto-generation on
   `leaveMeeting`, and the three provider SDK adapters (Teams .NET 8 sidecar,
   Meet Media API gRPC stream, Zoom C++ sidecar) — all flagged 大作業 in the
   04-22 summary and requiring vendor credentials.

## Consequences

- Circleback-style 参加 → 録画 → 文字起こし → **議事録** chain is now complete
  at the data-contract + generation-logic level on the etzhayyim-aligned path;
  the live provider adapters remain the vendor-side gap.
- The extractive default means minutes exist for every transcribed session
  with zero inference cost and zero gate friction; Murakumo upgrades quality
  when the operator opens the gate.
- One more inner type shares the default wrapper collection — every scan
  filters by its own `innerType` (existing rule, test-enforced; cross-session
  and cross-type leakage covered by tests: 16/16 green, tsc clean).
- The substrate never sees plaintext minutes; sharing is an explicit
  per-record `recipients` grant, consistent with `getTranscript` semantics.

## Alternatives Considered

- **Generate minutes vendor-side in the container (`transcript-pipeline.ts`
  follow-on)** — rejected for now: it would couple 議事録 to the
  vendor-resident execution plane and the prohibited-substrate Worker
  (Kysely/Hyperdrive), and duplicate logic the rw-free front needs anyway.
  The vendor plane can call the same pure generators later.
- **Silent fallback extractive ← murakumo on live failure** — rejected:
  violates the honest-rejection membrane pattern (karakuri G6) and hides
  inference-path drift from the operator.
- **Per-language LLM-only generation** — rejected: breaks hermetic tests and
  the Murakumo-only gate would make minutes unavailable whenever the fleet is
  unreachable.
- **Float confidence / score fields on minutes** — rejected: AT-Lexicon
  no-float rule (the transcript layer already migrated confidence to
  `confidencePct` integer).

## References

- `90-docs/260422-meeting-recorder-session-summary.md` — R0 scope + "What's NOT yet done"
- `90-docs/MIGRATION-STATUS.md` § meeting-recorder (vendor-resident classification, PR #844)
- ADR-2605181100 — kotoba E2E encrypted-record envelope
- ADR-2605215000 — Murakumo-only inference invariant
- ADR-2606011400 — Consensys product-front / infra-back split
- `20-actors/karakuri/methods/nl_plan.py` — refused-by-default live-LLM membrane precedent
- `60-apps/etzhayyim-project-meeting-recorder/rw-free/` — implementation + tests
