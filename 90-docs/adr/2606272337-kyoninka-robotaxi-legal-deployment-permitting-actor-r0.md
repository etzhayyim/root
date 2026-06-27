# ADR-2606272337 — kyoninka 許認可: robotaxi legal-deployment permitting actor (R0)

- Status: proposed (R0)
- Date: 2026-06-27
- Tier: B
- DID: `did:web:etzhayyim.com:actor:kyoninka`
- Relates to: robotaxi-actor (AR1 ⊣ SafetyGovernor) / ai-gftd-itonami (ops-LLM ⊣
  CertGovernor) — workspace actor lineage; chigiri 契 (ADR-2605262700, legal-
  procedure substrate / UPL boundary) / toritsugi 取次 / ooyake 公
  (ADR-2606021600, government atlas + BPMN) / hinagata 雛形 / tate 盾 —
  etzhayyim legal lineage; no-server-key (ADR-2605231525); kotoba-canonical-state
  (ADR-2605312345); actor-profile + did (ADR-2606013800); entity-as-actor
  registration (ADR-2606042330)

## Context

A driverless-taxi service may not carry a passenger on a public road until it
holds the right permits, licences, insurance and filings **for that
jurisdiction** — and the specifics differ sharply (JP 改正道路交通法 特定自動運行 +
道路運送車両法 型式指定 + 道路運送法; US-CA DMV deployment + CPUC passenger +
FMVSS; DE StVG AFGBV + UNECE + GDPR; SG LTA). "Can we launch here?" is a
liability decision, not a model question. Asking an LLM directly fails the way
liability decisions fail: hallucinated compliance ("you're clear" when the CPUC
permit was never granted or the type approval expired), jurisdiction blur
(applying one regime's framework to another), and silent actuation (an agent
that "files" or "activates" on its own judgement).

etzhayyim already has the legal-procedure neighbours (chigiri substrate, toritsugi
concierge, ooyake atlas) and the mobility bodies (wadachi/tazuna/ainori), but no
actor that decides **deployment legality** and renders the 手続き publicly.

## Decision

Build kyoninka as the **fourth instance of the workspace actor pattern**, fitted
to the etzhayyim platform:

1. **Containment + independent governor + immutable ledger.** A contained
   **reg-LLM** returns *proposals only* (`:effect :assessment`, recommendation +
   cited facts). An independent **PermitGovernor** censors every proposal against
   hard legal invariants over the EAVT ground datoms and dispositions it
   commit / hold / human-approval. Single invariant: **observe → recommend only
   — the actor never grants a permit and never activates a vehicle** (G1, the 許認可
   analog of robotaxi-actor's safety contract).

2. **A public-road launch always routes to a human regulatory authority** (G3):
   `interrupt-before :request-approval`. A clean checklist is necessary, never
   sufficient — the named authority (公安委員会 / 運輸局 / DMV / CPUC / KBA / LTA)
   signs the go-live.

3. **Hard invariants are unoverridable** (G4): jurisdiction recognized · target
   SAE level ≤ jurisdiction max · every mandatory permit granted & unexpired ·
   liability cover ≥ statutory minimum · every mandatory filing accepted ·
   remote operator present when required · no-actuation. No human can approve
   past a missing permit or below-floor cover.

4. **The jurisdiction rulebook is data** (G5): mandatory permits, minimum cover,
   filings, max SAE level and authority are attributes of a `jurisdiction`
   ground datom. Adding/correcting a jurisdiction is a reviewed transaction
   (counsel-supervised), not a code change.

5. **kotoba-native, observe-only** (G6/G7): jurisdiction/deployment/permit/
   insurance/filing/assessment are kotoba Datoms; the append-only ledger is the
   permitting genealogy; the Store is `:db-api`-driven (MemStore ≡ DatomicStore ≡
   kotoba pod). Non-adjudicating, not the practice of law (G8, shared UPL
   boundary with chigiri). reg-LLM inference Murakumo-default (G9); no
   server-held key (G10).

6. **The 手続き is visualized on the web.** `methods/site_gen.cljc` renders a
   crawlable static site (`etzhayyim.com/kyoninka`): the procedure flow, the
   per-jurisdiction requirement matrix, and the per-deployment readiness board
   (✓/✗ each requirement → verdict + which authority signs). No ad/tracking,
   non-adjudicating disclaimer on every page (the tate 盾 site idiom).

## Implementation (R0)

- **Runnable engine**: `orgs/etzhayyim/kyoninka-actor` — the langgraph-clj
  StateGraph actor (reg-LLM ⊣ PermitGovernor), robotaxi-actor / itonami sibling;
  10 contract tests green; `MemStore ≡ DatomicStore` proven; `clojure -M:dev:run`
  drives JP-clean→authority-signoff, CA-deficient→HARD HOLD, ZZ-over-level→HOLD,
  pre-application auto-commit, phase-0 held.
- **Platform form**: `20-actors/kyoninka/` — `manifest.edn` (Tier-B profile,
  registered into INFRA_ACTORS via `bb gen:tier-b-actors`), `methods/procedure.cljc`
  (the rulebook + invariants, dependency-free `.cljc`, bb-runnable),
  `methods/site_gen.cljc` (the web viz), `methods/test_procedure.cljc` (5 tests /
  14 assertions green). Static `public/actor/kyoninka/{did,profile}.json` +
  generated `public/kyoninka/` site.

## Consequences

- The DID resolves and the actor appears in `/search`; the 手続き is publicly
  legible at `etzhayyim.com/kyoninka` (worker deploy + Search Console = operator
  step).
- The reg-LLM can be upgraded / swapped to a real model without touching the
  legal guarantees, which live in the governor and the data.
- The rulebook is illustrative until curated with counsel per jurisdiction;
  because it is data, that curation is a reviewed transaction.

## Non-goals

- Not a law firm; non-adjudicating (general legal information). N: granting a
  permit, activating a vehicle, auto-launching, or adjudicating a dispute of law.
- Live ingest / binding authority sign-off = Council Lv6+ + operator (G8).
