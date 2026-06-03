# ooyake 公 — Maturity Scorecard

Honest R0 status per the gov-coverage maturity model (ADR-2605250680). **This is a
proof-of-model, not coverage.** Coverage is gated by `:sourcing` (G5): only
`:authoritative` rows count. The seed ships **zero** `:authoritative` rows; the
offline `reconcile.py` demo can promote **36 of 38** against the bundled authority
reference (see below) — still a demo, not live ingest. (Was 8/28 before the
2026-06-03 QID-integrity fix; see § "2026-06-03 QID integrity fix".) A registry
integrity guard (`scripts/check_seed_integrity.py`) now fails on the structural
tells of that fabrication class — see § "2026-06-03 integrity guard + breadth".

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
units in seed: 28 · authority records: 26
→ PROMOTED authoritative: 26  (all of JP central [内閣府+11省+デジタル庁+復興庁]
                               + 国税庁 + 東京都 + 新宿区 + US [Treasury/IRS] +
                               UK/HMRC + DE + KR + EU)
→ conflicts (kept unverified): 0
→ no authority record (stays representative): 2  (NTA Tokyo regional + 麹町税務署,
                               no Wikidata QID → cannot confirm, stays representative)
coverage: 92.9% authoritative (26/28) — rest honestly :representative
```

This is a deterministic OFFLINE demo against a bundled reference; **live fetch of
Wikidata / 行政機関コード / GeoNames is G4 + Council + operator gated** and is NOT run.

The reconcile logic is now a real cell: `cells/reconcile/cell.py` (`ReconcileCell`)
with `mode="bundled"` (runnable, the above) and `mode="live"` (raises, G4-gated).
`scripts/reconcile.py` is the thin CLI over it. Unit tests:
`cells/reconcile/test_reconcile_cell.py` — **5 passed** (promotion set, no-conflict
remainder, bundled-ok, live-gated, unknown-mode-rejected).

## Update 2026-06-03 — QID integrity fix (correctness, not just coverage)

While expanding the bundled authority reference, **every hand-entered Wikidata QID
for a sub-national / agency unit was found to be fabricated** — a contiguous fake
block (`Q1023718…Q1023920`) had been assigned to the JP cabinet office + ministries,
plus wrong QIDs for NTA, IRS, US Treasury, UK HMRC, Shinjuku, Digital Agency, and
the Reconstruction Agency. The most glaring: **MOF's "Q1023766" actually resolves to
*CIUTI*, a Brussels translators' association** — so the prior `reconcile` demo had
"verified" the Ministry of Finance against an unrelated NGO (circular agreement
between two copies of the same fake number).

Only the genuinely canonical QIDs were correct: country-level `Q17`/`Q30`/`Q145`/
`Q183`/`Q884`/`Q458` and Tokyo `Q1490`.

**Fix** (all QIDs independently re-verified against wikidata.org on 2026-06-03):

| unit | fabricated | corrected | resolves to |
|---|---|---|---|
| gov.jpn.cao 内閣府 | Q1023920 | **Q6005** | Cabinet Office |
| gov.jpn.mof 財務省 | Q1023766 (=CIUTI!) | **Q1322605** | Ministry of Finance |
| gov.jpn.mof.nta 国税庁 | Q2425817 | **Q11421205** | National Tax Agency |
| gov.jpn.mofa 外務省 | Q1023718 | **Q222241** | MOFA |
| gov.jpn.meti 経産省 | Q1023775 | **Q1197264** | METI |
| gov.jpn.mic 総務省 | Q1023776 | **Q1322293** | MIC |
| gov.jpn.moj 法務省 | Q1023732 | **Q1031145** | Ministry of Justice |
| gov.jpn.mext 文科省 | Q1023766 (dup) | **Q1054379** | MEXT |
| gov.jpn.mhlw 厚労省 | Q1023759 | **Q1191238** | MHLW |
| gov.jpn.maff 農水省 | Q1023745 | **Q1376786** | MAFF |
| gov.jpn.mlit 国交省 | Q1023784 | **Q1376196** | MLIT |
| gov.jpn.moe 環境省 | Q1023795 | **Q1125558** | Ministry of the Environment |
| gov.jpn.mod 防衛省 | Q1023804 | **Q1062689** | Ministry of Defense |
| gov.jpn.digital デジタル庁 | Q108458515 | **Q107291492** | Digital Agency |
| gov.jpn.reconstruction 復興庁 | Q11405853 | **Q1056221** | Reconstruction Agency |
| gov.jpn.city.13104 新宿区 | Q170461 | **Q179645** | Shinjuku |
| gov.usa.treasury | Q633534 | **Q648666** | US Dept. of the Treasury |
| gov.usa.treasury.irs | Q254375 | **Q973587** | Internal Revenue Service |
| gov.gbr.hmrc | Q1377862 | **Q166559** | HM Revenue & Customs |

Corrected in BOTH seeds (`gov-units.seed.edn`, `gov-units.jp-central.seed.edn`)
**and** `authority-reference.edn`. The authority reference grew **8 → 26 records**;
because the QIDs are now real (not circular fakes), the bundled reconcile honestly
promotes **26/28 (92.9%)** with **0 conflicts** (the 2 remainder have no QID).
Tests updated; **5 passed**.

**Sourcing policy change (founder directive 2026-06-03):** `authority-reference.edn`
`:provenance` now cites **each body's own official URL / document URL** (本体の url /
文書の url) as the primary source — e.g. `https://www.mof.go.jp/english/`,
`https://www.cao.go.jp/en/about.html`. The Wikidata entity page is recorded only in
a secondary `:wikidata-ref` field for QID traceability, never as the primary source.

> NOTE: rows remain `:representative` / `:unverified-seed` in the committed seeds.
> The reconcile demo *can* promote them, but committing `:authoritative` state is a
> separate operator-gated step (G5); the seeds are not silently upgraded. The
> fabrication finding also means: **do not trust any remaining un-reverified QID** in
> the JP-local 144-unit ingest (below) — those `iso3166-2`/`jp-jichitai` official
> codes are real, but their Wikidata cross-refs, where present, need the same pass.
> (Checked 2026-06-03: `deploy/ingest_jp_local.py` sets **no** Wikidata QID at all —
> it carries only official admin codes + official URLs — so the JP-local ingest is
> clean of this bug by construction.)

## Update 2026-06-03 — integrity guard + verified country breadth

**(A) Integrity guard (durable — prevents recurrence).**
`scripts/check_seed_integrity.py` is a read-only (G9) checker, run over both seeds +
`authority-reference.edn`, that hard-fails on the structural tells of the
fabrication class above:
  1. duplicate `:gov.unit/wikidata` across distinct units (the MOF/MEXT tell);
  2. malformed QID (must match `^Q[1-9][0-9]*$`);
  3. G5: every unit carries `:sourcing` + `:provenance` + `:last-verified`;
  4. authority-reference `:wikidata`/`:official-url` must AGREE with the seed unit
     (a mismatch = circular/stale "verification");
  5. authority record pointing at a non-existent unit (dangling).
Tests `cells/reconcile/test_seed_integrity.py` prove it both passes on the committed
registry AND actually fires on synthetic duplicate/malformed/missing/mismatch
inputs. Suite now **9 passed** (5 reconcile + 4 integrity).

**(B) Verified country breadth.**
Added 4 units — **France** (country `Q142` + `Ministère de l'Économie et des
Finances` `Q1416512`) and **Canada** (country `Q16` + `Department of Finance Canada`
`Q1191438`) — every QID web-verified against wikidata.org on 2026-06-03, every
`:provenance` citing the body's own official URL (`gouvernement.fr`,
`economie.gouv.fr`, `canada.ca`, `canada.ca/en/department-finance.html`).

National "executive" coverage spans JP (full central gov) + US + UK + DE + KR + EU
+ FR + CA, each with a verified finance-ministry child where added.

### 2026-06-03 (cont.) — G7 completion + India/Australia

Added 6 more units, all QIDs web-verified against wikidata.org + `:provenance` =
body's own official URL:
- **Italy** (country `Q38` + `Ministero dell'Economia e delle Finanze` `Q1116000`)
  — completes the **G7** national set (US/UK/FR/DE/JP/IT/CA all present);
- **Australia** (country `Q408` + `The Treasury` `Q3277092`);
- **India** (country `Q668` + `Ministry of Finance` `Q2641068`).

Registry now: **38 units / 36 authority records**; bundled reconcile promotes
**36/38 (94.7%)**, **0 conflicts** (the 2 remainder = NTA Tokyo regional + 麹町税務署,
no QID). The integrity guard + 9-test suite stay green. Every national row carries a
verified finance-ministry/treasury child. Still `:representative` in committed state
(promotion is operator-gated, G5).

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
