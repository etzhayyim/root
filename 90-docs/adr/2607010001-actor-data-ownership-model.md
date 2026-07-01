---
id: adr-2607010001-actor-data-ownership-model
title: "Actor data-ownership model — each actor holds its required real-world data (RAD data-holding vocabulary + domain-hybrid layering)"
status: accepted
doc_type: adr
topic: actor-data-ownership-model
authoritative: true
last_verified: 2026-07-01
# Implementation status: ACCEPTED — all phases landed (21 PRs, #2792–#2833)
#   317 RAD actors / 11 holdings / 10 dataset types / 9 declared / 148 toritsugi children
#   Pipeline: git → datalad → kotoba(CID) → kotobase.net → ipfs → B2
authoritative_for:
  - "70-tools/src/etzhayyim/kotoba_rad.cljc (holding-datoms / publish-identity! :holds / add-holding!)"
  - "70-tools/src/etzhayyim/data_provenance.cljc (validator)"
  - "70-tools/src/etzhayyim/ownership_matrix.cljc (generator)"
  - "70-tools/src/etzhayyim/datalad.cljc (DataLad pipeline bridge)"
  - "70-tools/src/etzhayyim/actor_publish.cljc (manifest->holds / -add-holding CLI)"
  - "RAD data-holding vocabulary (:rad/holds-dataset RID-side datom + dataset:<id> sub-entity)"
  - "00-contracts/lexicons/com/etzhayyim/kotoba/datasetPointer.json (graph-layer binding record)"
  - "90-docs/data-layering-rule.md (normative two-layer rule)"
  - ".github/workflows/data-ownership-provenance.yml (CI gate)"
depends_on:
  - adr-2606162000-jinushi-land-ownership-acquisition-mirror
  - adr-2605241500-etzhayyim-dataset-cid-substrate
  - adr-2606231200-kotoba-rad-sovereign-actor-identity
  - adr-2606241500-sops-age-kotoba-rad-actor-git-evolution
  - adr-2606292000-toritsugi-authority-actor-fanout
  - adr-2605252330-etzhayyim-land-data-substrate-open-only-policy
---

# ADR-2607010001 — Actor data-ownership model

## Context

Owner directive (2026-06-30): move from the *toritsugi* relay / fetch-on-demand
model to one where **each actor HOLDS its own required real-world data**
(companies, financials, transactions, real estate, government open data). Scope
is all actor domains (jinushi / toritsugi / kanjo / all ~312 actors); layering
is **domain-hybrid** (high-frequency/runtime data in the kotoba graph; heavy
reference data in etzhayyim child repos + `root/80-data` backed by B2/DataLad/IPFS).

Three gaps block this today:

1. **RAD declares WHO an actor is, not WHAT it holds.** The 312 identity journals
   (`80-data/kotoba-rad/<actor>.identity.journal.edn`) carry only identity
   attributes (`:rad/did-web`, `:rad/repo`, …). No attribute says "this actor
   holds dataset X". The only data-related precedent is `:rad/age-recipient`
   (ADR-2606241500, for sops secrets).
2. **Bulk data has no binding back to the actor identity.** jinushi/kanjo/
   hirameki-patents/genome already hold real data under `80-data/*/` with a
   mature `*.raw.*` (gitignored, IPFS) → `*.kotoba.edn` (git, CIDv1) +
   `ingest-provenance.json` pipeline, but the holding is not attested in RAD and
   the provenance schema is fragmented per-domain.
3. **The kotoba-graph ↔ etzhayyim-git two-layer relationship is undocumented.**
   The graph layer (ATProto MST) holds only small signed records
   (`app.bsky.feed.post`, `com.etzhayyim.apps.kotoba.cc.*`); bulk data is awkward
   there. There is no normative rule for what goes in which layer.

## Decision

**D1 — RAD data-holding vocabulary (RID-stable, backward-compatible).** Add an
optional holding vocabulary to `etzhayyim.kotoba-rad`, mirroring the accepted
`:rad/age-recipient` precedent and the `add-delegate!` / `sigref:<RID>`
append-only sub-entity pattern:

- RID-side (cardinality-many): `:rad/holds-dataset` (value = dataset-id),
  `:rad/requires-dataset` (needs but does not hold — the honest relay escape-
  hatch), `:rad/depends-on-actor` (runtime delegation).
- holding sub-entity `dataset:<dataset-id>` (same shape as `sigref:<RID>`):
  `:rad/type :dataset-holding`, `:rad/holder`, `:rad/dataset-id`, `:rad/layer`
  (`:graph` | `:repo`), `:rad/source`, `:rad/cidv1`, `:rad/freshness-days`,
  `:rad/retrieved`, `:rad/counts-toward-world-coverage`.

**RID stability is load-bearing.** Holdings ride a **post-genesis tx**
(`holding-datoms` never touches the genesis block); when `:holds` is nil/empty,
zero holding datoms are emitted, so the existing 312 RIDs are bit-identical.
`add-holding!` is the append-only, idempotent (by dataset-id) retrofit path for
the pilot journals — no history rewrite.

**D2 — Ownership matrix: manifest = source, matrix = projection, RAD = attestation.**
The per-actor `manifest.jsonld` gains a `substrate.datasets` block (extending the
already-widespread `substrate.largeAssets` / `governance.dataSources`
conventions). A generator emits `80-data/kotoba-rad/ownership-matrix.edn` by
joining all manifests + all RAD journals. RAD carries the signed attestation.
Three roles mirror the `.md → docs.edn → graph.edn` chain; the matrix is never
hand-edited.

**D3 — Unified provenance & header convention.** Standardize on the jinushi
`ingest-provenance.json` shape across all domains (today fragmented):
`ingest-id` == `:rad/dataset-id` == the `*.kotoba.edn` `:dataset-id` header;
`sources[]` with `sha256`/`cidv1`/`records`/`countries`/`counts-toward-world-
coverage`; `coverage-policy`; `ipfs{status, directory-cid, file-count}`. A
validator (`bb lint:provenance`) re-derives each artifact's CID/sha256 (reusing
jinushi `methods/verify.cljc` logic) and enforces **pin==HEAD** for `:repo`
holdings.

**D4 — Hybrid layering rule (normative; see `90-docs/data-layering-rule.md`).**
- **kotoba graph layer**: dataset **pointers / fingerprints** only — dataset-id,
  layer, cidv1, freshness, last-verified, and at most small signed aggregate
  facts. Carried by a new `com.etzhayyim.kotoba.datasetPointer` lexicon record
  signed by the actor's own did:key (`holderRank` = `canonical` | `mirror`,
  naming ONE canonical owner).
- **etzhayyim repo + DataLad/IPFS layer**: canonical projections (`*.kotoba.edn`,
  git, CIDv1) + raw blobs (`*.raw.*`, gitignored, B2/annex).
- **Rule**: anything > a few KB, any raw blob, any full projection → `:layer
  :repo`; its fingerprint goes in graph. High-frequency / per-query aggregates a
  `/search` XRPC returns → `:layer :graph`. ONE field set, TWO representations
  (signed journal datom = sovereign attestation; signed graph record =
  runtime-discoverable pointer).

**D5 — Staged rollout.** Phase 0 = this ADR + RAD schema + matrix/provenance
schema + layering rule. Phase 1 = normalize jinushi to the standard. Phase 2 =
kanjo (XBRL/EDGAR/TDnet). Phase 3 = toritsugi holder-migration (registry data
alongside wayfinding; **holding ≠ actuation**, G14/G15 gates stay). Phase 4 =
fill empty domains (gyosei etc.). Phase 5 = backfill all 312 actors (generator,
append-only, RID-stable).

## Consequences

- An actor's identity journal now also attests its data holdings, queryable by
  dataset-id across the matrix. Bulk data still lives where it already lives
  (`80-data/*/`, DataLad/IPFS); only a pointer + attestation are added.
- RAD schema is extended but **only with optional attributes** in the clean
  `:rad/` namespace; all 312 existing RIDs are unchanged (verified by unit test:
  `holding-datoms` returns `[]` for nil/empty holds).
- The graph↔git layering is now a normative rule with a binding record type,
  closing the documentation gap.
- Follow-up work (separate PRs): `bb rad:add-holding` (manifest→`add-holding!`
  wiring in `actor_publish.cljc`), `data_provenance.cljc` validator,
  `ownership_matrix.cljc` generator, `bb lint:provenance` / `rad:ownership-matrix`.
- Per-domain rollouts (Phases 1–5) each append RAD holdings via `add-holding!`;
  no history rewrite, no force-push (consistent with ADR-2606231200 + the
  standing-authorization guardrails).

## Alternatives Considered

- **Matrix-as-source (a single `ownership-matrix.edn` authored by hand).**
  Rejected: invents a new SSoT outside each actor, breaks containment, drifts
  the moment any actor evolves. Manifest = source mirrors the repo's settled
  canonical/projection pattern.
- **Holdings inside the genesis block.** Rejected: the genesis CID *is* the RID,
  so any holding change would rotate the RID and break every existing journal.
  Post-genesis tx (like `add-delegate!`) is the established retrofit path.
- **Put bulk datasets in the kotoba graph (PDS MST).** Rejected: the graph layer
  holds small signed records; bulk data there is awkward and unbounded. Pointers
  in graph + blobs in repo/IPFS is the boundary that already works for
  jinushi/kanjo.
- **A per-actor custom field (e.g. each actor invents its own dataset-cid attr,
  as tadori does today).** Rejected as the *general* mechanism: it does not
  cross-actor query. `datasetPointer` generalizes tadori's
  `:tadori.source/dataset-cid` into a shared, queryable record type.

## References

- ADR-2606162000 (jinushi-land ownership acquisition mirror) — the held-data template
- ADR-2605241500 (dataset CID substrate — DataLad + git-annex → IPFS)
- ADR-2606231200 (kotoba-rad sovereign actor identity — RID / sigref / genesis DAG)
- ADR-2606241500 (sops+age — the `:rad/age-recipient` attribute-add precedent)
- ADR-2606292000 (toritsugi authority-actor fanout — 148 per-regime children)
- ADR-2605252330 (land-data substrate open-only policy)
- `70-tools/src/etzhayyim/kotoba_rad.cljc` — `holding-datoms` / `publish-identity!` / `add-holding!`
- `00-contracts/lexicons/com/etzhayyim/kotoba/datasetPointer.json` — graph-layer binding record
- `90-docs/data-layering-rule.md` — normative two-layer rule
- `80-data/jinushi-land/ingest-provenance.json` — canonical provenance template
