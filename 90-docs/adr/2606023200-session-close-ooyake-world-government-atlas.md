---
id: adr-2606023200-session-close-ooyake-world-government-atlas
title: "ADR-2606023200: Session close — ooyake (公) world government atlas R0/R1 build + self-paced /loop maturation"
status: active
doc_type: adr
topic: session-close-ooyake-world-government-atlas
authoritative: false
last_verified: 2026-06-02
related:
  - adr-2606021600-ooyake-world-government-atlas
  - adr-2605242330-gov-procedure-pregel-mcp-coverage
  - adr-2605312030-toritsugi-government-procedure-concierge-tier-b-actor-r0
  - adr-2605192300-etzhayyim-bootstrap-council-five
supersedes: []
superseded_by: []
---

# ADR-2606023200: Session close — ooyake (公) world government atlas

**Status**: active
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

# Context

Session opened on the founder's question: *「全世界の政府、自治体、省庁単位までの actor
の設計…profile, xrpc…住所、窓口、書式、手続き、bpmn…すべて設計・公開されているか?」* The honest
answer was **no** — the six government-facing actors (danjo/kanae/toritsugi/moushibumi/
himotoki/tsumugi) observe or serve governments but none catalogs them; the legacy
`gov*` BPMN/OpenAPI were stubs. This session designed and built **ooyake 公** to fill
that gap, then matured it across a self-paced `/loop` (9 iterations).

# Decision (what shipped)

**ooyake 公** — a Tier-B, kotoba-Datomic-native, READ-SIDE structural atlas of world
government units (per ADR-2606021600). Posture: **observational mirror + civic
wayfinding map** — never the government, never an official channel, never a target-list
(G3/G10).

## Landed on `main`

- **Actor + substrate**: ADR-2606021600 + `gov-atlas-ontology.kotoba.edn`
  (`:gov.unit/address/window/form/procedure/bpmn`) + manifest + 8 read-only lexicons +
  3 BPMN. Registered in INFRA_ACTORS + actor-profile-seed + yoro seed-datoms.
- **Live (production etzhayyim.com)**: `/actor/ooyake/did.json` (KV-served DID +
  AtprotoPDS/XRPC services) · `/.well-known/gov-units.json` (machine index) · `/gov`
  (human civic-wayfinding search) · in `/.well-known/actors.json`.
- **Data (kotoba `gov-atlas-v1`, operator-local)**: **772 units / 178 jurisdictions** —
  full JP central gov (内閣府+11省+デジタル庁+復興庁), all 47 都道府県 + 20 政令市 + 23 特別区,
  real-named major cities across 176 countries, + ISO3 country units (153/177 real-named
  from lea NCB records). **6 procedures (toritsugi 6/6)** / 5 forms / 3 windows.
- **Authority**: 118 units (`:authoritative`) — the JP official-code backbone
  (全国地方公共団体コード / ISO 3166-2:JP) promoted under the **bootstrap attestation**
  (`BOOTSTRAP-ATTESTATION-reconcile-live.md`, Seat 1 Lv7 provisional; re-ratify at
  Council 3-of-5). The other 654 stay `:representative` (G5).
- **Toolchain (offline, tested — `deploy/run_tests.sh` 8/8 green)**: `ingest_records`,
  `ingest_jp_local`, `ingest_states_global`, `promote_authoritative`, `reconcile` cell
  (bundled + 5 tests), `gov_atlas_client` (shared read API + 7 tests), `validate_atlas`
  (772/772 parent-refs resolve), `resolve_for_toritsugi`, `consumers_example`.
- **Integration**: the `GovAtlas` client is the one read API for all 5 consumers
  (danjo/kanae/tsumugi/toritsugi/himotoki) — demonstrated with running, tested code.

PRs: #746/#760/#770 + gen/read-client merged; #779 (country-name enrichment, ingest
side), #784 (MATURITY refresh), #789 (consumer examples), #792 (toolchain README +
test runner) open at close.

# Consequences / honest pending (G5 — no silent truncation)

What is **gated or environment-blocked**, NOT done:

- **Full JP 1,718-municipality long tail + per-country full authoritative** → requires
  `reconcile` **live mode** (external public-registry fetch), which is **G4 + Council
  Lv6+ 3-of-5 gated**. The org currently has a single participant (Seat 1), so a 3-of-5
  multisig is physically unconstructable; the bootstrap attestation covers only the
  already-bundled official-code tiers. No fabrication, no Council overreach.
- **Country-name enrichment (153 names) + any public index refresh deployed live** →
  blocked this session by `wrangler` (exit-194); pending a healthy deploy.
- **kotoba bulk re-ingest** → batch `kg.ingest_batch` was flaky (401; single writes ok).
- **`/search` (yoro)** surfacing gov units → pending a yoro Pages deploy (454 uncommitted
  files made a full deploy out of scope).
- **`kotoba commit`** IPFS cold-tier seal → operator cadence (WAL-durable meanwhile).

# Resumption triggers

Re-open the `/loop` (or direct task) when: (a) `wrangler` deploy recovers → push the
country-name enrichment + refresh the public index, re-ingest kotoba; (b) the Bootstrap
Council reaches 3-of-5 → ratify `COUNCIL-PROPOSAL-reconcile-live.md` → reconcile-live →
full authoritative ingest; (c) a fuller authoritative dataset (e.g. complete
全国地方公共団体コード) is bundled.

# References

- ADR-2606021600 (ooyake design) · `20-actors/ooyake/{MATURITY,COUNCIL-PROPOSAL-reconcile-live,BOOTSTRAP-ATTESTATION-reconcile-live}.md`
- `20-actors/ooyake/deploy/README.md` (toolchain) · `deploy/run_tests.sh`
- ADR-2605242330 (scope amended) · ADR-2605312030 (toritsugi) · ADR-2605192300 (Bootstrap Council)
