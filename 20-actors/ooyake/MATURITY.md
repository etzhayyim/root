# ooyake 公 — Maturity Scorecard

Honest R0 status per the gov-coverage maturity model (ADR-2605250680). **This is a
proof-of-model, not coverage.** Coverage is gated by `:sourcing` (G5): only
`:authoritative` rows count. The seed ships **zero** `:authoritative` rows; the
offline `reconcile.py` demo can promote **8 of 28** against the bundled authority
reference (see below) — still a demo, not live ingest.

## Seed contents (R0, 2026-06-02)

Two seed files: `gov-units.seed.edn` (proof-of-model chain) + `gov-units.jp-central.seed.edn` (full JP 府省庁).

| Vocabulary | Count | All `:unverified-seed`? |
|---|---|---|
| `:gov.unit/*` | **28** — base 15 (JP ×7, USA ×3, GBR ×2, DEU ×1, KOR ×1, EU ×1) + JP central 13 (内閣府 + 11省 + デジタル庁 + 復興庁) | yes |
| `:gov.address/*` (住所) | **17** — base 4 + JP central 13 (霞が関 + 市谷 + 紀尾井町) | yes |
| `:gov.window/*` (窓口) | 2 | yes |
| `:gov.form/*` (書式) | 2 (→ chigiri templates) | yes |
| `:gov.procedure/*` (手続き) | 3 (→ toritsugi-ref) | yes |
| `:gov.bpmn/*` (BPMN) | 3 (`:model-only`) | n/a |

**Full vertical chain proven**: `gov.jpn → 財務省 → 国税庁 → 東京国税局 → 麹町税務署`
(with 住所 + 窓口) and `東京都 → 新宿区 → 戸籍住民課窓口` (with 住所). **省庁単位の幅**:
the entire JP central government (内閣府 + 総務/法務/外務/財務/文科/厚労/農水/経産/国交/環境/防衛
省 + デジタル庁 + 復興庁) each with HQ 住所. **国際的な幅**: country + flagship ministry
rows for US/UK/DE/KR + EU supranational.

## Reconcile demo (R1 mechanism, offline)

`scripts/reconcile.py` proves the `:representative → :authoritative` promotion rule
(G5: promote only when `:gov.unit/wikidata` AND `:gov.unit/official-url` agree with
`registry/authority-reference.edn`). Latest run:

```
units in seed: 28 · authority records: 8
→ PROMOTED authoritative: 8  (gov.jpn, gov.jpn.cao, gov.jpn.mof, gov.jpn.mofa,
                              gov.jpn.meti, gov.jpn.pref.13, gov.usa.treasury, gov.gbr.hmrc)
→ conflicts (kept unverified): 0
→ no authority record (stays representative): 20
coverage: 28.6% authoritative (8/28) — rest honestly :representative
```

This is a deterministic OFFLINE demo against a bundled reference; **live fetch of
Wikidata / 行政機関コード / GeoNames is G4 + Council + operator gated** and is NOT run.

The reconcile logic is now a real cell: `cells/reconcile/cell.py` (`ReconcileCell`)
with `mode="bundled"` (runnable, the above) and `mode="live"` (raises, G4-gated).
`scripts/reconcile.py` is the thin CLI over it. Unit tests:
`cells/reconcile/test_reconcile_cell.py` — **5 passed** (promotion set, no-conflict
remainder, bundled-ok, live-gated, unknown-mode-rejected).

## What is NOT done (by design at R0)

| Question | Status |
|---|---|
| All world governments enumerated? | **NO** — 28 units (proof-of-model). The world has ~195 countries × thousands of units each. |
| Any `:authoritative` row in the seed? | **NO** — every seed row is `:representative` / `:unverified-seed`. The `reconcile.py` demo can promote 8/28 against the bundled reference, but that is a demo, not committed seed state or live ingest. |
| Cells running? | **PARTIAL** — `reconcile` (bundled mode) is implemented + unit-tested (5 passed); the other 5 cells are path-reserved scaffolds. `reconcile` live mode + all ingest/serve cells are gated. |
| Per-unit DID served? | **NO** — scheme defined; dynamic did.json serving is R2. |
| `findService` live? | **NO** — lexicon + BPMN defined; serving is R1/R2. |
| `/actors` search surfaces gov units? | **NO** — R1 (after `atlas_serve` + reconcile). |
| Addresses/hours authoritative? | **NO** — best-effort public references as of 2026-06-02, expected to drift. |

## Maturity score (self-assessed, R0)

- **L1 namespace** (country scaffolds): inherited from legacy `gov*` dirs (196 dirs) — but stubs, not ooyake-native yet.
- **L2 agency registry**: 28 ooyake-native units (`:representative`; full JP central government covered).
- **L3 public-services hub** (住所/窓口): 17 addresses + 2 windows (JP only).
- **L4 procedure ingest**: 3 procedures (JP only, → toritsugi).
- **L5 routing-around**: **out of scope** for ooyake (read-side only, G9/G10).

Coverage score remains governed by ADR-2605250680 (49.18/100 baseline). ooyake R0
moves the **schema/substrate** axis to green; the **data/coverage** axis stays red
until R1 authoritative ingest. **No silent truncation**: this file is the
canonical honest record (G5).

## Update 2026-06-02 — JP local-government breadth ingest

`deploy/ingest_jp_local.py` projected the bundled official-code dataset
(`60-apps/ai-gftd-project-states/data/gov/jpn/{prefecture,municipality}.ndjson`;
全国地方公共団体コード / 地方自治法) into `:gov.unit` and ingested it into the live
`gov-atlas-v1` kotoba graph (operator-local):

- **47 prefectures** (都道府県, codes 01–47, with `iso3166-2:JP-NN` + `jp-jichitai:NN`)
- **71 municipalities** — 20 designated cities (政令指定都市) + 23 Tokyo special wards
  (特別区, level `:ward`) + 28 prefectural capitals/major cities, each with its
  6-/5-digit 全国地方公共団体コード as `:gov.unit/external-code`
- 118 units / ~2006 datoms; 200 ok in 2 batches. `gov.jpn.pref.13` (東京都) and
  `gov.jpn.city.13104` (新宿区) merged with the prior hand-seed by id (no duplicate).

Distinct `:gov.unit` in `gov-atlas-v1` after this ingest: **~144** (28 prior + 118
JP-local − 2 overlaps). All JP-local rows ship `:sourcing :representative` /
`:verification-status :unverified-seed` (G5) — they carry official codes + official
`provenance` URLs but are a curated bundle, not an ooyake-reconcile live-verified
fetch; the `reconcile` cell (live mode, G4-gated) promotes them to `:authoritative`.

Honest scope note: ~144 units is still a small fraction of Japan's full local universe
(47 prefectures + 1,718 municipalities + countless bureaus/divisions/窓口) and a rounding
error of the global universe (~195 states × thousands each). This ingest covers the
**highest-tier official backbone** (every prefecture + every designated city + every Tokyo
special ward); the long tail of 765 cities / 716 towns / 156 villages is the next
authoritative-dataset bundle, not fabricated here (G5).

## Update 2026-06-02 (consolidated) — current state of the atlas

Supersedes the R0 "proof-of-model" framing above for the live numbers. The gov-atlas
graph (`gov-atlas-v1`, operator-local kotoba node) + the public index now hold:

| Vocabulary | Count | Note |
|---|---|---|
| `:gov.unit/*` | **772** across **178 jurisdictions** | 177 country + 47 prefecture + 23 ward + 504 municipality + 14 ministry + 4 agency + 1 bureau + 1 division + 1 supranational |
| `:gov.address/*` | 17 (JP) | |
| `:gov.window/*` | 3 (JP) | |
| `:gov.form/*` | 5 (→ chigiri) | |
| `:gov.procedure/*` | 6 (→ toritsugi-ref) | full toritsugi R0 set (6/6) |
| `:gov.bpmn/*` | 3 (`:model-only`) | |

**Sourcing (G5)**: `representative` 654 / **`authoritative` 118**. The 118 = the JP
official-code backbone (47 都道府県 ISO 3166-2:JP + 71 市区町村 全国地方公共団体コード),
promoted under `BOOTSTRAP-ATTESTATION-reconcile-live.md` (Seat 1 Lv7 provisional;
**re-ratify at Council 3-of-5**). 153/177 country units carry a real English name
(from lea NCB records); 24 remain ISO3-code stubs.

**Toolchain (all offline-runnable + tested)**: `ingest_records.py`,
`ingest_jp_local.py`, `ingest_states_global.py`, `promote_authoritative.py`,
`cells/reconcile/cell.py` (bundled mode + 5 tests), `gov_atlas_client.py` (shared read
API + 7 tests), `validate_atlas.py` (integrity, 772/772 parent-refs resolve),
`resolve_for_toritsugi.py` (toritsugi 6/6).

**Integration (read-side SSoT consumed)**: `GovAtlas` client (getUnit / resolvePath /
findService / searchUnits / by_level / by_jurisdiction / resolve_procedure) is the one
API danjo / kanae / tsumugi / toritsugi / himotoki use. toritsugi 6/6 procedures
resolve to 所管 + 窓口 + 住所 + 書式 + 根拠法令.

**Public surface (LIVE)**: `etzhayyim.com/actor/ooyake/did.json` (KV) ·
`/.well-known/gov-units.json` (772 units) · `/gov` (human search) · `/.well-known/actors.json`.

**Maturity axes (self-assessed)**: substrate/schema 95 🟢 · actor liveness 90 🟢 ·
tooling 88 🟢 · public discovery 🟢 · **data breadth ~30 🟡** (178 countries, but
backbone/major-city tier only) · **data authority ~25 🟡** (118/772 authoritative,
provisional/bootstrap).

**Honest pending (gated or env-blocked, NOT done — no silent truncation, G5)**:

- Full JP **1,718-municipality long tail** + per-country full authoritative coverage →
  needs `reconcile` **live mode** (G4 + **Council 3-of-5**; bootstrap attestation covers
  only the already-bundled official-code tiers).
- Country-name enrichment (153 names) **deployed to the public `gov-units.json`** →
  pending a healthy `wrangler` deploy (env tooling exit-194 on 2026-06-02 session).
- `/search` (yoro) surfacing gov units → pending a yoro Pages deploy.
- `kotoba commit` IPFS cold-tier seal → operator cadence (WAL-durable meanwhile).
- Live `:authoritative` promotion is **provisional** until Council re-ratifies.
