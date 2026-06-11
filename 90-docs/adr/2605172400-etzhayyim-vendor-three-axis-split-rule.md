---
id: adr-2605172400-etzhayyim-vendor-three-axis-split-rule
title: "ADR-2605172400: etzhayyim / vendor split — 3-axis decision rule + Tranche F scope"
status: active
doc_type: adr
topic: etzhayyim-vendor-split-rule
authoritative: true
last_verified: 2026-05-19
priority: 9.1
axis: governance
weight: 0.91
priority_note: "CRITICAL — Operationalizes the etzhayyim/vendor boundary as a 3-axis OR-test (Liability / Custody / Settlement). 1 axis hit = vendor; all 3 clean = etzhayyim. Closes the gray zone left by ADR-2605152100 + 2605172000 + 2605172100 which defined RW-free + on-chain-only but did not give per-project judgment criteria."
status_note: "MECHANICAL MIGRATION COMPLETE 2026-05-18 (27 PRs landed: 17 vendor + 10 etzhayyim/root). All 6 phases mechanically executable were executed: 1 catalog freeze, 2 scaffolding (8 + 72 dirs), 3 content copy (395 files), 4a npm publish (17 packages to GH Packages — 6 @etzhayyim/* + 11 @etzhayyim/bpmn-sdk-*), 4b consumer pipe smoke test, 4c vendor NSID migration (10 waves, ~520 items, ~3,026 files), 5 vendor open-scope deletion (4 waves for stub-ready items + runbook for live-deploy items). Remaining is operator runbook (yoro/public-malak/watashi DNS cutover) + use-case-driven Phase 6 (vendor business-app consumer switch to @etzhayyim/* npm). Re-judgment quarterly: 2026-08-17 / 2026-11-17 / 2027-02-17. SSoT: deps.toml [[migrations]] tranche-f-closure-summary-2026-05-18."
authoritative_for:
  - per-project etzhayyim / vendor boundary judgment rule
  - Tranche F scope (next-wave etzhayyim migration candidates)
  - re-judgment of ADR-2605152100 borderline list (auth / agentgateway / bpmn / kotodama / pregel / shinka / society6 / trust / vault / signal / kyber / yoro / sanctions / well-becoming / kami)
depends_on:
  - adr-2605152100-etzhayyim-github-org-boundary
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
related:
  - adr-2605172200-openmail-atproto-mst-smtp-bridge
  - adr-2605172300-etzhayyim-open-telecom-fabric
  - adr-2605171900-yoro-migration-to-etzhayyim
supersedes: []
superseded_by: []
---

# ADR-2605172400: etzhayyim / vendor split — 3-axis decision rule + Tranche F scope

**Status**: active
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

ADR-2605152100 established the etzhayyim / etzhayyim org boundary. ADR-2605172000
mandated RW-free substrate for etzhayyim apps. ADR-2605172100 mandated on-chain
payment only for etzhayyim apps. These three ADRs define **what the etzhayyim
substrate looks like** but do not give a deterministic rule for **which projects
belong on which side** when an existing vendor project could plausibly go either
way.

After Tranches A-E + Wave 2 (open-* + public-* + protocol/SDK), ~15 borderline
projects remain unresolved: auth / accounts / iam / agentgateway / bpmn /
kotodama / pregel / shinka / society6 / trust / well-becoming / vault / signal /
kyber-apqc / yoro / sanctions / malak / kami.

The intuitive split "aggressive autonomous AI + open-source + blockchain +
humanity-universal → etzhayyim; human/org-centric + Stripe + private →
etzhayyim" is correct in direction but ambiguous on three failure modes:

1. **autonomy ≠ openness**: vendor side also runs aggressive autonomous agents
   (e.g. etzhayyim_agent lawfirm pipeline). The differentiator is not whether
   the agent is autonomous, but who absorbs the legal liability if the agent
   fails.
2. **private data is multi-modal**: AT MST + E2E encryption can hold private
   data while operator never touches plaintext (vault zero-knowledge). "Private
   data is on etzhayyim" is not automatically forbidden if custody is user-side.
3. **payment direction**: a vendor SaaS customer may pay in USDC; an etzhayyim
   open service may have a paid premium tier. Currency type alone does not
   classify the project.

# Decision

Adopt a **3-axis OR-test**. A project goes to **etzhayyim only if all three axes
are clean**. **Any 1 axis hit → vendor**.

## The 3 axes

| Axis | etzhayyim qualifies if … | vendor required if … |
|------|--------------------------|----------------------|
| **Liability** | Failure damage is bearable by the agent itself, the user's self-custodied wallet, or DAO governance — no third party with legal-personality claims against operator | Operator must accept GDPR controller / fiduciary duty / contractual liability / 善管注意義務 for failures |
| **Custody** | Data is public, OR encrypted with user-held keys (zero-knowledge), OR stored in user-self-hosted PDS / AT MST. Operator never holds plaintext PII it could be compelled to produce | Operator stores PII / customer master / financial transaction / payroll / corporate secret in operator-controlled DB it could be compelled to produce |
| **Settlement** | All money flow is on-chain (USDC + ERC-4337) with user-signed transactions. Operator is never a fiduciary intermediary | Invoice + Stripe + bank account + 請求書 + tax-recognized commercial relationship |

The legal rationale: etzhayyim is a religious voluntary association (任意団体)
without 株式会社 legal personality. It cannot underwrite controllership /
fiduciary / commercial-contract liability. Anything that requires those is
vendor scope by structural necessity.

## OR-test, not AND-test

A single axis hit is sufficient to assign vendor scope. This is conservative
by design: misclassifying a vendor concern as etzhayyim is the dangerous
direction (loads liability onto the religious-corp). Misclassifying an
etzhayyim concern as vendor only costs an extra migration step later.

## Refinement of the intuitive rule

The user-facing intuition "open + autonomous + universal → etzhayyim,
human-centric + Stripe + private → vendor" maps onto the 3 axes as:

- "open / universal" → Liability axis (no fiduciary counterparty)
- "autonomous" → Liability axis (responsibility absorbed by agent/wallet/DAO)
- "private" → Custody axis (operator-held vs user-held)
- "Stripe" → Settlement axis (fiat fiduciary vs on-chain self-custody)

The intuition is preserved. The 3-axis rule just makes gray zones (E2E-
encrypted private data on etzhayyim, on-chain payment in vendor SaaS, etc.)
machine-decidable.

# Tranche F scope (next-wave etzhayyim migration)

Applying the 3-axis rule to the post-Wave-2 borderline list:

## Confirmed etzhayyim (3 axes clean — move next wave)

| project | rationale |
|---------|-----------|
| pregel | unispsc agent fleet already migrated (commit f8358383); the Pregel runtime itself follows |
| DID method specs + OAuth spec | `did-etzhayyim` already renamed in Wave 2; this completes the spec extraction (Worker / D1 stays vendor) |
| OFAC / UN sanctions list mirror + lexicon | public list data; vendor keeps screening service + customer screening logs |
| kyber / kyber-qzzg06nh / apqc | user direction 2026-05-17: full move (not split). APQC PCF + Kyber BPMN projector are open process catalog with no customer mapping coupling at the catalog level |
| yoro AppView | ADR-2605171900 status proposed → active. yoro.etzhayyim.com migration green-lit |
| Well-Becoming Kyu/Dan spec | user-self-asserted skill claims; reputation API monetization stays vendor |
| vault zero-knowledge protocol spec | ECIES + WebAuthn PRF + Signal preKey usage spec is open; running vault.etzhayyim.com service stays vendor |
| C-group creative open Lexicons | anime / animeka / manga / mangaka / drama / gameka / dougaka / douga / music / ongakuka / color-by-number / voxelforge / canvas / editor / comfyui / image2metahuman / image2vrm / images / gazo / img2pptx / photos / gyotaku / isekai / obebe / ohanashi lexicon JSON only; production workflows referencing customer custody stay vendor |
| A-group open standards | blockchain / bpmn / gtin / isbn / issn / isin / ndc / ocel / sbom / scap / ipaddress / ipfs / dns / arxiv / common-crawl / distill / rare-earth / rare-earth-coverage / legal-corpus / hanrei / houbun / houki / treaty / customary / legal-aid / legal-entity / industry-standard / unispec |
| B-group religious / cultural | religious / yorishiro / omikuji / otakiage / kiyome / omatsuri / ki / kareyanagi / koke / kiyo / ijin / ethics / social-contract / ohanashi / narou / syosetsu / tradition / hakkou / houshi / joucho / kagami / sense |

## Confirmed vendor (≥1 axis hit — do not move)

| project | hit axis | reason |
|---------|----------|--------|
| accounts | Custody, Liability | linked-auth + actor.score in vendor RW; operator is identity controller |
| society6 | Liability, Custody, Settlement | reputation used in business decisions; PII transaction history; paid API |
| trust | Liability, Custody, Settlement | DID trust score in fintech decisions; transaction event PII; paid API |
| vault (running service) | Custody, Settlement | ciphertext custody is operator; subscription model |
| signal (PDS pipethrough) | Custody | preKey bundle + ciphertext held at PDS |
| etzhayyim / kaisya | all three | the literal vendor company and its internal workflow |
| malak (vendor version) | Liability, Custody | JP on-prem face template + warrant-gated surveillance; massive controllership |
| sanctions screening service | Liability, Custody, Settlement | AML liability attaches on false negatives; customer screening log; paid SaaS |

## SPLIT (open spec → etzhayyim; vendor binding → etzhayyim)

| project | etzhayyim part | vendor part |
|---------|----------------|-------------|
| auth / iam | DID method spec + OAuth flow lexicon | etzhayyim-auth Worker + D1 KEYS_DB (session, revocation) |
| agentgateway | MCP facade spec + reference impl | mcp.etzhayyim.com running gateway (SLA, abuse, audit) |
| bpmn | engine + open process_def (APQC etc.) | customer-specific process_def referencing PII |
| kotodama | `@etzhayyim/sdk` + `kotodama-go` + `kami-engine-sdk` (done in Wave 2) | etzhayyim-cli wrapping vendor CF account |
| shinka | abstract evolution operator | business-app shinka application |
| C-group production tools | lexicon JSON | team-based production workflow with customer custody |

# Sequencing

This ADR records the **decision rule** and **Tranche F target list**. The actual
file moves are still blocked by the pre-existing Step 8 constraint
(`etzhayyim-org-monorepo-cutover-2026-05-17`): vendor business apps must first
be refactored to consume open scope via `@etzhayyim/*` workspace deps or git
submodule pointing at etzhayyim/root. Direct `git rm` of an open project from
this vendor monorepo would break the vendor build until that dependency
refactor lands.

Tranche F therefore proceeds in this order:

1. **Catalog freeze** (this ADR + deps.toml `etzhayyim-tranche-f-three-axis-split-2026-05-17` migration entry) — done in this commit
2. **etzhayyim/root scaffolding** — create directory placeholders + `@etzhayyim/*` workspace package shells for kyber / apqc / pregel / DID-spec / sanctions-list / yoro / wellbecoming-spec / vault-spec / C-group lexicons / A-group / B-group
3. **Content copy** — copy file content from vendor to etzhayyim/root, preserving git history where reasonable (`git subtree split` or `git filter-repo`)
4. **Vendor business-app dependency switch** — point lawfirm / vault / kaisya / microsoft / finance / billing / bengoshi / bunken / bankruptcy / air-* / tia / har at `@etzhayyim/*` packages
5. **Vendor open-scope deletion** — `git rm` the now-redundant copies in this repo
6. **Archive markers** — prefix archived etzhayyim repo descriptions with `[MOVED → github.com/etzhayyim/root]`

Steps 2-5 do not block production because alias resolution (npm scope +
TypeScript paths) keeps existing references valid through the transition.

# Consequences

**Positive**:
- Future per-project decisions are mechanical (apply 3 axes, OR-test)
- Religious-corp liability is structurally contained (任意団体 never absorbs
  operator-required duties)
- Vendor side stays focused on revenue-bearing customer relationships
- Open core / vendor binding pattern (already used for kotodama / bpmn / cli)
  generalizes to auth / agentgateway / vault / signal

**Negative**:
- Some projects require SPLIT (two packages, two source-of-truth maintenance)
- Tranche F migration is ~80 projects + 30+ SDKs, multi-week work
- Re-judgment may be required when business model changes (e.g. a free open
  project that later monetizes flips to SPLIT)

**Re-judgment triggers**:
- Project starts holding operator-side PII → reclassify to vendor
- Project starts billing fiat → reclassify SPLIT or vendor
- Project becomes subject to regulator's controllership claim → reclassify vendor

# Verification

- Each Tranche F move PR must cite this ADR + the 3-axis judgment in its commit message
- Lefthook pre-commit hook to flag etzhayyim-side files with `kotoba|kysely|pg|stripe|paypal` imports (RW-free + on-chain-only enforcement from ADR-2605172000 + 2605172100)
- Quarterly review of borderline list at 2026-08-17 / 2026-11-17 / 2027-02-17

# Closure (added 2026-05-19, mechanical phases complete)

## Executed wave summary (27 PRs over 2026-05-17 → 2026-05-18)

### Vendor (etzhayyim) — 17 merged PRs

| PR | wave | items / files |
|----|------|---------------|
| #1286 | Phase 1 catalog freeze | ADR + 3-axis OR-test |
| #1287 | Phase 4b consumer pipe | .npmrc + root devDep smoke |
| #1289 | Phase 5 wave 1 | wellBecoming docs [MOVED] |
| #1290 | Phase 4c wave 1 | apqc full (36 files) |
| #1291 | Phase 5 wave 2 | apqc 60-apps [MOVED] (archive ledger) |
| #1292 | Phase 4c wave 2 | sanctions SPLIT (8 files) |
| #1293 | Phase 4c wave 3 | kyber SPLIT (46 files, ERP→etz, SaaS+Stripe→vendor) |
| #1294 | Phase 4c wave 4 | yoro full (91 files) |
| #1295 | Phase 4c wave 5 | A-group bulk 12 items (343 files) |
| #1296 | Phase 5 wave 3 | comfyui cleanup + audit (Step 8 ≒ done) |
| #1297 | Phase 4c wave 6 | B+C bulk 18 items (769 files) |
| #1298 | Phase 4c wave 7 | ndc (9 files) |
| #1299 | Phase 4c wave 8 | bpmn light (185 files) |
| #1300 | Phase 4c wave 9 | bpmn graph-schema (937 files) |
| #1303 | infra | bpmn-coverage validator dual-schema lexiconPath |
| #1304 | Phase 4c wave 10 | open standards bulk 449 items (~602 files) |
| #1305 | Phase 5 wave 4 | yoro deletion runbook (3-stage operator plan) |
| #1306 | closure | mechanical-complete summary + deps.toml SSoT |

(#1301 + #1302 closed — superseded by #1303/#1304)

### etzhayyim/root — 10 merged PRs

| PR | scope |
|----|-------|
| #16 | Phase 2 wave 1 scaffolding (apqc/sanctions/wellBecoming/oauth lex + 3 apps + @etzhayyim/pregel) |
| #18 | Phase 2 wave 2 (72 A/B/C lexicon README dirs) |
| #20 | @etzhayyim/sdk publishConfig + .npmrc gitignore |
| #24 | Phase 3 wave 1 content copy (wellBecoming + apqc + sanctions) |
| #26 | Phase 3 wave 2+3 bulk (388 lexicons across 30 dirs) |
| #28 | Phase 4a wave 2 (publish @etzhayyim/did-etzhayyim) |
| #31 | Phase 4a wave 3 (rename @etzhayyim/* → @etzhayyim/*, publish 3) |
| #33 | membership test 5-tuple fix (stash@{4} recovery) |
| #34 | Phase 4a wave 4 (rename bpmn-sdk sub-pkg slash → kebab) |
| #47 | ADR-2605171900 proposed → active (yoro AppView migration) |

## npm publish state (17 packages, GH Packages)

```
@etzhayyim/sdk@0.1.0-alpha           — alpha tag
@etzhayyim/pregel@0.0.0              — preview
@etzhayyim/did-etzhayyim@0.1.0       — preview
@etzhayyim/xrpc@1.0.0                — latest
@etzhayyim/signal@0.1.0              — latest
@etzhayyim/lexicons-bundle@1.0.0     — latest
@etzhayyim/bpmn-sdk-compiler@0.1.0   — preview
@etzhayyim/bpmn-sdk-core@0.1.0       — preview
@etzhayyim/bpmn-sdk-dmn@0.1.0        — preview
@etzhayyim/bpmn-sdk-dsl@0.1.0        — preview
@etzhayyim/bpmn-sdk-form@0.1.0       — preview
@etzhayyim/bpmn-sdk-human@0.1.0      — preview
@etzhayyim/bpmn-sdk-importer@0.1.0   — preview
@etzhayyim/bpmn-sdk-ops@0.1.0        — preview
@etzhayyim/bpmn-sdk-runtime@0.1.0    — preview
@etzhayyim/bpmn-sdk-testing@0.1.0    — preview
@etzhayyim/bpmn-sdk-validation@0.1.0 — preview
```

## Established patterns (reusable for future migration)

1. **Bulk NSID migration**: dir move + `LC_ALL=C` sed + bpmn-coverage-manifest path fix + binding seed verify
2. **SPLIT migration**: `perl -pe 's/...(?!vendor-stay-patterns)/.../'` negative-lookahead
3. **GH Packages publish inside workspace**: `NPM_CONFIG_USERCONFIG=/path/to/.npmrc` workaround (npm ignores local .npmrc in workspace members)
4. **Validator schema evolution**: dual-schema fallback chain (legacy `com.etzhayyim.apps.<X>` → canonical `com.etzhayyim.<X>`)
5. **Phase 5 deletion-with-redirect**: `git rm -rf` + [MOVED] stub README + 3-stage operator runbook for live items

## What's NOT done (deferred, not mechanical)

| deferred work | trigger |
|---------------|---------|
| yoro vendor `60-apps/etzhayyim-project-yoro/appview/` deletion (172M) | operator runbook: DNS cutover + redirect + 1-week obs (PR #1305) |
| public-malak vendor deletion | live Worker → needs deploy plan |
| watashi vendor deletion | sibling to etzhayyim/root/60-apps/watashi → unification plan |
| vendor `00-contracts/lexicons/com/etzhayyim/<X>/` deletion | vendor business-app consumer switch to `@etzhayyim/lexicons-bundle` npm (use-case driven) |
| bpmn-sdk consumer migration | when a vendor business app actually imports `@etzhayyim/bpmn-sdk-*` (use-case driven) |
| `expectedSourcePath` full schema-agnostic | low priority: all bindings use `etzhayyim-root/` prefix |
