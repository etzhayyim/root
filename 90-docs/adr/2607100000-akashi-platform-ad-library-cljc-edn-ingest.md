---
id: adr-2607100000-akashi-platform-ad-library-cljc-edn-ingest
title: "ADR-2607100000: akashi platform ad-library ingest is CLJC/.kotoba-only and stores EDN for git, DataLad, kotoba-rad, GitHub, Radicle, Datomic, and DataScript"
status: accepted
doc_type: adr
topic: akashi-platform-ad-library-cljc-edn-ingest
authoritative: true
last_verified: 2026-07-10
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Locks akashi Meta/Instagram/X reviewed-export ingest to .cljc/.kotoba only; Python is not an allowed adapter implementation surface."
authoritative_for:
  - akashi reviewed local Meta/Instagram/X ad-library export ingest
  - akashi EDN tx-data projection for DataScript/kotoba and Datomic import
  - akashi storage handoff through git, DataLad/git-annex, kotoba-rad, GitHub, and Radicle
depends_on:
  - adr-2606022300-akashi-public-ad-disclosure-kotoba-actor-r0
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2607010001-actor-data-ownership-model
related:
  - adr-2607090900-kotoba-lang-bpmn-canonical-engine-omg-202
supersedes: []
superseded_by: []
---

# ADR-2607100000: akashi platform ad-library ingest is CLJC/.kotoba-only

**Status**: accepted
**Date**: 2026-07-10
**Deciders**: Jun Kawasaki

## Context

akashi needs to ingest operator-reviewed public ad-library export snapshots from
Meta/Facebook/Instagram and X/Twitter into source-cited transparency records.
The actor must preserve the R0 boundary: no live scraping, no login flow, no ad
SDK, no targeting-list reconstruction, and no adjudication.

The storage/query question is also part of the boundary. The reviewed snapshots
must become deterministic EDN so they can be saved in git, DataLad/git-annex,
kotoba-rad, GitHub, and Radicle, then queried either directly as
DataScript/kotoba tx-data or via a Datomic schema/scalar transaction bundle.

## Decision

akashi platform ad-library ingest is implemented only as `.cljc` and `.kotoba`
artifacts. Python is not an allowed akashi adapter implementation surface.

The live design is:

- `adapters/platform_ad_library_fixture_parser.cljc` parses reviewed local
  Meta/Instagram/X-style snapshots into akashi lexicon-shaped records.
- `adapters/ingest_platform_ad_library.cljc` is the operator-facing local-file
  ingest boundary. It has no network mode.
- `adapters/edn_export.cljc` emits deterministic DataScript/kotoba tx EDN and a
  Datomic import bundle with schema plus scalar `:db/add` tx ops.
- `adapters/persist_fixture_edn.cljc` materializes EDN artifacts and a storage
  manifest for git, DataLad/git-annex, and kotoba-rad handoff.
- `adapters/edn_query.cljc` queries the fixture tx-data without requiring a
  live Datomic/DataScript database.
- `adapters/public_page_scribe.cljc` is the production path. It supports public
  pages and operator-saved public files, preserves raw scribe EDN, and has no
  platform-token, login, or UI-automation mode.

## Operational persistence status, 2026-07-10

The fixture EDN artifacts are actually saved in the repository and have been
pushed to both GitHub and Radicle:

- GitHub remote: `https://github.com/etzhayyim/root`
- Git commit: `e48f35c55107982cfb4d6dc7675f7b79841443c9`
- Radicle RID: `rad:z2kYxHLH4E6pJHksgzAkRm9ztFgjC`
- Radicle alias/DID: `com-junkawasaki` /
  `did:key:z6Mkud1DguEntg5EBhsfiHNJJBs8Qiw39x5iRgSCfH3cAuin`
- Radicle seed status observed: `root` policy `allow/all`, in sync with
  `rosa.radicle.network`

The saved akashi dataset is the reviewed fixture dataset, not a production
public-page capture:

- `20-actors/akashi/data/akashi-platform-ad-library.fixture.tx.kotoba.edn`
- `20-actors/akashi/data/akashi-platform-ad-library.fixture.datomic.edn`
- `20-actors/akashi/data/akashi-platform-ad-library.storage-manifest.edn`
- CIDv1 for the kotoba tx EDN:
  `bafkreihcflz5xuinkb7ixurqccmlwl3gknc74uwthamg6vbwzhbsnmtqb4`
- kotoba-rad holding:
  `80-data/kotoba-rad/akashi.identity.journal.edn`

## Consequences

The actor can answer: "is this designed?" with yes, within the fixture/reviewed
local export boundary. It is not a live platform collector. The current ingest
path stores EDN artifacts under `20-actors/akashi/data/`, records their CIDv1
metadata in the storage manifest, and keeps query code CLJC-native.

Any future live source adapter requires a separate source-policy approval,
R1/R2 activation gate, and continued `.cljc`/`.kotoba` implementation.

As of 2026-07-10, the Meta/X source-policy approval is for public-page/file
scribe only. No production public-page fetch has been materialized in this
workspace yet.

GitHub/Radicle persistence does not change that collection status: it proves the
fixture EDN and manifests are durably published, not that live Meta/X/Instagram
public pages have already been collected.
