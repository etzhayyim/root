---
id: adr-2606212200-hirameki-worldwide-patent-kg-mirror
title: "ADR-2606212200: hirameki 閃き — world public-patent KG-mirror (kotoba + DataLad), superseding the legacy RisingWave/B2 patent pipeline"
status: accepted
doc_type: adr
topic: hirameki-patent-kg-mirror
authoritative: true
last_verified: 2026-06-21
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Closes the worst world-coverage gap (patents ≈ 0.00002%) on the canonical kotoba substrate; OBSERVATION-only, charter-clean."
authoritative_for:
  - hirameki actor scope + gates (public-patent KG-mirror)
  - patent corpus persistence (kotoba EDN + DataLad/git-annex/IPFS, CIDv1)
  - relationship to tokigusuri (pharma subset) and open-patent app (generation)
depends_on:
  - 2605262130  # kotoba storage substrate (no RisingWave)
  - 2605312345  # kotoba Datom log = first-class canonical state
  - 2605241500  # DataLad + git-annex + IPFS dataset CID substrate
related:
  - 2604251024  # legacy patent bulk ingest (superseded)
  - 2606171300  # tokigusuri pharma patent-cliff mirror
  - 2604271830  # patent-expired pharma → open-seiyaku handoff
  - 2606022000  # kabuto supply-chain KG
  - 2606161730  # busshi commodity KG (mirror-lineage sibling)
supersedes:
  - 2604251024
superseded_by: []
---

# ADR-2606212200: hirameki 閃き — world public-patent KG-mirror (kotoba + DataLad)

**Status**: accepted
**Date**: 2026-06-21
**Deciders**: Jun Kawasaki

# Context

The roster has no actor that mirrors the world's PUBLIC patent corpus onto the canonical
substrate. The closest prior art is **ADR-2604251024** ("Patent bulk ingest + full
PDF/webp/OCR persistence to B2", status `proposed`), which observed that patent world-coverage
was effectively zero (`collected/world_total ≈ 0.00002%`, the single worst gap on the old
`mv_world_coverage_live`). But that ADR's architecture is **entirely on the deprecated
substrate**: RisingWave `vertex_*` tables, B2/Vultr blob storage, Hyperdrive bulk-INSERT,
BPMN-as-actor, AT-firehose follow-based ingest. All of these are now prohibited engineering
choices (ADR-2605262130 kotoba supersedes RisingWave; the repo-wide clj/bb-over-kotoba rule
supersedes BPMN/py pipelines). The two legacy apps that partially implement it
(`60-apps/etzhayyim-project-{patent,open-patent}`) write to RisingWave and are unmaintained.

Two adjacent actors exist but do **not** cover the general patent corpus:

- **tokigusuri 時薬** (ADR-2606171300) mirrors only the *pharmaceutical* patent-cliff /
  off-patent-access subset (edge-primary exclusivity-barrier → release), not all technology.
- **open-patent** (`60-apps/etzhayyim-project-open-patent`) *generates* new IP from a corpus;
  it consumes patents, it is not the mirror.

The user asked, directly: *is there an actor that ingests worldwide patent data and saves it
to EDN + DataLad?* There was not. This ADR creates it.

# Decision

Create **hirameki 閃き** — the world public-patent KG-mirror observatory — as a **clj-native,
kotoba-Datom-native** Tier-B actor, **superseding ADR-2604251024**. hirameki is the
all-technology **generalization of tokigusuri** (pharma is tokigusuri's; everything else is
hirameki's, N4 boundary).

## Scope

1. **Ingest** PUBLIC patent bibliographic data — USPTO PatentsView (CC0 bulk TSV), EPO OPS
   (free tier, citation/family), WIPO PATENTSCOPE (PCT) — bibliographic metadata only.
2. **Persist** on two layers:
   - **kotoba Datom log** — EAVT `[:db/add e a v]` (G5; no RisingWave/SQL); derived
     observations on an append-only, content-addressed, tamper-evident commit-DAG ledger.
   - **DataLad dataset substrate** (`80-data/hirameki-patents/`, ADR-2605241500: DataLad +
     git-annex + IPFS) — the corpus as canonical kotoba EDN, each artifact content-addressed
     to a **CIDv1 (raw, sha2-256) byte-identical to `ipfs add --cid-version=1 --raw-leaves`**
     (verified). The bounded R0 snapshot is git-tracked directly; the full ~200M-patent corpus
     goes via DataLad→IPFS (git-annex) as the operator G9 step.
3. **Analyze** (edge-primary, on read, no stored score):
   - per technology **FIELD** — exclusivity-**concentration** (top-assignee share + named-HHI,
     `:other` long tail excluded → a lower bound) vs **release-readiness** (expired +
     ½·expiring-soon + 0.4·open-licensed), weighted by disclosed standard-essentiality →
     **route** ∈ `{:release(解放), :open-license, :de-monopolization, :monitor}`.
   - per **PATENT** — the **release clock** (`years-to-expiry` → `release-status`).

The framing is the KG-mirror lineage's: exclusivity **concentration routed to RELEASE** — the
patent system's own bargain (disclosure now, public domain after the term) made into a map.

## Gates (proven by tests)

- **G1 release-map-not-verdict** — never a patent-busting / FTO-opinion / infringement-
  determination / per-company-verdict / patent-equity signal (`:hirameki/infringement-verdict`,
  `:hirameki/fto-opinion`, `:hirameki/equity-signal` unrepresentable).
- **G2 patent-is-object-never-holder** — a patent is the GATED OBJECT, never a 取-holder; only
  an assignee/holder imposes exclusivity (`:hirameki.patent/imposes-on` unrepresentable, in code
  + test). Mirrors tokigusuri's "a medicine is never a 取-holder source."
- **G3 non-adjudicating-no-forecast** — patent status/share are DISCLOSED office facts, never
  re-judged (no validity/novelty verdict), never a forecast.
- **G4 lawful-release-only** — release via statutory expiry / public-domain / voluntary open
  licensing (pledge / pool / FRAND-zero / MPP); circumvention / `:hirameki.patent/design-around`
  unrepresentable.
- **G5 kotoba-eavt-native** — state is kotoba Datoms (supersedes the 2604251024 RisingWave schema).
- **G6 aggregate-no-person-inventor** — assignee = org; no person-level inventor targeting
  (`:hirameki.inventor/person` unrepresentable); no-doxxing (tsumugi/keizu lineage).
- **G7 murakumo-only** — narration via Murakumo (DEFAULT-PREFERRED, Rider v3.3 §2(i)).
- **G8 no-server-key** — platform holds no key; live ingest + IPFS pin/IPNS = operator steps.
- **G9 datalad-content-addressed** — corpus in `80-data/hirameki-patents/` (DataLad/git-annex/
  IPFS), each artifact CIDv1 byte-identical to `ipfs add`; the loop never queries the API
  (snapshot = SoT).

## Non-goals

N1 not a patent-filing/prosecution/generation actor (that is open-patent) · N2 not legal
advice / FTO / patentability opinion (chigiri UPL boundary) · N3 not a patent-equity /
litigation-prediction signal · **N4 not the pharma patent-cliff specialist (tokigusuri 時薬)** ·
N5 no person/individual inventor data.

# Consequences

- **Positive**: the worst world-coverage gap is now addressable on the canonical substrate;
  the answer to "ingest worldwide patents → EDN + DataLad" is YES, clj-native and charter-clean.
  CID parity with `ipfs add` makes the corpus trustlessly verifiable. The mirror composes —
  citation edges will cross-link to tsumugi/kabuto; the release map feeds open-patent's
  prior-art search and tokigusuri's pharma handoff.
- **R0 honesty**: the seed is a BOUNDED `:representative` slice (11 fields across CPC A/B/C/G/H/Y
  + 7 exemplar patents). At broad CPC-subclass granularity real concentration is naturally
  diluted (top assignee ≤ ~18%), so `:de-monopolization` rarely fires at R0 — it is exercised by
  unit test and will surface at finer (subclass/SEP) granularity. Live authoritative ingest is
  the operator G8/G9 step.
- **Supersession**: ADR-2604251024 moves to `superseded`. Its data-source list (PatentsView CC0,
  EPO OPS free) is retained; its substrate (RisingWave/B2/BPMN) is discarded. The legacy
  `60-apps/etzhayyim-project-{patent,open-patent}` RisingWave tables are not migrated (open-patent
  keeps generating; its read path migrates to kotoba-kqe per ADR-2605262130 at Phase 2.5).
- **Cost**: a new ~200M-record DataLad/IPFS dataset is a real storage commitment, deferred to the
  operator G9 step; R0 commits only the bounded snapshot (no git-lfs).

# Alternatives Considered

1. **Resurrect ADR-2604251024 as-is (RisingWave/B2/BPMN)** — rejected: prohibited substrate;
   would re-introduce RisingWave + a platform-held B2 key (no-server-key violation).
2. **Extend tokigusuri to all technology** — rejected: tokigusuri's pharma-access framing
   (WHO-EML essentiality, MPP) is domain-specific; conflating all patents into it would muddy
   both. Sibling actors with a shared lineage is the established pattern (busshi vs
   rare-earth-coverage).
3. **Fold into the open-patent app** — rejected: open-patent *generates* IP (a different,
   HITL-gated concern); the mirror must be an independent OBSERVATION-only actor (G1).
4. **kotoba-only, no DataLad** — rejected: the full corpus is far larger than the Datom log
   should inline; DataLad/git-annex→IPFS is the established large-dataset substrate
   (ADR-2605241500, as used by genome/jinushi-land), and the user explicitly asked for DataLad.

# References

- `/20-actors/hirameki/` — the actor (methods + ontology + seed + tests + CLAUDE.md)
- `/80-data/hirameki-patents/` — DataLad dataset substrate (corpus + datoms + manifest, CID-verified)
- ADR-2604251024 (superseded), ADR-2606171300 (tokigusuri), ADR-2605262130 (kotoba),
  ADR-2605312345 (Datom-first state), ADR-2605241500 (DataLad/IPFS CID substrate)
- USPTO PatentsView (CC0) · EPO OPS · WIPO PATENTSCOPE
