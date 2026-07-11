---
id: adr-2607101730-global-legislation-datoms-catalog-layer
title: "ADR-2607101730: global-legislation-datoms ships the R1 catalog layer for ADR-2605262800 (world legal-source registry, not full text)"
status: accepted
doc_type: adr
topic: global-legislation-datoms-catalog-layer
authoritative: true
last_verified: 2026-07-10
priority: 5.5
axis: architecture
weight: 0.35
priority_note: "ADR-2605262800 designed the global legal-corpus ingestion architecture (statutes/cases/treaties/procedures/templates via IPFS-pinned DataLad subdatasets) but shipped only R0 (ADR + sensor scaffold + fetcher path-reserves) — no raw legal text has actually been ingested into any monorepo repo. This ADR records a narrower, immediately-shippable slice: a hand-curated, query-verified catalog of WHERE each jurisdiction's legal sources live, under what license, and which kotodama-py sensor family targets them — built entirely from facts already on record in this monorepo (ADR-2605262800's own prose, kotodama-py's sensors/legal README, hanrei's CLAUDE.md, ooyake's verified legislature registry). It does not ingest, host, or redistribute any statute or case-law full text, and explicitly pins that invariant in its own CI (`:quality/ingested-full-text` hard-fixed at 0)."
authoritative_for:
  - "etzhayyim/global-legislation-datoms repo scope and non-scope (catalog layer, not text corpus)"
  - "the R1 maturity marker for ADR-2605262800's legal-source registry (as distinct from R0 sensor scaffold and the not-yet-shipped W1 raw-bytes ingestion)"
depends_on:
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
related: []
supersedes: []
superseded_by: []
---

# ADR-2607101730: global-legislation-datoms ships the R1 catalog layer for ADR-2605262800

**Status**: accepted
**Date**: 2026-07-10
**Deciders**: Jun Kawasaki

# Context

The owner asked (2026-07-10) whether a repo exists across `etzhayyim`, `cloud-itonami`,
and `kotoba-lang` that can query the world's laws and bills via EDN + Datomic/Datascript.
A survey of the three orgs found no such repo, but three overlapping partial designs:

- **ADR-2605262800** (this repo) designed the global legal-corpus ingestion
  architecture — statutes/cases/treaties/procedures/templates for ~20 jurisdictions
  (US/UK/EU/JP/CA/AU/CoE/UN/DE/FR/IT/KR/IN/BR/CN + more) via IPFS-pinned DataLad
  subdatasets, five `kotodama.organism.sensors.legal.*` sensor families, explicit
  Tier-A/B/C license grading, and a prohibited-vendor list (Westlaw/LexisNexis/Bloomberg
  Law/Wolters Kluwer). Shipped R0 only: the ADR itself plus a sensor scaffold and
  fetcher path-reserves. No raw text was ever ingested.
- **`kotoba-lang/kotodama-py` `organism/sensors/legal/`** carries the Python
  `DatasetSensor` scaffold for that ADR (Statute/Case/Treaty/Procedure/Template
  families, a wave-1 5-anchor table: US Code, CFR, JP e-Gov, EUR-Lex,
  legislation.gov.uk). As of this ADR, only the `README.md` exists on disk — the
  described `base.py` / `us_usc_sensor.py` implementation files are not yet checked in.
- **`etzhayyim/com-etzhayyim-hanrei`** (via `etzhayyim/root`
  `60-apps/etzhayyim-project-hanrei`) is the actor actually collecting case law and
  legislation today — 83 jurisdictions, e-Gov/courts.go.jp/kanpo Collection Jobs. Its
  storage is AT-proto records + Kysely/Hyperdrive/RisingWave SQL, not EDN/Datomic — and
  per this repo's own current substrate rules, RisingWave/Kysely-as-canonical-state is
  now superseded by the kotoba Datom log, so hanrei predates the substrate unification.
- **`etzhayyim/com-etzhayyim-ooyake`** is genuinely "kotoba-Datomic-native" and
  EDN-backed with real, `:maintainer-verified` Wikidata-sourced data (~6,535
  `:gov.unit` rows across ~190 jurisdictions, including one `:legislature` row per
  country's parliament with an official URL and Wikidata QID) — but it catalogs
  government *institutions*, not legal *texts*.

None of the three is a working "-datoms" style projection (schema + Datascript-tx +
Kotoba EAVT + provenance + coverage + read-only consumer contract) for law, the pattern
already proven for world energy statistics in `etzhayyim/global-energy-datoms`
(2026-07-10, same day). That repo projects independently-fetched DataLad raw source
datasets (World Bank WDI, Our World in Data, UN SDG, jp.go.meti.enecho) into a queryable
EDN contract. No equivalent raw legal-text dataset exists yet anywhere in the monorepo
for `global-legislation-datoms` to project the same way — ADR-2605262800's raw-bytes
layer (IPFS-pinned DataLad legal-corpus subdatasets) remains R0/unshipped.

# Decision

Ship **`etzhayyim/global-legislation-datoms`** as the immediately-buildable slice: a
hand-curated **catalog** of legal *sources* (not legal *text*), following the exact
`global-energy-datoms` schema/tx/kotoba-eavt/provenance/coverage/connections/read-only
adapter shape, sourced entirely from already-reviewed monorepo docs rather than freshly
fetched raw files (since no such raw files exist yet for this domain):

- `data/seed/legal-sources.edn` — 29 rows across 16 jurisdictions (12 national + EU +
  COE + UN + ICC), each citing its grounding doc (`ADR-2605262800`,
  `kotodama-py sensors/legal/README.md`, or `hanrei`'s `CLAUDE.md`), its license and
  Tier-A/B/unspecified grading, and — for the 5 wave-1 anchors — its
  `kotodama.organism.sensors.legal.*` sensor id.
- `data/seed/legislatures.edn` — 12 rows mirrored verbatim from ooyake's
  `:maintainer-verified` `gov-units.world-legislatures.edn`, joinable to legal-source
  rows by jurisdiction code, so a query can resolve "which official body legislates for
  jurisdiction X" alongside "what raw sources exist for X."
- `data/seed/prohibited-sources.edn` — the four vendors ADR-2605262800 and
  kotodama-py's README both explicitly prohibit, modeled as queryable rows (not just
  prose) so a future ingestion candidate can be mechanically checked against the list.
- `data/seed/hanrei-coverage.edn` — hanrei's own reported aggregate coverage snapshot
  (75 national + 8 international jurisdictions; civil/common/islamic/mixed counts),
  folded in as a cross-check entity rather than duplicated per-country data hanrei alone
  holds.

`bin/build.cljs` (nbb) compiles these seeds into `data/datascript-tx.edn` and
`data/world-legislation.kotoba.edn` (Kotoba-compatible `[e a v tx :add]` EAVT), matching
`global-energy-datoms`'s output shape exactly. `test/query_contract.clj` exercises the
Datascript compatibility path via the canonical JVM Datascript library (same
NBB-builds/JVM-verifies split as the sibling repo, and for the same reason: NBB is the
scripting/ETL runtime, the canonical Datascript library itself only ships for
JVM/ClojureScript).

**The one invariant this repo must never silently violate**: `data/quality-report.edn`
`:quality/ingested-full-text` is hard-pinned at `0` and asserted by CI. This is what
distinguishes a source *catalog* (this repo) from a text *corpus* (the still-unshipped
raw-bytes layer ADR-2605262800 describes). Landing actual ingested statute/case-law text
is explicitly out of scope for this repo — see `maturity/scorecard.edn`
`:full-text-corpus :status :explicitly-out-of-scope`.

Registered in `com-junkawasaki/root`'s west manifest as
`orgs/etzhayyim/global-legislation-datoms` (`manifest/repos.edn` `:extra-projects`,
minimal `--entry` diff to `manifest/west.yml`, pin verified server-side against the
pushed repo's default branch).

# Consequences

**Positive**:

- Answers the owner's original question honestly: a Datascript/Kotoba-EAVT-queryable
  registry of the world's legal *sources* now exists and is real, verified, on GitHub
  today — but a full-text world law/bill corpus does not yet exist anywhere in the
  monorepo, and this repo's own CI enforces that it never silently starts claiming
  otherwise.
- Gives `kotoba-lang/kotodama-py`'s eventual sensor implementations, `hanrei`'s ongoing
  collection, and `chigiri`'s procedural cells (per ADR-2605262700) a single
  machine-readable jurisdiction × source × license × sensor-readiness registry to read
  instead of re-deriving it from ADR prose each time.
- Establishes the "-datoms" pattern's second instance, proving it generalizes beyond
  statistical time series (`global-energy-datoms`) to qualitative registries.

**Negative**:

- Still no full-text ingestion; a caller expecting to retrieve actual statute or
  judgment text from this repo will find only a pointer (a source URL) and must go to
  the origin, `hanrei`, or (once shipped) ADR-2605262800's raw-bytes layer.
- URLs for sources not literally quoted in an in-repo doc are marked
  `:legal-source/url-provenance :well-known-domain` (a well-known official government
  portal, not independently re-fetched here per the passive-only invariant) rather than
  `:doc-literal` — a future contributor must not conflate the two confidence levels when
  extending the catalog.
- 15 of 29 rows carry `:legal-source/license-tier :tier/unspecified` because
  ADR-2605262800's prose did not grade every named source; closing that gap requires new
  research, not just compilation, and is left as follow-up work.

# Alternatives Considered

**A. Wait for ADR-2605262800 W1 (real raw-bytes ingestion) before shipping anything.**
Rejected: W1 has no committed timeline and requires DataLad+IPFS infrastructure work
orthogonal to this task. A catalog layer is honestly scoped, immediately verifiable, and
does not block or preempt W1 — it is the registry W1's sensors will eventually read.

**B. Extend `etzhayyim/com-etzhayyim-ooyake` in place instead of a new repo.**
Rejected: ooyake's `:gov.unit` schema and G3/G9/G10 posture (civic wayfinding map of
government *institutions*, explicitly read-only and non-target-list) is a different
domain than legal-source cataloging, and conflating "which ministry exists" with "which
statute database exists, under what license" would blur ooyake's own scope discipline.
The two repos join cleanly on jurisdiction code instead (this repo's
`data/seed/legislatures.edn` mirrors the relevant ooyake rows for exactly this purpose).

**C. Model per-country legal-system classification (civil/common/islamic/mixed) for all
16 jurisdictions.**
Rejected for this R1: hanrei's own `CLAUDE.md` only publishes the *aggregate* count
(civil_law 47, common_law 15, islamic_law 1, mixed 12), not a per-jurisdiction table, and
no other in-repo doc supplies one. Fabricating a plausible-looking per-country
classification would violate this repo's own provenance discipline
(`bin/verify-seed-provenance.cljs`); the aggregate is recorded as-is via
`data/seed/hanrei-coverage.edn` instead.

# References

- `etzhayyim/global-legislation-datoms` (this repo's own `README.md` and
  `docs/ci-design.md` explain the scope split from `global-energy-datoms` in detail)
- `etzhayyim/global-energy-datoms` — the sibling "-datoms" repo this one's shape mirrors
- ADR-2605262800 (`public-data-legal-corpus-ipfs-ingestion`) — the parent design this
  ADR ships the catalog-layer slice of
- ADR-2605262700 (`chigiri-legal-procedure-tier-b-actor-r0`) — the primary intended
  consumer of the eventual full corpus, and of this catalog as an interim pointer table
- `kotoba-lang/kotodama-py` `src/kotodama/organism/sensors/legal/README.md` — wave-1
  5-anchor source table this catalog's wave-1 rows are grounded in
- `etzhayyim/root` `60-apps/etzhayyim-project-hanrei/CLAUDE.md` — coverage snapshot and
  explicit e-Gov/kanpo/courts.go.jp URLs this catalog's JP rows are grounded in
- `etzhayyim/com-etzhayyim-ooyake` `registry/gov-units.world-legislatures.edn` — source
  of this catalog's `legislature` join rows
