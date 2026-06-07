---
id: adr-2605212340-etzhayyim-ai-domain-cutover
title: "ADR-2605212340: legacy domain → etzhayyim.com cutover"
status: accepted
doc_type: adr
topic: domain-cutover
authoritative: true
last_verified: 2026-05-21
priority: 4.5
axis: infrastructure
weight: 0.50
priority_note: "Large-scale domain rename, 26,800+ files affected"
authoritative_for:
  - domain-cutover-to-etzhayyim-com
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605192100-etzhayyim-mission-charter
related: []
supersedes: []
superseded_by: []
---

# ADR-2605212340: legacy domain → etzhayyim.com cutover

**Status**: accepted (Phase A executed 2026-05-21)
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

# Context

The legacy domain (the etzhayyim top-level zone, referred to throughout this
ADR as `<LEGACY-DOMAIN>` to avoid self-cutover during sed pass) was the
canonical hostname under etzhayyim ownership. After migrating etzhayyim-project
apps + 20-actors + 90-docs to etzhayyim, the inherited code still referenced
`<LEGACY-DOMAIN>` in:

- **24,559 .jsonld files** (JSON-LD `@context` namespace URIs, e.g.
  `https://<LEGACY-DOMAIN>/ns/kotodama/v1`, `https://yabai.<LEGACY-DOMAIN>/ontology/context`)
- **677 .md files** (design docs, READMEs, ADRs migrated from etzhayyim)
- **596 .ts / 679 .py / 240 .json / 38 .toml / 23 .js / 10 .mjs files**
  (source code referencing `*.<LEGACY-DOMAIN>` subdomains for app deployment)
- Solidity contracts in 50-infra referenced `<LEGACY-DOMAIN>`

Total scope: ~26,800 files / 134,792 string occurrences.

The constitutional `Identity` rule in `/CLAUDE.md` declares
`https://etzhayyim.com` as the canonical domain (Cloudflare Registrar,
2026-05-15, live since DID publish 2026-05-17). Continued reference to
`<LEGACY-DOMAIN>` in canonical etzhayyim code is identity-incoherent.

## Constraints

1. **JSON-LD namespace URIs are schema identifiers.** Replacing
   `https://<LEGACY-DOMAIN>/ns/kotodama/v1` with the etzhayyim equivalent
   creates a new schema URI that must be served at etzhayyim.com to remain
   resolvable. External consumers (other AT Protocol participants, federated
   indexes) that pinned the legacy URI will get 404 until DNS/CDN routing
   serves both URIs.
2. **Subdomain DNS records.** `news.<LEGACY-DOMAIN>`, `bpmn.<LEGACY-DOMAIN>`,
   `yabai.<LEGACY-DOMAIN>`, etc. are real DNS records currently serving
   production traffic. Code change alone does not migrate traffic.
3. **Package prefix `etzhayyim-project-*` is intentional** (per CLAUDE.md
   "Existing seeded files with legacy prefixes will be renamed in a follow-up
   cutover"). OUT OF SCOPE for this ADR.
4. **`etzhayyim`** (the for-profit company name) is a separate identity from
   the domain. 792 files reference `etzhayyim`. OUT OF SCOPE for this ADR.

# Decision

**Execute a code-level domain cutover in two phases:**

## Phase A — EXECUTED 2026-05-21

Replaced `<LEGACY-DOMAIN>` → `etzhayyim.com` in canonical etzhayyim source code.

- **In scope**:
  - `.md`, `.ts`, `.tsx`, `.js`, `.mjs`, `.py`, `.toml`, `.json`, `.sol`,
    `.yaml`, `.yml`, `.svelte`, `.rs`, `.sh` files
- **Excluded (defer to Phase B)**:
  - `.jsonld` files (24,559) — schema identifiers requiring coordinated
    DNS+CDN cutover, not a string replace
  - `node_modules/`, `.venv/`, `vendor/`, `lib/*-fork/` — vendored deps
- **Preserved**:
  - `/CLAUDE.md`, `/README.md`, `/CHARTER-RIDER.md` (alias documentation)
  - `etzhayyim-project-*` package prefix
  - `etzhayyim` company-name references

**Execution result**: 3,087 files modified, 0 failed, 0 source files with
`<LEGACY-DOMAIN>` remaining.

## Phase B — pending

For the 24,559 `.jsonld` schema URIs:

- Stand up `https://etzhayyim.com/ns/*` JSON-LD resolver that serves the same
  schema bodies currently served at `<LEGACY-DOMAIN>/ns/*`
- Cloudflare worker: rewrite + dual-serve (both domains return same context)
- Schedule deprecation of legacy `/ns/*` URIs only after external consumers
  have migrated (≥90-day notice)
- Then bulk-replace JSON-LD context URIs in this repo

# Consequences

- 3,087 source/config/design-doc files now reference `etzhayyim.com`.
- Identity-coherence violation removed for code; remains for `.jsonld`.
- No breakage for external consumers in Phase A (only internal code).
- Production deployment URLs still point to `*.<LEGACY-DOMAIN>` (DNS, not code).
- Solidity contracts: code references changed; on-chain state unchanged.

# Alternatives Considered

1. **All-at-once cutover (26,800 files, including .jsonld)** — rejected:
   silently breaks federated JSON-LD resolution.
2. **Defer entirely until DNS migration is complete** — rejected: code
   identity-incoherence violates `/CLAUDE.md` Identity rule.
3. **Replace only in newly authored files, leave seeded** — rejected:
   doesn't address the migrated bulk.

# Notes

- `<LEGACY-DOMAIN>` placeholder used in this ADR text to prevent the
  document itself from being mutated by the sed pass it documents.
- The legacy domain literal can be reconstructed from git history of any
  pre-cutover file, or from /CLAUDE.md / /README.md / /CHARTER-RIDER.md
  alias docs (which were preserved).

# References

- `/CLAUDE.md` — Identity (CRITICAL) section
- ADR-2605170900 (etzhayyim/root as canonical home)
- ADR-2605192100 (Mission Charter)
- Verification scan 2026-05-21: 2,829 source files + 24,559 .jsonld files
