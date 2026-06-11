---
id: adr-2606061600-gov-procedures-publish-and-ameno-kotoba-conversation
title: "ADR-2606061600: Government procedures published on etzhayyim.com by administrative unit + kotoba-grounded browser conversation (ameno gemma4-e4b)"
status: accepted
doc_type: adr
topic: gov-procedures-publish-and-ameno-kotoba-conversation
authoritative: true
last_verified: 2026-06-06
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "R0 code + tests; live deploy + UI build stay Council/operator gated (G11)"
authoritative_for:
  - 50-infra/etzhayyim-did-web/src/registry/gov-procedures.gen.ts
  - 70-tools/scripts/entity-actors/gen-gov-procedures.py
  - 70-tools/scripts/audit/test_gov_procedures_gen_fresh.py
  - 40-engine/llm/inference/ameno/src/kotoba-ground.ts
depends_on:
  - 2606061200
  - 2606021600
  - 2606042330
  - 2605215000
  - 2605241900
  - 2605231525
related:
  - 2606013800
  - 2605190824
  - 2605312345
supersedes: []
superseded_by: []
---

# ADR-2606061600: Government procedures published on etzhayyim.com by administrative unit + kotoba-grounded browser conversation

**Status**: accepted
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

# Context

Answers 「この手続きを http://etzhayyim.com/ で actor として行政単位で細かく公開、また
gemma4 e4b で browser 上の ameno, 推論で会話が kotoba ベースで進むように.」

Two gaps after the coverage/maturity expansion (ADR-2606061200):

1. **Publish gap** — the ~157 `:gov.procedure` records (ooyake, across 50
   jurisdictions, projected from the toritsugi registry) were *registered* but
   had **no read surface** on the apex Worker. The Worker served gov *units* as
   entity-actors (`/actor/gov-<…>/did.json`) and the unit atlas
   (`/.well-known/gov-units.json`) but exposed no procedures.
2. **Conversation gap** — `gemma4-e4b` already runs **in the browser** via ameno
   (MediaPipe LiteRT `.task`, ungated; ADR-2605190824 / 2605241900 edge carve-out
   under the Murakumo-only invariant ADR-2605215000). But the conversation was
   ungrounded — it answered from parametric memory, not from etzhayyim's kotoba
   procedure data. There was no "kotoba-based" grounding path.

# Decision

## A. Publish procedures FINELY BY ADMINISTRATIVE UNIT (apex Worker)

- `70-tools/scripts/entity-actors/gen-gov-procedures.py` compiles every ooyake
  `:gov.procedure` into `50-infra/etzhayyim-did-web/src/registry/gov-procedures.gen.ts`,
  grouped under its **owning gov entity-actor handle** (`gov.<id>` → `gov-<id>`,
  the gen-entity-handles transform). 157 procedures / 51 administrative units /
  50 jurisdictions; small enough to compile into the Worker (no KV).
- Two new Worker read routes (GET/HEAD, cookie-free, CORS, no-server-key):
  - `GET /.well-known/gov-procedures.json` — the full index.
  - `GET /actor/<gov-handle>/procedures.json` — one administrative unit's
    procedures (e.g. `gov-jpn` → passport / licence / business-reg / tax …;
    `gov-gbr` → Companies House / DVLA / HM Passport).
- **Charter posture (mirror, ADR-2606021600 / 2606042330):** an OBSERVATIONAL
  catalog of *where/how* a public procedure is done — never the government, never
  an official channel, never filing on anyone's behalf (that is toritsugi,
  gated). Every row carries sourcing + verification-status; all are
  `:representative` / `:unverified-seed` (G5 — never authoritative coverage).
- Side-effect: regenerated `entity-handles.gov.gen.ts` to include `gov-dnk`
  (Denmark, added in ADR-2606061200), so every procedure owner handle resolves.

## B. kotoba-grounded browser conversation (ameno gemma4-e4b)

- `40-engine/llm/inference/ameno/src/kotoba-ground.ts` (+ `/kotoba-ground`
  export): `fetchGovProcedures()` loads the published index once; pure CJK-aware
  `retrieveProcedures()` selects records relevant to the user turn;
  `buildKotobaContext()` / `groundedMessages()` compose a grounded system prompt.
- The grounding prompt **forbids** the model from claiming to BE the government,
  to be an official channel, or to file on the member's behalf; it must answer
  ONLY from the supplied records, cite each `source:` provenance, say so when no
  record matches (no invention), and surface the `unverified-seed` caveat.
- Wired into the ameno Svelte UI (`App.svelte`) as a **「kotoba 行政手続き」**
  toggle: when on, `handleSend` appends the retrieved kotoba context to the
  system prompt before browser inference. Inference stays the edge carve-out
  (gemma4-e4b on-device WebGPU/MediaPipe); this module only shapes the prompt and
  never calls a server LLM.

## C. Freshness / drift guard (maturity)

- `70-tools/scripts/audit/test_gov_procedures_gen_fresh.py` (R0-safe, fail-closed)
  recomputes the expected projection from ooyake and asserts the committed
  `gov-procedures.gen.ts` matches in both the procedure-id set and the exported
  counts — so editing ooyake without re-running the generator is caught. Mirrors
  the ooyake→atlas freshness guard (ADR-2606061200).

# Consequences

- A member (or any client) can read the world's administrative procedures keyed
  to the owning government unit, and a fully browser-local gemma4-e4b assistant
  can answer procedure questions grounded on that kotoba data with provenance.
- **Verified surfaces:** worker tests 30/30 (incl. 6 new gov-procedures +
  mirror/honesty invariants), ameno kotoba-ground 9/9, audit suite green incl.
  the new freshness guard; worker tsc clean.
- **ZERO invariant amendments** — strengthens no-server-key (ADR-2605231525),
  observational-mirror (ADR-2606021600 / 2606042330), Murakumo-only edge
  carve-out (ADR-2605215000 / 2605241900), kotoba-canonical-state
  (ADR-2605312345). All rows remain `:representative` / `:unverified-seed`.

# Honest limits (R0)

- **Not deployed.** Code is built + tested; `wrangler deploy` to etzhayyim.com is
  outward-facing and Council+operator gated (G11). KV is not required (the index
  is compiled into the Worker).
- The ameno Svelte app's `node_modules` are not installed in this environment, so
  `svelte-check` / `vite build` were not run; the package-level kotoba-ground
  module is type-checked (only the pre-existing `@webgpu/types` dep is missing)
  and unit-tested. Real-device verification (Chrome → toggle → grounded answer)
  is deferred to a build+deploy step.
- Procedure rows are wayfinding scaffold needing primary-source verification
  before any live use (toritsugi G14); the publish surface never files anything.
