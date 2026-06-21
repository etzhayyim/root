# SUBSTRATE-PORT-PENDING — etzhayyim-project-gov

**Status**: 🟡 **PARTIAL — 2026-05-24** (Kysely→MST done in `src/app.ts`; package rename + Svelte xrpc adapter still deferred to ADR-2605214000 atomic cutover).

## Background

This app is the etzhayyim-side **public-services hub** (`gov.etzhayyim.com`) — COFOG-aligned, 8 path-based DID sub-agents covering healthcare / insurance / welfare / education / prevention / housing / employment / child_family. The 12 missing files were dropped during the 2026-05-21 batch migration because the etzhayyim implementation relied on a substrate stack prohibited on the etzhayyim side.

## What's done (2026-05-24 substrate-port wave)

- `src/app.ts` (282 → 319 LoC) — full Kysely + HyperDrive Postgres removal. 3 write handlers + 5 read handlers now use `@etzhayyim/sdk` `Etzhayyim.write` / `Etzhayyim.read`.
- 5 Lexicons authored at `00-contracts/lexicons/com/etzhayyim/gov/`: `agency.json`, `official.json`, `consult.json`, `municipality.json`, `procedure.json`.
- Lexicon NSID rename — 12 call sites in `src/app.ts` migrated from `com.etzhayyim.apps.gov.*` to `com.etzhayyim.gov.*`.
- `ACTOR_DID` migrated: `did:web:gov.etzhayyim.com` → `did:web:etzhayyim.com:gov`.
- Pagination semantics flipped: 5 list queries dropped offset/limit, switched to cursor pass-through (MST is cursor-paged).
- etzhayyim-legacy bookkeeping fields (`vertex_id`, `_seq`, `created_date`, `sensitivity_ord`, `owner_did`, `id`, `actor_did`, `org_did`) dropped from emitted records — MST envelope carries equivalent metadata.

## Substrate violations remaining (ADR-2605172000 / 2605172100 boundary)

1. ~~`appview/gov-mcp-component/src/app.ts` — Kysely → MST.~~ **DONE 2026-05-24.**
2. `appview/gov-mcp-component/svelte/src/routes/xrpc/[...path]/+server.ts`
   - Forwards to `mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message`. Re-target to etzhayyim XRPC adapter.
3. `appview/gov-mcp-component/svelte/svelte.config.js` + `package.json`
   - Package name `@etzhayyim/kotodama-gv7ps2m1` → `@etzhayyim/kotodama-gv7ps2m1` (ADR-2605214000 §3 atomic cutover wave — still pending).
4. `src/app.ts` retains `@etzhayyim/kotodama-host-sdk` import (preserved by design — atomic cutover deferred). Once ADR-2605214000 lands, drop the unused `createKyselyDb`, `Database` imports and switch the package name.

## Deliberately preserved as-is

- COFOG-aligned 8 path-based DID taxonomy (`healthcare` / `insurance` / `welfare` / `education` / `prevention` / `housing` / `employment` / `child_family`)
- WIT contract `etzhayyim:gov/public-service@1.0.0` (to be re-namespaced to `etzhayyim:gov/public-service@1.0.0`)
- Agency registry data model fields (name / nameLocal / jurisdiction / branch / level / cofog / parentAgencyDid / establishedAt / legalBasis / websiteUri)

## Cross-links

- Source archive: `/Users/junkawasaki/github/etzhayyim-apps-etzhayyim/_archive/migrated-to-etzhayyim-2026-05-21/60-apps/etzhayyim-project-gov/`
- Substrate rules: ADR-2605172000 (kotoba), ADR-2605172100 (substrate ladder)
- Rename plan: ADR-2605214000 §3 atomic identifier cutover (still pending legal registration trigger)
- Migration batch: ADR-2605212100 (referenced by DEPRECATED.md but missing — author as part of follow-up)
