---
id: adr-2606033400-session-close-consensys-kotoba-migration-sweep
title: "ADR-2606033400: Session close — Consensys kotoba migration COMPLETE: sweep + truth-pass + kotoba-E2E waves 1+2 (53 apps V→A) — final A=158 / V=22"
status: active
doc_type: adr
topic: session-close-consensys-kotoba-migration-sweep
authoritative: true
last_verified: 2026-06-03
related:
  - adr-2606011400-consensys-pattern-etzhayyim-product-etzhayyim-infra-vendor
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
  - adr-2605152100-etzhayyim-github-org-boundary
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605172100-etzhayyim-payments-on-chain-only
supersedes: []
superseded_by: []
---

# ADR-2606033400: Session close — Consensys-pattern kotoba migration sweep

**Status**: active
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

A self-paced `/loop` drove a per-app migration sweep over a 24-app priority batch
plus Bucket C/D in `90-docs/MIGRATION-STATUS.md`. Each fire classified ONE app's
PRIMARY function under the **Consensys pattern** (ADR-2606011400, product-front /
infra-vendor) + the **3-axis OR-test** (ADR-2605172400 — Liability / Custody /
Settlement: any axis hit ⇒ stays etzhayyim vendor) and either built an on-chain
`kotoba` reference impl (`@etzhayyim/sdk`, AT PDS, no RW/Stripe/HYPERDRIVE/D1)
for product-front (a)/(c) apps, or marked the app **Bucket V — confirmed
vendor-resident** for regulated-infra (b) apps.

# Decision (what this sweep concluded)

## Final git-authoritative tracker state

| Bucket | Count | Meaning |
|--------|------:|---------|
| A — DONE | 105 | has a committed `kotoba/src/index.ts` |
| B — CLEAN | 209 | no kotoba, no TODO, no prohibited imports |
| C — NEEDS-CODEMOD | 0 | CLEARED |
| D — TODO-PENDING | 7 | all build-targets resolved; remainder = legacy codemod chores |
| **V — VENDOR-RESIDENT** | **75** | regulated-infra primary function — stays etzhayyim |

The **priority batch (24/24)**, **Bucket C (0)**, and **all Bucket C/D
asserted-resolved names (50/50)** are resolved git-authoritatively (each app has
either a committed `kotoba/src/index.ts` OR a unique `^- **<app>**` Bucket V
entry OR is a documented phantom). The `/loop` cron job + pending wakeup were
deleted at STOP.

## The one genuine product migration this arc: `repository`

`repository` (ADR-0039 Repository-in-Graph) was the single **(c) mixed** build:
the git object model (blob → tree → commit → ref over Actor DID) is the user's
own first-party source code → migrated to AT PDS records (`repository/kotoba`,
5/5 tests). FaaS build dispatch + execution stay etzhayyim via consent-capability.

## Tracker truth-passes (the consequential meta-finding)

Prose "RESOLVED" assertions in the tracker were **not trustworthy**; three
git-authoritative sweeps corrected the accounting (the judgments were sound — the
bookkeeping under them was not):

1. **6 Bucket-A phantoms** — `6ir`, `air-sched`, `analytics`, `bim`,
   `business-person`, `legal-corpus` were listed as DONE but had zero committed
   `kotoba/src` (only stray `node_modules`) and no source in either repo.
   Removed; A count made git-authoritative (committed `index.ts` = 105).
2. **1 mis-filed C/D name** — `mangaka` was asserted "already in A" but was
   neither built nor in V. It is a generation-compute pipeline (ComfyUI/USD;
   carry-forward test fails) → Bucket V, same family as voxelforge/dougaka/yukkuri.
   The consumer catalog front is its sibling `animeka` (in A).
3. **10 Bucket-V duplicates** — `accounts` + the 9 `air-*` apps were each present
   TWICE: a prior/parallel session had already classified them (b), and this
   session re-classified them, inflating V to 85. Deduped to the authoritative
   **75** (`sort -u` of `^- **<app>**`); both copies agreed on (b).

## Root cause (the guard for any future loop run)

The loop's STEP-1 PICK rule was *"skip any app with an existing `kotoba/src` OR
already in Bucket V."* The implementation checked `kotoba/src` but **not Bucket V
membership** — half the documented rule. So ~10 fires re-classified already-
resident apps, producing the duplicates + V inflation. **Future loop runs MUST
check Bucket V membership in PICK**, not just `kotoba/src`. (This is honest
record, not "completed cleanly" — every app is genuinely resolved, but the
accounting needed this correction pass.)

## Vendor-resident roster (75) — what stays etzhayyim

Grouped by primary function (full per-app axis rationale in
`90-docs/MIGRATION-STATUS.md` Bucket V):

- **Aviation operations (9)** — Liability/Custody/Settlement: `air-book`,
  `air-cargo`, `air-crew`, `air-dcs`, `air-ffp`, `air-mro`, `air-ops`, `air-sms`,
  `air-yield`.
- **Identity & auth (2)** — Custody: `accounts`, `auth`.
- **Payments / settlement / financial ledgers (7)** — Settlement/Custody:
  `harai`, `shiharai`, `wire`, `web4`, `credits`, `kaikei`, `resource-provider`.
- **Messaging / email / comms relays (PII custody) (13)**: `communicator`,
  `gmail`, `microsoft`, `microsoft-graph`, `meet`, `meeting-recorder`,
  `messenger`, `mailer`, `phone`, `os-messaging`, `fax`, `external-service-adapter`,
  `briefing`.
- **Social-PII ingest (3)** — Custody: `facebook`, `x`, `outreach`.
- **Generation / render / inference compute (RW/GPU) (8)**: `mangaka`,
  `voxelforge`, `dougaka`, `yukkuri`, `ongakuka`, `shinka`, `game-play-uploader`,
  `recap`.
- **Infra / execution / gateway / orchestration (11)**: `site`, `business-edge`,
  `cloudflare-browser-render`, `playwright`, `hub`, `yorishiro`, `scheduler`,
  `robot`, `keiei`, `ops`, `llm`.
- **RW / data backends (7)**: `coverage`, `cowork`, `yatabase`, `yabai`, `jukyu`,
  `deai`, `manimani`.
- **Security / LE / regulated-screening (8)**: `crypto-asset-freeze`,
  `cyber-drill`, `open-kyber`, `open-ossekai`, `ses`, `society6`, `tia`, `insatsu`.
- **Web-content hosting/generation (2)** — RW + LLM compute: `webmk`, `webya`.
- **Other (5)**: `hc` (health, all-3-axis), `intel` (CUI custody), `tenso`
  (zero-knowledge E2E), `watashi` (device-session relay), `resource-planner`
  (per-user resource custody).

# Amendment 2026-06-03 — kotoba-E2E migration wave (founder-directed)

The founder ruled that **PII / CUI / LE / yabai-risk are safe to migrate
on-substrate via kotoba E2E** (ADR-2605181100 encrypted-record envelope) — so
they front (E2E-sealed), they do NOT stay etzhayyim for confidentiality reasons. This
reframes the Consensys split: the regulated **DATA** migrates (plaintext if
public, E2E if sensitive); only regulated **EXECUTION** (fiat-MoR settlement,
GPU/LLM inference, enforcement/blocking actions, credential/secret custody) stays
etzhayyim, consumed via consent-capability.

Pattern established + de-risked:
- `@etzhayyim/sdk-mock` gained `encryptedWrite`/`encryptedRead` (faithful
  in-memory Tahoe envelope: recipient read-cap access-control + innerType routing).
- `intel/kotoba` = reference (plaintext `coverageProjection` + E2E
  `inferredCohort`), tested incl. access-control isolation.

**Wave 1 (24 apps V→A, all verified green — tsc + vitest + import-scan, ~140
tests):** intel, air-cargo, yabai, deai, manimani, open-kyber, open-ossekai,
society6, tia, insatsu, hc, tenso, watashi, resource-planner, voxelforge, shinka,
business-edge, yorishiro, scheduler, robot, keiei, ops, jukyu, crypto-asset-freeze.
Each splits public-meta (plaintext) from sensitive payload (E2E `encryptedWrite`).
Counts after wave: **A 105→129, V 75→51.**

**Aviation-8 resolved (founder, option A):** air-book/crew/dcs/ffp/mro/ops/sms/
yield accepted as already-fronted — the aviation consumer product layer is on
etzhayyim via `flight-offer` + `air-sched`; the 8 stay etzhayyim as settlement/safety
EXECUTION backends consumed via consent-capability. The full 32-app founder
directive is complete: 24 migrated V→A (incl. air-cargo), 8 accepted as
already-fronted.

# Amendment 2026-06-03 (2) — E2E wave 2 + program close

Wave 2 (29 apps V→A, all green ~260 tests): aviation-8 FULL migration
(air-book/crew/dcs/ffp/mro/ops/sms/yield) + harai/shiharai/wire/web4/credits/
resource-provider + communicator/meet/meeting-recorder/messenger/phone/
os-messaging/fax/briefing/external-service-adapter + webmk/webya/site/hub/coverage/
cowork. DATA migrated (plaintext public + E2E sensitive); only irreducible
EXECUTION stays etzhayyim (fiat-MoR rail per ADR-2605172100, GPU/LLM inference,
credential custody, 100B site archive). Counts: **A 129→158, V 51→22.**

**MIGRATION PROGRAM COMPLETE (founder option 1).** The 22 remaining vendor apps
are CONFIRMED FINAL — credential custody (accounts/auth), third-party-ToS social
PII (facebook/x/gmail/outreach), external-IdP token exec (microsoft/microsoft-graph/
mailer), fiat-MoR settlement (kaikei/game-play-uploader), GPU/LLM generation
(mangaka/dougaka/yukkuri/ongakuka/recap), infra/gateway/storage (cloudflare-browser-
render/playwright/llm/yatabase/cyber-drill), regulated PII intake (ses). Each stays
etzhayyim for a reason E2E cannot resolve; further migration would require redesigning the
underlying execution (e.g. on-chain USDC rails). Across both E2E waves, 53 apps
migrated V→A. Final: **A=158, V=22.**

# Consequences

- The Consensys boundary is now per-function reconciled across the full app
  surface: product-front (105 kotoba) vs etzhayyim infra-vendor (75 Bucket V), with
  the regulated functions consumed by etzhayyim fronts via consent-capability.
- `MIGRATION-STATUS.md` counts are git-authoritative and deduped.
- **HONEST PENDING**: Bucket D = 7 legacy codemod-cleanup chores (import-removal
  in already-classified apps — `common-crawl` / `cpc` / `email-service-adapter` /
  `fax` family), NOT migration targets; tracked but not loop-blocking. The
  vendor-side RW retirement / cutover sequences (NDL/KG ingest, kotoba datomic
  handoff) remain governed by their own ADRs and are not part of this product
  classification sweep.
