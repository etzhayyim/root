---
id: adr-2606271700-nyusatsu-worldwide-procurement-social-actor
title: "ADR-2606271700: nyusatsu 入札 — JP→worldwide public-procurement mirror, OCDS-normalized, jurisdiction-attributed, social-derived"
status: accepted
doc_type: adr
topic: nyusatsu-worldwide-procurement-mirror
authoritative: true
last_verified: 2026-06-27
priority: 6.0
axis: architecture
weight: 0.6
priority_note: "Closes the world-coverage gap for public procurement (currently JP-only) on the canonical kotoba substrate; OBSERVATION/mirror-only, charter-clean, OCDS-aligned."
authoritative_for:
  - nyusatsu-worldwide-procurement-mirror
  - govFiscal-procurementBid-lexicon
depends_on:
  - "2605262130  # kotoba storage substrate (no RisingWave)"
  - "2605312345  # kotoba Datom log = first-class canonical state"
  - "2606230001  # actor → kotoba-mesh pipeline"
  - "2606072000  # kosatsu competing-claim mirror (attributed, primary-source, non-adjudicating pattern reused)"
related:
  - "2606212200  # hirameki worldwide patent KG-mirror (sibling worldwide OBSERVATION actor; same charter posture)"
  - "2605301600  # danjo public-accountability oversight (JP gov-corpus ingest incl. 政府調達)"
  - "0035        # jp-tax-money-flow reverse-topology (original nyusatsu / NJSS-replacement rationale)"
supersedes: []
superseded_by: []
---

# ADR-2606271700: nyusatsu 入札 — JP→worldwide public-procurement mirror

**Status**: accepted (founder Lv7+ attested 2026-06-27; G8 unlocked, §8.1)
**Date**: 2026-06-27
**Deciders**: Jun Kawasaki

# Context

`20-actors/nyusatsu` today is a **Japan-only** public-procurement aggregator — a
self-hosted NJSS replacement crawling GEPS + 全省庁 + 47 都道府県 + 1,718 市町村 +
独法/特殊法人 入札公告/開札結果, extracting `com.etzhayyim.apps.jpFiscal.procurementBid`,
and `derive`-ing an `app.bsky.feed.post` per bid (manifest-only; `actor-manifest.jsonld`;
no clj yet; `MIGRATION-TODO` = TRANSFORM/codemod pending).

The user requirement is **全世界の政府の調達情報** — worldwide government procurement —
ingested, normalized in EDN/clj, and social-posted to etzhayyim. Three gaps:

1. **Scope** — JP-only sources; no supranational (EU/UN/World Bank) or other-nation feeds.
2. **Schema** — `jpFiscal.procurementBid` hard-codes JPY and a JP issuer-DID shape; not
   jurisdiction-neutral; no global dedup key.
3. **Substrate/posture** — jsonld manifest (being retired; cf. kosatsu's
   `manifest.jsonld → manifest.edn` conversion) and no charter-grade gating for what is
   inherently a cross-jurisdiction political-economic mirror.

Two existing actors already solve the hard parts of "worldwide, attributed, charter-clean
OBSERVATION mirror" and are reused rather than reinvented:

- **kosatsu 高札** (ADR-2606072000) — multi-jurisdiction (OFAC/EU/UN/UK/JP/Interpol)
  **attributed, primary-source-only, non-adjudicating** mirror with member-signed dry-run
  social posts and a 10-gate charter. nyusatsu adopts the same gate spine.
- **hirameki 閃き** (ADR-2606212200) — the precedent for a **worldwide OBSERVATION
  KG-mirror** on kotoba + DataLad. nyusatsu is its procurement sibling.

The decisive external standard is **OCDS — the Open Contracting Data Standard**
(standard.open-contracting.org). 50+ governments already publish OCDS JSON (UK FTS,
Ukraine ProZorro, Mexico, Canada, Australia AusTender, EU eForms→OCDS). OCDS gives a
ready-made global normalization target keyed by **`ocid`** (Open Contracting ID), which
becomes our cross-jurisdiction dedup key.

# Decision

Generalize nyusatsu **in place** from "JP procurement aggregator" to a **worldwide
public-procurement mirror**, OCDS-normalized, jurisdiction-attributed, kotoba-native, with
gated multilingual social derivation. nyusatsu's existing JP source set becomes the **JP
jurisdiction adapter** — one tier among many, not the whole actor.

## 1. Identity & substrate

- DID: `did:web:etzhayyim.com:actor:nyusatsu` (subdid convention, per ADR-2606232100;
  the legacy `did:web:nyusatsu.etzhayyim.com` is retired with the jsonld manifest).
- Canonical state: **kotoba Datom log** (append-only EAVT; no RisingWave/SQL — ADR-2605262130/2605312345).
- Manifest: **`manifest.edn`** (EDN; jsonld retired). Existing `actor-manifest.jsonld`
  kept only as a frozen legacy artifact until the JP pipeline is ported.
- Runtime: KOTOBA Mesh cells (`kotoba.app.edn`), Murakumo LLM for extraction/narration only.

## 2. Lexicon: `jpFiscal.procurementBid` → `govFiscal.procurementBid`

A new jurisdiction-neutral, OCDS-aligned lexicon
`com.etzhayyim.apps.govFiscal.procurementBid` supersedes the JP-specific one. Key fields:

| field | source | note |
|---|---|---|
| `ocid` | OCDS `ocid` (or `<jurisdiction>-<sourceId>-<tenderId>` synthesized) | **global dedup key** |
| `jurisdiction` | ISO 3166-1 alpha-2 (+ optional subdivision e.g. `JP-13`) | replaces JP-implicit |
| `issuerDid` | `did:web:gov.etzhayyim.com:country:<iso3>:<agency>` | owner DID (G-ownership) |
| `tenderId` | source-local notice no. | was `tenderNo` |
| `title` / `description` | source | `sourceLang` carried alongside |
| `method` | OCDS `tender.procurementMethod` {open\|selective\|limited\|direct} | normalized enum |
| `status` | OCDS `tender.status` {planning\|active\|complete\|cancelled\|unsuccessful} | event-log/as-of |
| `category` | OCDS `mainProcurementCategory` {goods\|works\|services} | |
| `classification` | CPV / UNSPSC code | cross-walk via `unspsc-compat` |
| `value` | `{amount, currency}` ISO 4217 | replaces JPY-only `estimatedJpy` |
| `tenderPeriod` | `{startDate, endDate}` ISO 8601 (UTC) | replaces `openedAt/closedAt` |
| `award` | on award: `{supplierName, supplierDid?, value, date}` | links to `contract` lexicon |
| `provenance` | `{sourceUrl, citations[≥1], sourcing :representative\|:authoritative, fetchedAt, robotsOk}` | G3 |

`jpFiscal.procurementBid` records are migrated to `govFiscal` with `jurisdiction "JP"` and
`value.currency "JPY"` by a one-shot codemod; the JP `contract` lexicon is unchanged.

## 3. Worldwide source registry — `registry/sources.edn`

Sources are tiered and prefer **OCDS/structured APIs over HTML scraping**. Tiers:

- `:supranational` — EU TED, UN UNGM, World Bank, WTO GPA (cf. `wto-compat`, `worldbank-compat`).
- `:national` — per-country portals (US SAM.gov, UK FTS, JP GEPS, KR KONEPS, AU AusTender,
  CA CanadaBuys, IN CPPP/GeM, BR PNCP, MX ComprasMX, UA ProZorro, SG GeBIZ, …).
- `:subnational` — states/prefectures/municipalities (JP 47 都道府県 etc., US states, …).
- `:standard-feed` — OCDS data registry (standard.open-contracting.org/data) for **discovery**
  of new publishers (drives the shinka loop).

Each entry: `:id :tier :jurisdiction :kind {:ocds-api|:rest-api|:csv|:rss|:html} :entry
:rate-ms (≥1500 default) :auth (none|api-key) :robots :note`. The full JP set from the
legacy jsonld is imported verbatim as the JP `:national`/`:subnational` rows.

## 4. Ingest pipeline (cells)

Two ingest fast-paths, one normalizer, one mirror, one social — Pregel cells (kosatsu shape;
`.solve()` raises until Council ratifies live operation, G8):

| cell | node | phase | I/O |
|---|---|---|---|
| `nyusatsu_ocds_ingest` | reuben | continuous | OCDS/REST source → releases → normalized `procurementBid` datoms (no LLM; structured) |
| `nyusatsu_html_extract` | reuben | continuous | HTML/PDF source → Murakumo structured-extract → `procurementBid` datoms (fallback) |
| `nyusatsu_normalize_dedup` | gad | continuous | MERGE by `ocid`; currency/date/method normalization; CPV↔UNSPSC cross-walk; award→contract link |
| `nyusatsu_resolve_award` | gad | event (xrpc `…nyusatsu.resolveAward`) | award datom → edge to `contract`/issuer DID |
| `nyusatsu_social_post` | naphtali | periodic (event) | a bid/award → **dry-run** member-signed multilingual `networkPost`; live = Council Lv6+ + operator gated |

Robots/rate-limit honored per source; OCDS APIs preferred so most jurisdictions never touch
the LLM path. clj method modules (kosatsu convention): `methods/ingest.clj`
(`--live` REFUSED at R0), `methods/normalize.clj`, `methods/social.clj`, `methods/edn.clj`.

## 5. Social derivation (gated, multilingual)

The legacy single JP-template `derive` is replaced by a `networkPost` projection (kosatsu
`social.clj` pattern):

- **Dry-run only at R0** (`:post/status :dry-run`) — never published until Council Lv6+ +
  operator + member signature (G8). `:post/server-held-key false` (member signs, not server).
- **Multilingual**: summary rendered in `sourceLang` **and** English; currency shown native +
  optional reference. Template e.g. `入札公告/Tender: {{issuer}} · {{method}} · {{value}} ·
  closes {{tenderPeriod.endDate}} — {{sourceUrl}}`.
- **Non-adjudicating / mirror** (G2/G9): a post reports *that an authority published a notice*,
  attributed; never ranks bidders, predicts winners, or advises.
- Routed to the etzhayyim ATProto feed (`app.bsky.feed.post` embed = external `sourceUrl`),
  `langs` = `[sourceLang "en"]`.

## 6. Charter gates (adopt kosatsu spine, procurement-specialized)

- **G1 mirror-not-author** — etzhayyim authors no tender; issuer is always an attributed gov DID.
- **G2 non-adjudicating** — no winner-prediction, no bidder ranking/score, no corruption verdict.
- **G3 primary-source-only** — ≥1 (≥2 for award) of the issuer's OWN publications; paid
  aggregators (NJSS / 官公需ウォッチャー / commercial tender terminals) prohibited as citations.
- **G4 event-log / as-of** — `status` transitions are NEW datoms; nothing overwritten.
- **G5 PII** — bidder sole-proprietor addresses etc. = PII Tier-3; redaction hook mandatory
  (ADR-0018); off-graph encrypted.
- **G6 robots/legality** — per-source robots.txt + rate-limit; rely on each jurisdiction's
  publication-mandate (e.g. JP 会計法29条/地方自治法234条/情報公開法; EU TED mandate; etc.).
- **G7 no-server-key (non-custodial — NOT anti-automation)** — nyusatsu holds NO
  platform-custodial unilateral signing key in a hosted Worker/pod/CronJob/CI. It MAY act
  autonomously: (a) **read-only public ingest is exempt** — the actor fetches OCDS/REST
  sources itself, no key, no operator (ADR-2606072802 clarification); (b) **autonomous
  writes/posts are permitted** when signed by the actor's OWN self-generated `did:key` (seed
  sealed off-platform in Keychain/1Password, present-only) and attributed to a consenting
  member via a CACAO leash (ADR-2605231525 + ADR-2606111400; the deployed kaname/ibuki/
  tsubasa pattern). No per-tender/per-bidder score. **`no-server-key` ≠ "do not automate/
  post/push"** — it forbids only a custodial central key.
- **G8 outward-gated (the DISTINCT governance lever)** — what holds live PUBLICATION back is
  Council Lv6+ attestation (= PR-review in Bootstrap) + member signature, NOT G7. Until G8 is
  unlocked, social posts are `:dry-run` and award→contract / external writes are withheld.
  **Do not conflate G7 with G8**: a read-only public ingest needs neither a key (G7-exempt)
  nor a Council gate (G8 gates outbound publication, not inbound observation) — so the ingest
  cell runs autonomously *before* G8; only posting/writing waits on G8.
- **G9 map-not-target** — outputs serve transparency/SME-access/market visibility; never a
  "who-to-influence/lobby/collude" target-list.
- **G10 sourcing-honesty** — `:representative` (synthetic seed) vs `:authoritative` declared per datom.

### 6.1 Two distinct levers (do not conflate)

`no-server-key` (G7) and `outward-gated` (G8) are orthogonal charter levers; an earlier draft
conflated them. To be explicit:

| | **G7 no-server-key** | **G8 outward-gated** |
|---|---|---|
| Concern | *who holds the signing key* (non-custody / anti-centralization) | *when outbound publication is allowed* (governance) |
| Forbids | a platform-custodial unilateral key in a hosted Worker/pod/CI | live posting / external writes before Council attestation |
| Read-only ingest | **exempt** — autonomous fetch, no key | **not gated** — ingest is inbound, not outbound |
| Autonomous write/post | **allowed** via actor self-`did:key` (sealed off-platform) + member CACAO leash | allowed once G8 is unlocked (member-signed) |
| Lifts at | never (it is a standing non-custody invariant) | R3, by Council Lv6+ = PR-review attestation |

Consequence for residence: nyusatsu can **run resident and ingest the world's procurement
autonomously at R2** (G7-clean, G8-irrelevant for inbound); only the *outbound* social post /
contract write waits for the G8 unlock. There is no charter bar on a resident actor that
posts or pushes — only on a *custodial central key* doing so unilaterally.

## 7. Shinka (self-evolution) loop

Unchanged in spirit, widened in scope: the OCDS data registry + per-jurisdiction crawl
surface new publishers; each discovery emits `shinkaEvolution`/`shinkaKnowledge` and updates
a **world coverage snapshot** (jurisdictions covered / OCDS-native vs HTML / freshness).

## 8. Status & rollout

- **R0 (this ADR)**: `manifest.edn` + `registry/sources.edn` + `govFiscal.procurementBid`
  lexicon spec + clj method scaffolds raising R0; JP rows imported; seed = `:representative`.
- **R1** (landed): clj `edn`/`normalize`/`ingest`/`social` green OFFLINE over OCDS-native
  jurisdictions + JP; dry-run posts; 24 tests / 67 assertions green.
- **R2 — RESIDENCE + autonomous read-only ingest** (kaname/ibuki/tsubasa pattern):
  `autorun.cljc` heartbeat + `cell.cljc` registered in `50-infra/.../cell-runner/cells.edn`
  (cron) + launchd `LaunchAgent` (OS residence, not a `nohup &`) + `kotoba_bridge.cljc`
  (commit-DAG → live kotoba Datom log; actor self `did:key` sealed off-platform + member CACAO
  leash; exactly-once cursor; fail-open). **Read-only OCDS ingest runs AUTONOMOUSLY here —
  G7-exempt, NOT G8-gated** (the actor fetches public sources itself, no operator). Bids
  persist `:representative`→`:authoritative`; coverage snapshot live. Social posts stay
  `:dry-run`/`:prepared`.
- **R3 — OUTBOUND unlock (G8 = Council Lv6+ PR-review attestation)**: live social posting on
  member signature + award→contract writes; the HTML/PDF fallback tier (Murakumo extract) for
  non-OCDS jurisdictions (e.g. JP GEPS). GitHub/PR push, where used, is **member-/operator-
  principal** (their own credentials or the actor's leashed self-key), never a platform key.

### 8.1 G8 attestation (outward-gate UNLOCKED)

**G8 is UNLOCKED for nyusatsu — founder Lv7+ (Council 1/1), 2026-06-27.** Per the Bootstrap
operational premise (Council attestation = PR-review), the attestation is executed as the
review/merge of this ADR change. This authorizes the OUTBOUND class: live social posting and
live award→contract writes.

**Necessary, not sufficient** — what G8-unlock does NOT do by itself:

1. It does **not** create the posting pipeline. Live posting still requires the **R2 residence**
   legs (`autorun` + `cell` registered in `cell-runner/cells.edn` + launchd LaunchAgent +
   `kotoba_bridge`) and an **R3 live-post path**, none of which are built yet (R1 = offline only).
2. It does **not** relax **G7 (non-custodial)**. Every live post/write must be signed by the
   actor's OWN sealed `did:key` (off-platform, present-only) + a member **CACAO leash** — never a
   platform-held key. G8 lifts the governance gate; G7 still dictates *how* the signing happens.
3. The G3/G2/G1/G5 content gates are unaffected — an unlocked actor still posts only attributed,
   primary-sourced, non-adjudicating, PII-clean records.

Operational sequence now authorized: build R2 (residence + autonomous read-only ingest, already
G7-exempt) → generate the actor's sealed `did:key` + member leash → enable the R3 live-post path
(`:dry-run` → `:prepared` → `:published`). Each step lands by PR.

# Consequences

**Positive**: closes the worldwide procurement-coverage gap on the canonical kotoba
substrate; OCDS alignment means most jurisdictions need no LLM and no scraping; charter
posture inherited from kosatsu (proven, 79 tests); JP work is preserved as one adapter, not
thrown away; jurisdiction-neutral lexicon unlocks cross-country market-size SoS joins.

**Negative / costs**: a `jpFiscal → govFiscal` lexicon codemod + JP-record migration;
per-jurisdiction adapter maintenance (auth keys for SAM.gov, format drift); i18n/currency
normalization surface; coverage will be long-tail (OCDS-native first, HTML stragglers last).

**Neutral**: legacy `actor-manifest.jsonld` retained read-only until the JP pipeline ports to
the EDN manifest; danjo's JP 政府調達 ingest and nyusatsu now overlap on JP — reconciled by
making danjo *consume* `govFiscal.procurementBid` rather than re-crawl (follow-up).

# Alternatives Considered

1. **New separate actor (`sekai-nyusatsu`/`bankoku`)** — rejected: duplicates the JP source
   set and the charter spine; the user asked to *extend* nyusatsu; one actor with a tiered
   registry is simpler to evolve.
2. **Define our own procurement schema instead of OCDS** — rejected: OCDS is the de-facto
   global standard with 50+ publishers; reinventing forfeits free normalization + the `ocid`
   dedup key.
3. **LLM-extract every jurisdiction (nyusatsu's current single path)** — rejected as primary:
   costly, lossy, and unnecessary where OCDS/REST exists; kept only as the HTML/PDF fallback tier.
4. **Keep jsonld manifest** — rejected: jsonld is being retired repo-wide (kosatsu precedent);
   EDN manifest is the current convention.

# References

- `20-actors/nyusatsu/` (legacy JP actor: `actor-manifest.jsonld`, `CLAUDE.md`, `MIGRATION-TODO.md`)
- `20-actors/kosatsu/` (manifest.edn + methods/{ingest,weave,social}.clj — reused pattern)
- ADR-2606072000 kosatsu competing-claim mirror · ADR-2606212200 hirameki worldwide patent mirror
- ADR-2605262130 / 2605312345 (kotoba substrate) · ADR-2606230001 (actor→kotoba-mesh)
- OCDS — Open Contracting Data Standard, standard.open-contracting.org
- `00-contracts/lexicons/com/etzhayyim/apps/govFiscal/procurementBid.json` (new; spec §2)
