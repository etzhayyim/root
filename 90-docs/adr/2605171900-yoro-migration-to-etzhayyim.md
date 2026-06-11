---
id: adr-2605171900-yoro-migration-to-etzhayyim
title: "ADR-2605171900: yoro AppView migration — code + DNS + deployment to yoro.etzhayyim.com"
status: active
doc_type: adr
topic: yoro-migration-to-etzhayyim
authoritative: true
last_verified: 2026-05-18
status_note: "Activated 2026-05-18 by vendor Phase 4c wave 4 (PR #1294) — full yoro NSID migration com.etzhayyim.apps.yoro.* → com.etzhayyim.yoro.* completed across 91 vendor consumer files. Stages 3-5 (DNS cutover yoro.etzhayyim.com → yoro.etzhayyim.com, redirect, vendor 60-apps/etzhayyim-project-yoro/ deletion) remain operator runbook items."
priority: 7.0
axis: organization
weight: 0.70
priority_note: "Stages 1-2 (code + spec restore + DNS placeholder) done in this commit. Stages 3-5 (deployment + redirect + cleanup) require follow-up PRs and operator action."
authoritative_for:
  - yoro AppView canonical home (etzhayyim/root)
  - yoro.etzhayyim.com as user-facing surface
  - migration policy for hybrid open-concept / legacy-deployed surfaces
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
related:
supersedes: []
superseded_by: []
---

# ADR-2605171900: yoro AppView migration — code + DNS + deployment to yoro.etzhayyim.com

**Status**: proposed (Stages 1-2 done, Stages 3-5 pending)
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

`yoro` is conceptually positioned by **ADR-2605091900 "Yoro = Flowering / Fruiting Surface"** as the open, user-facing surface of the Bonsai/Cultivar ecosystem (ADR-2605091300). The implementation previously lived in a separate (private) upstream monorepo and deployed at a legacy domain — outside the etzhayyim brand, despite the open conceptual framing.

This created a misalignment with **ADR-2605152100 "etzhayyim GitHub Org Boundary"**: open religious-corp surfaces should live under `etzhayyim` (org + domain).

During the 2026-05-17 Tier 1 cleanup (commit 5af9dd82) the yoro lexicon + BPMN spec dirs were defensively removed from `etzhayyim/root` because the legacy deployment was upstream-managed. This was an overshoot: the Lexicon spec is AT Protocol-compatible (open by design), and the project is conceptually open per ADR-2605091900.

This ADR establishes the migration plan and records Stages 1-2 (already done in the same commit as this ADR).

# Decision

**`yoro` migrates fully to etzhayyim:**

| Layer | Was (legacy) | Becomes (etzhayyim) |
|---|---|---|
| Project code | upstream `60-apps/etzhayyim-project-yoro/` | `etzhayyim/root/60-apps/etzhayyim-project-yoro/` |
| Lexicon spec | upstream `00-contracts/lexicons/com/etzhayyim/apps/yoro/` (15 JSON) | `etzhayyim/root/00-contracts/lexicons/com/etzhayyim/apps/yoro/` |
| BPMN spec | upstream `00-contracts/bpmn/com/etzhayyim/yoro/` (6 BPMN) | `etzhayyim/root/00-contracts/bpmn/com/etzhayyim/yoro/` |
| Domain | legacy domain | `yoro.etzhayyim.com` (etzhayyim CF zone `etzhayyim.com`) |
| Deployment | legacy CF account | etzhayyim CF account |
| DID resolver | legacy `did:web` | `did:web:etzhayyim.com` |
| License | proprietary | Apache 2.0 |

## Migration stages

### Stage 1 — Code + spec restoration (✅ this commit)

`rsync -a` from upstream:
- `60-apps/etzhayyim-project-yoro/` (293 MB working tree before build-artifact filtering; ~30-50 MB tracked after `.gitignore` excludes node_modules / .svelte-kit / dist)
- `00-contracts/lexicons/com/etzhayyim/apps/yoro/` (15 files: activity / activitySeen / health / ingestProductCategory / listApps / listPosts / listProductResearch / postAgencyUpdate / productResearch / projectEntity / ...)
- `00-contracts/bpmn/com/etzhayyim/yoro/` (6 files: actorQualityEnrich / platformPulse / respondToFollow / respondToMention / translatePost / translatePostBatch)

Sensitive-content scan: zero case-anchored markers (no `takahashi-hiroyuki`, no `0x06f...`, no `bitnest`, no `chain_freeze` etc.). Auth subsystem = `passkey` (WebAuthn, open standard).

### Stage 2 — DNS placeholder (✅ this commit)

CF API created on etzhayyim.com zone (`54dece4ac787807d4c3410243916a1e6`):

```
AAAA  yoro.etzhayyim.com  →  100::  proxied=true  ttl=1
record id: 5df2d02dd52796f169ecc04ec50d56ac
comment:   "yoro AppView placeholder (ADR-2605091900) — Worker/Pages binding pending"
```

`100::` is the RFC 6666 discard prefix — never actually resolves; exists only so CF accepts a Worker route or Pages custom-domain binding to `yoro.etzhayyim.com`.

### Stage 3 — AppView deployment (⏳ pending)

The project is a SvelteKit AppView with CF-compatible adapter. Two viable targets:

- **CF Pages**: connect `github.com/etzhayyim/root` as source, set build root to `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/`, output dir `.svelte-kit/cloudflare/`. Custom domain bind to `yoro.etzhayyim.com`.
- **CF Worker**: `wrangler deploy` from the existing `wrangler.jsonc` in the project, with route updated to `yoro.etzhayyim.com/*` and account_id pointed at the etzhayyim-owned account.

Before deploy, the project's hardcoded legacy-domain references must be replaced with `yoro.etzhayyim.com` (sed pass across `svelte/src/`, `static/`, build config).

Auth/billing decoupling: `lib/auth/passkey.ts` is open; any billing endpoints found in bundles are likely user-tier metadata and need a refactor pass to either (a) stay as open user-tier (free / member) or (b) call out to a separate paid-tier backend service.

### Stage 4 — legacy → yoro.etzhayyim.com redirect (⏳ pending)

On the legacy CF zone, replace the current yoro routing with a 301 redirect Worker:

```
return Response.redirect(`https://yoro.etzhayyim.com${url.pathname}${url.search}`, 301);
```

Grace period: 12 months minimum (per the etz_hayim → etzhayyim → etzhayyim rename precedent in the operator email migration plan). After grace, the redirect Worker is decommissioned and any remaining traffic returns 404.

### Stage 5 — Upstream cleanup (⏳ pending)

After Stage 3-4 stabilize:

- Remove `60-apps/etzhayyim-project-yoro/` from upstream
- Remove `00-contracts/lexicons/com/etzhayyim/apps/yoro/` from upstream
- Remove `00-contracts/bpmn/com/etzhayyim/yoro/` from upstream
- Update upstream `deps.toml [platform.operating_entity].public_page` to `https://yoro.etzhayyim.com/support/operator`
- Update upstream `CLAUDE.md` references

# Consequences

## 正の効果

- **Brand alignment**: open Bonsai surface (yoro) now lives on open domain (yoro.etzhayyim.com) under open monorepo (etzhayyim/root).
- **License clarity**: Apache 2.0 across the AppView, lexicon, and BPMN. External contributors can freely fork without proprietary-license friction.
- **Identity unification**: AppView resolves DID via `did:web:etzhayyim.com` (LIVE since 2026-05-17T03:25Z), matching its hosting domain.
- **ADR consistency**: actualizes the open framing already declared by ADR-2605091900 (Yoro = Flowering/Fruiting Surface) and ADR-2605091300 (Bonsai Cultivar).

## 負の効果 / コスト

- **Working tree bloat**: yoro adds 293 MB pre-filter to etzhayyim/root working tree (mostly Svelte build artifacts that `.gitignore` excludes; tracked footprint estimated 30-50 MB).
- **Refactor needed**: hardcoded legacy-domain references in code/config/static assets need a `sed` pass. Any upstream-only auth/billing endpoints need decoupling.
- **Two-step deploy**: Stage 3 requires CF Pages connection or Worker `wrangler deploy` — neither runnable from this commit alone.
- **12-month redirect window** ties up the legacy zone with a redirect Worker.
- **DID compatibility**: any existing user data on the legacy domain that references the legacy `did:web` continues to resolve; new data uses `did:web:etzhayyim.com`. Migration of legacy identities is out of scope for this ADR.

# Alternatives Considered

## A. Keep yoro on the legacy stack (don't migrate)

却下理由: contradicts ADR-2605091900 (Yoro = open Flowering/Fruiting Surface) and ADR-2605152100 (etzhayyim org boundary).

## B. Lexicon-spec-only migration (impl stays upstream)

却下理由: half-migration creates dual sources of truth. The Lexicon JSON would have to be cross-referenced from etzhayyim/root while the BPMN, code, and deployment stayed elsewhere. Increases coordination overhead vs. clean split.

## C. Full rewrite under new branding (e.g., flower.etzhayyim.com)

却下理由: yoro is established branding with existing user base; rewriting from zero discards the work already done. Migration preserves the surface contract (NSIDs, URLs, lexicon shape).

## D. Federate via AT Protocol (legacy PDS → yoro.etzhayyim.com AppView)

却下理由: viable long-term but adds AT federation complexity. The simpler migration (direct code + DNS swap with 301 redirect) is enough to actualize the open framing now; federation can be layered on later if multi-tenant requirements emerge.

# References

- ADR-2605091900 Yoro = Flowering / Fruiting Surface (conceptual framing — open)
- ADR-2605091300 Bonsai Cultivar Layer Above Myco-Yeast Substrate
- ADR-2605170900 (this repo) — etzhayyim/root as canonical home for open ADRs
- CF DNS record: AAAA yoro.etzhayyim.com → 100:: proxied (id 5df2d02dd52796f169ecc04ec50d56ac, created 2026-05-17)
- did:web:etzhayyim.com (LIVE since 2026-05-17T03:25Z)
