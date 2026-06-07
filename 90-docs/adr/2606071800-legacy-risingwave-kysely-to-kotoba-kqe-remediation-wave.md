---
id: adr-2606071800-substrate-remediation-wave
title: "ADR-2606071800: legacy RisingWave/Hyperdrive/Kysely → kotoba-kqe read-path remediation wave"
status: proposed
doc_type: adr
topic: substrate-remediation-wave
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 90-docs/_registry/substrate-remediation-inventory.txt
depends_on:
  - 2605172000   # RW-free state substrate
  - 2605262130   # kotoba storage substrate unification
  - 2605312345   # kotoba Datom = first-class canonical state
  - 2605191648   # substrate-boundary lefthook (the commit-time guard)
related:
  - 2606071400   # omise kotoba-native promotion (this wave's reference conversion)
  - 2606012100   # okaimono (reference kotoba-native impl)
supersedes: []
superseded_by: []
---

# ADR-2606071800: legacy RisingWave/Hyperdrive/Kysely → kotoba-kqe read-path remediation wave

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

The substrate boundary is unambiguous: **kotoba Datom log is the first-class canonical
state** (ADR-2605312345); the read path is **`kotoba-kqe` arrangements (EAVT/AEVT/AVET/VAET)**
directly over content-addressed blocks (ADR-2605262130 D7); **RisingWave / Hyperdrive /
Kysely / Postgres are prohibited** as canonical or as a projection/cache layer.

A commit-time guard exists — `substrate-boundary` lefthook (ADR-2605191648,
`70-tools/scripts/lint/substrate-boundary.mjs`) blocks `kysely`/`pg`/`risingwave`/
`hyperdrive` imports in *newly staged* files. **But it only gates new diffs.** The
app-coverage audit (2026-06-07) found a large body of **pre-guard legacy code** that still
reaches its read path through RisingWave-via-Hyperdrive + Kysely SQL:

- **137 code files across 75 modules** with actual `createKyselyDb`/Hyperdrive/RisingWave
  usage (gate-prohibition *text* in `.edn`/`.md` excluded). Full machine-readable list:
  **`90-docs/_registry/substrate-remediation-inventory.txt`**.
- Concentration: `60-apps/etzhayyim-project-yatabase` (28), `20-actors/magatama` (25),
  then a long tail of 1–4 per module (maps, auth, open-* apps, …).

These predate both the kotoba unification and the lint guard. They are not charter-clean:
the read path is a SQL projection the boundary forbids. The `okaimono` (ADR-2606012100),
`warifu`, `todoke`, and now `omise` (ADR-2606071400) actors are the **reference kotoba-native
pattern** (EAVT Datoms + `kotoba-kqe` reads); the legacy footprint must converge to it.

# Decision

Open a **remediation wave** to migrate the 137-file / 75-module legacy footprint from
RisingWave/Hyperdrive/Kysely reads to **`kotoba-kqe` over the canonical Datom log**, tracked
to **zero**, and **close the guard gap** so the count is shrink-only.

**1. Frozen-legacy allowlist (shrink-only).** Snapshot the inventory as
`90-docs/_registry/substrate-remediation-inventory.txt`. Extend the `substrate-boundary`
lint with a **frozen allowlist** seeded from this snapshot: a listed legacy file may keep its
forbidden import; any file **not** on the list (new or migrated-then-regressed) is blocked, as
today. The allowlist may only **shrink** — a CI check fails if a path is added to it. This
converts an unbounded legacy liability into a monotonically decreasing debt counter.

**2. Migration order (cheap → load-bearing).**
   - **Phase A — manifest-only actors** (legacy `actor-manifest.jsonld` with no/å thin code,
     e.g. business-manager, yotei, organizer, talent): rewrite to kotoba-native `manifest.edn`
     + `lex/*.edn` + cells, mirroring `okaimono`/`omise`. Cheap, no data migration. (omise is
     the worked example, ADR-2606071400.)
   - **Phase B — single-reference apps** (the ~60 modules at count 1–2): replace the lone
     `createKyselyDb(env.HYPERDRIVE)…` read site with a `kotoba-kqe` query over the same
     entity shape; the write path already (or should) append Datoms.
   - **Phase C — load-bearing apps** (yatabase 28, magatama 25, maps): staged per-module
     migration with its own ADR + parity tests (read-path equivalence vs the retired SQL
     view) before the SQL view is deleted. `maps` (134 XRPC / 51 node-type production app) is
     the largest single migration and gets a dedicated follow-up ADR.

**3. Reference recipe (per file).** `createKyselyDb(env.HYPERDRIVE).selectFrom(X)…` →
`kotoba.kqe.query([:find … :where …])` over the entity's Datoms; remove the Hyperdrive
binding from `wrangler` config; entity schema becomes `kotoba/schema.edn`. The okaimono/omise
`py/agent.py` + `kotoba/schema.edn` pair is the canonical shape to copy.

**4. Exit criterion.** Wave closes when the inventory reaches 0 modules and the
`substrate-boundary` lint runs **without** a frozen allowlist (i.e. the allowlist is empty and
removed). At that point every read path is `kotoba-kqe` and the boundary is enforced for the
*entire* tree, not just new diffs.

**Scope of THIS ADR:** raise the wave, snapshot the inventory, define the frozen-allowlist
guard + phasing + recipe + exit criterion. The per-module migrations land as their own scoped
PRs against this ADR.

**Implemented in this wave** (the guard, not the migrations):
- `70-tools/scripts/lint/substrate-remediation-audit.mjs` — full-tree ratchet; `--write` seeds
  the allowlist, `--audit` FAILS on any storage violation absent from it and WARNs on graduated
  entries. Wired as a `pre-push` lefthook command.
- `70-tools/scripts/lint/substrate-frozen-allowlist.json` — the frozen snapshot (124 files at
  seed; shrink-only).
- `substrate-boundary.mjs` (pre-commit) extended to **grandfather** frozen-legacy storage
  violations to a warning (so unrelated edits to a legacy file are not blocked) while still
  hard-blocking storage imports in any non-frozen file.

# Consequences

- Turns a silent, unbounded substrate-boundary violation (137 files) into a tracked,
  shrink-only debt with a hard CI ratchet — no new violation can be added and no migrated file
  can regress.
- Makes the boundary real for the *existing* tree, closing the "guard only gates new diffs"
  gap that let the legacy footprint accumulate.
- Large up-front migration cost concentrated in yatabase/magatama/maps; mitigated by phasing
  (cheap manifest rewrites first) and per-module parity tests before any SQL view deletion.
- `maps` loses no functionality but its 125-file production read path is the longest pole;
  explicitly deferred to a dedicated ADR so this wave is not blocked on it.

# Alternatives Considered

1. **Leave legacy as-is, rely on the existing lint for new code** — rejected: the boundary is
   a constitutional invariant (ADR-2605312345), not a going-forward style preference; 137
   files reading through a forbidden SQL projection is a standing violation.
2. **Big-bang migrate everything at once** — rejected: yatabase + magatama + maps are
   load-bearing; a single PR would be unreviewable and unsafe. Phased + allowlist-ratcheted is
   the only tractable path.
3. **Allow RisingWave as a read-only cache under kotoba** — rejected: ADR-2605262130 D7 + N8
   explicitly forbid any SQL projection/cache layer; the read path is `kotoba-kqe` directly.

# References

- ADR-2605172000 — RW-free state substrate
- ADR-2605262130 — kotoba storage substrate (no RisingWave/SQL; read path = kotoba-kqe)
- ADR-2605312345 — kotoba Datom = first-class canonical state
- ADR-2605191648 — substrate-boundary lefthook (the commit-time guard being extended)
- ADR-2606071400 — omise kotoba-native promotion (worked Phase-A conversion)
- `90-docs/_registry/substrate-remediation-inventory.txt` — the tracked 137-file / 75-module snapshot
