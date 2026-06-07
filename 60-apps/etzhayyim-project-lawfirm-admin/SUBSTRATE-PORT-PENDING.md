# SUBSTRATE-PORT-PENDING — etzhayyim-project-lawfirm-admin

**Status**: 🟡 **PARTIAL — 2026-05-24** (`src/app.ts` ported; Svelte adapter + package rename still deferred to ADR-2605214000).

## Background

11 files of `appview/lawfirm-admin-mcp-component/` (Svelte appview + worker + Kotodama SDK wiring) were dropped during the 2026-05-21 batch migration because the etzhayyim implementation uses substrate primitives that are prohibited on the etzhayyim side.

## What's done (2026-05-24 substrate-port wave)

- Surprise audit finding: this app is a **thin-edge proxy** with no Kysely / HyperDrive usage. Substrate-port is correspondingly simple — no MST rewrite needed.
- `src/app.ts` — `ACTOR_DID` etzhayyim.com → etzhayyim.com; `NSID_PREFIX` `com.etzhayyim.apps.lawfirmAdmin.` → `com.etzhayyim.lawfirmAdmin.`; dispatcher default URL etzhayyim.com → etzhayyim.com.

## Substrate violations remaining (ADR-2605172000 / 2605172100 boundary)

1. ~~`src/app.ts` — DID / NSID / dispatcher URL rename.~~ **DONE 2026-05-24.**
2. `svelte/src/routes/xrpc/[...path]/+server.ts` — forwards to `mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message` → re-target to `mcp.etzhayyim.com` (same pattern as gov-mcp-component port).
3. ~~Kysely / HyperDrive references.~~ **N/A — never present in this app.**
4. ~~Lexicon namespace rename.~~ **DONE 2026-05-24** (NSID_PREFIX cutover in `src/app.ts`).
5. Package name `@etzhayyim/kotodama-*` → `@etzhayyim/kotodama-*` (ADR-2605214000 atomic cutover — still pending).

## Cross-links

- Source archive: `/Users/junkawasaki/github/etzhayyim-apps-etzhayyim/_archive/migrated-to-etzhayyim-2026-05-21/60-apps/etzhayyim-project-lawfirm-admin/`
- Substrate rules: ADR-2605172000, ADR-2605172100
- Rename plan: ADR-2605214000 §3
- Migration batch: ADR-2605212100 (referenced by DEPRECATED.md but missing — author as part of follow-up)
