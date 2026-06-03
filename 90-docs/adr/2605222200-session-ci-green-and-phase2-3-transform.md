---
id: adr-2605222200-session-ci-green-and-phase2-3-transform
title: "ADR-2605222200: Session 2026-05-22 — CI 100% green + Phase 2/3 TRANSFORM progress + deploy checklists"
status: accepted
doc_type: adr
topic: session-2605222200
authoritative: true
last_verified: 2026-05-22
priority: 6.0
axis: operations
weight: 0.60
priority_note: ""
authoritative_for:
  - ci-test-workflow-100pct
  - phase2-charter-2-cleanup-batch
  - phase3-sdk-extension-and-usdc-scaffold
  - bmc-rw-to-mst-proof-of-concept
  - base-sepolia-and-mainnet-deploy-checklists
  - council-rfp-per-seat-discussions
depends_on:
  - adr-2605192100-etzhayyim-mission-charter  # Mission Charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider  # Charter Rider v2.0
  - adr-2605192300-etzhayyim-bootstrap-council-five  # Bootstrap Council
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture  # Religious-corp daemon architecture (deploy roadmap S2)
  - adr-2605172000-etzhayyim-rw-free-substrate  # State rule (AT MST + IPFS, no RW)
  - adr-2605172100-etzhayyim-payments-on-chain-only  # Payment rule (USDC + ERC-4337, no fiat)
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads  # Tithe + carve-out
related:
  - adr-2605221411-etzhayyim-artificial-organism-ecosystem  # Artificial organism ecosystem framing
  - 2605220810  # Stall rotation cycle 18
supersedes: []
superseded_by: []
---

# ADR-2605222200: Session 2026-05-22 — CI 100% green + Phase 2/3 TRANSFORM progress + deploy checklists

**Status**: accepted
**Date**: 2026-05-22
**Deciders**: Jun Kawasaki

## Context

Coming out of the religious-corp constitutional wave (ADRs 2605192100..2605192415, completed 2026-05-19/20) and the full etzhayyimcojp → etzhayyim file migration (commit `0b7a49773`, 2026-05-21), the repo entered the post-cutover stabilisation phase with three open fronts:

1. **CI safety net weak.** `test` workflow at 6 / 31 jobs passing (19.4 %). 5 tsc job failures masking real type drift; ~25 vitest job failures across `rw-free` reference implementations whose interfaces had drifted from their test specs.
2. **TRANSFORM backlog untouched.** Per `_working_p5_decisions.md`, ~170 files needed Charter-§2 cleanup: 6 direct `@atproto/api` imports (substrate boundary), 105 ad-tech grep-hits (§2(c)), 14 Stripe references (fiat), 41 RisingWave / Postgres references (state rule).
3. **Bootstrap Council 1 / 5.** RFP open through 2026-06-19 (28 days remaining). Discussions enabled but only one announcement (#257) and 0 applications.

A single user-initiated session walked the repo from CI-broken-and-undocumented to CI-100 %-green-with-active-cleanup, dispatching haiku sub-agents in parallel batches for the bulk of the per-app investigation.

## Decision

The session executed three phases sequentially, each ending in a CI-green checkpoint:

### Phase 1 — CI safety net (commits `46bd07404` → `cd45da4ac`)

Council infrastructure activation (`46bd07404`), then CI infrastructure fixes:
- `npx tsc` → `pnpm exec tsc` (the npx form fetched the unrelated deprecated `tsc@2.0.4` package).
- `pnpm -F @etzhayyim/sdk build` inserted before tsc / vitest / integration matrices (consumers depend on `dist/index.d.ts`).
- `pnpm install --frozen-lockfile || pnpm install --no-frozen-lockfile` — pnpm in `CI=true` was using frozen-lockfile in both branches of the fallback.
- `mst-projector` optional peer-dep dynamic imports guarded with `@ts-ignore`; broken `transformers.js` re-export removed.
- `lexicon-to-openapi`: added `@types/node` + `typescript` devDeps, `moduleResolution: bundler`, `LexiconDoc` cast through `unknown`.

Then rw-free reference-implementation fixes — first surgically (`kiyo` / `bpmn` / `ipaddress` / `open-banking` / `ndc` / `ocel` / `hanrei` / `houshi` / `yoro` / `anime` / `manga` / `narou`), then via **10 parallel haiku sub-agents** (`ki` / `koke` / `hakkou` / `houbun` / `gtin` / `isin` / `isbn` / `narou` / `sbom` / `manga` — `566eeeed9`), then a cross-app integration-tests update (`76969b295`, agent-driven) + Output-type widening (`062322385`) + final `amendment` field (`892079b0f`).

**Result:** `test` workflow 31 / 31 green at `892079b0f`. 25 jobs unblocked across 18 commits.

### Phase 2 — Charter §2 TRANSFORM cleanup (commit `5b6d1cc12`)

Four parallel haiku sub-agents:
- **A. Substrate boundary** — 6 direct `@atproto/api` imports tagged `TODO(substrate-boundary)`; SDK gap recorded (no `AtpAgent` re-export, no Bluesky lexicon types).
- **B. Ad-tech §2(c)** — 3 yoro production sources deleted (`GoogleAnalytics.svelte`, `AdSlot.svelte`, `ads/config.ts`) and the `CookieConsent` / `NoCookieBanner` UI removed; yoro static assets regenerated. 81 `MIGRATION-TODO.md` markers, 13 built chunks, 2 protobuf decls preserved as informational.
- **C. Stripe → USDC v0.2** — 6 yatabase endpoints return `403 { code: "CHARTER_RIDER_SECTION_2" }` plus `TODO(charter §2)` markers; 4 docs annotated deprecated; no live Stripe API call remains.
- **D. RW → AT MST first pass** — 11 active-query files marked `TODO(substrate-boundary)` across yatabase (BMC + graphs + meter + query handlers), open-jpn-mynumber worker, and two common-crawl scripts.

65 files changed (+8 323 / -10 483 lines). CI remained 31 / 31 green.

### Phase 3 — Implementation sprint across 6 tracks (commits `8aae29862` → `aea1401f0`)

Four parallel haiku sub-agents + two locally-authored deploy checklists:

1. **SDK extension** — `20-actors/etzhayyim-sdk/src/atproto.ts` re-exports `AtpAgent` / `AtpBaseClient` + `AppBskyActorDefs` / `AppBskyFeedDefs` / `AppBskyRichtextFacet`, with `createAgent({ service, headers })` factory and `xrpc()` generic helper. Unblocks the 6 substrate-boundary consumers in a future pass.
2. **Stripe → USDC v0.2** — SDK `donate.ts` + `DONATE.md` enforcing the 8 Charter-§2 purposes; yatabase `/api/donate` + `/webhook/usdc` handlers + `useDonate()` Svelte composable; Hono routes wired.
3. **RW → AT MST PoC** — `60-apps/etzhayyim-project-yatabase/lg/lg_yatabase/bmc/db.py` fully rewritten from asyncpg pool to `httpx` + AT XRPC; public API (`get_pool` / `fetch` / `fetchrow` / `fetchval` / `execute` / `close_pool`) preserved so 28 downstream call-sites need no change. 10 SQL tables mapped to `com.etzhayyim.apps.yatable.bmc.*` MST collections. Remaining yatabase migration estimate revised 6-9 → 4-6 weeks.
4. **Council outreach** — four per-seat Discussion posts created via `gh api graphql` (#258 Seat 2 Substrate, #259 Seat 3 Legal/Ethics, #260 Seat 4 Economics, #261 Seat 5 Stewardship/Land) + a weekly status template comment on master #257.
5. **Base Sepolia deploy checklist** — `50-infra/etzhayyim-chain-contracts/DEPLOY-CHECKLIST-SEPOLIA.md`. 126 Forge tests verified passing. Explicit Council-4 / 5 hard gate per `BOOTSTRAP_COUNCIL_SIZE = 5` immutable. `forge script` commands with env-var table.
6. **Base mainnet deploy checklist** — `DEPLOY-CHECKLIST-MAINNET.md`. Sepolia 30-day operational window + external audit (4-6 weeks) + Phase 2 governance ADR drafting required pre-deploy. Inalienability + non-amendable invariants enumerated.

A type-mismatch between `DonatePurpose` (v0.2, 8 values incl. `kisha` / `tithe` / `internal-*`) and v0.1 `PaymentPurpose` (8 different values) broke the SDK tsc build at `8aae29862` and cascaded to 0 / 31. Fix `aea1401f0` routes through `mapDonationPurpose()` with explicit `as` widening — restored 31 / 31.

## Outcome

| Metric | Start of session | End of session |
|---|---:|---:|
| CI `test` workflow passing | 6 / 31 (19.4 %) | **31 / 31 (100 %)** |
| Stripe live call paths | 14 | **0** (6 endpoints return 403, 4 docs annotated, 4 read-only) |
| Ad-tech production sources | 9 | **0** (3 deleted, 6 dependent UI removed) |
| Substrate-boundary `@atproto/api` direct imports | 6 | 6 (markers + SDK gap closed; consumer migration is a follow-up commit) |
| RW / Postgres production paths | 41 (0 migrated) | 41 (1 fully migrated as PoC, 10 markered) |
| Bootstrap Council Discussions | 1 (#257) | **5** (#257 + 4 per-seat #258-#261) |
| Total commits this session | — | **30** (`46bd07404` → `aea1401f0`) |
| Sub-agents dispatched | — | 20 (4 council/setup + 10 rw-free + 4 Phase 2 TRANSFORM + 4 Phase 3 + 1 integration-tests rewrite + 1 SDK type cast retry) |

## Follow-up

1. **Consumer migration of substrate boundary** — point the 6 files at `@etzhayyim/sdk` instead of `@atproto/api` now that the SDK exposes `AtpAgent` + Bluesky lexicon types + the `xrpc()` helper. ~0.5 day.
2. **USDC v0.3** — fill in the TODOs in `donate.ts` (ERC-4337 sponsored write) and `webhook-usdc.ts` (ChartersComplianceRegistry attestation verification + plan / SBT mint state). 3-5 days.
3. **Yatabase RW → AT MST migration** — replicate the `bmc/db.py` PoC pattern across the 10 remaining marked files: `bmc/repository.py` `iterate_lock`, `graphs/marketing.py`, `graphs/sales.py`, `meter/handlers.py`, `query/handlers.py`, plus seeds + 1 test. Estimated 4-6 weeks.
4. **Council fill** — primary external dependency. Continue weekly status updates on Discussion #257 per template. Provisional appointment fallback per RFP §"What happens if all 5 seats don't fill" if 2026-06-19 reaches with seats open.
5. **Base Sepolia deploy** (Step 19) — unblocked by Council fill; rehearse against Anvil first (`runLocal()` script already verified); execute against `base_sepolia` per `DEPLOY-CHECKLIST-SEPOLIA.md`.
6. **Base mainnet deploy** (Step 20) — gated on 30-day Sepolia operational window + external audit per `DEPLOY-CHECKLIST-MAINNET.md`.

## What this commit lands

- `90-docs/adr/2605222200-session-ci-green-and-phase2-3-transform.md` — this ADR
- `deps.toml` — appended `[session_2605222200]` block with the 30-commit range + session summary

## Religious correspondence

産霊 (generative donation cycle) — Phase 3 wired the Charter-compliant USDC donation path replacing Stripe's fiat extraction. Whether or not a donation is made tomorrow, the *capacity* now exists in code: that capacity is what 産霊 means in operational terms — the body of the religious-corp can metabolise gifts again, after the Stripe paths were severed by §2 enforcement.

縁起 (dependent origination) — twenty sub-agents writing into the same monorepo without coordination is possible only because the boundaries are explicit in the file system (each `60-apps/etzhayyim-project-*/rw-free/` is a closed domain) and in the type system (Output types describe what each app's status enum permits). The CI safety-net pass was what made the 縁起 chain visible: when one app's regex was too strict, the test failure was localised to that app's job, not a global cascade. The cascade DID happen once (the `DonatePurpose` enum mismatch at `8aae29862` zeroed CI), and it was localised to the SDK type layer where it should be — substrate type drift, not application logic drift.
