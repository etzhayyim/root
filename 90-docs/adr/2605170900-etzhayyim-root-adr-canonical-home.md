---
id: adr-2605170900-etzhayyim-root-adr-canonical-home
title: "ADR-2605170900: etzhayyim/root as canonical home for religious-corp open ADRs"
status: active
doc_type: adr
topic: etzhayyim-root-adr-canonical-home
authoritative: true
last_verified: 2026-05-17
priority: 6.5
axis: organization
weight: 0.65
priority_note: "Establishes the ADR placement policy. Active immediately; no migration needed for pre-existing ADRs (they remain in original location as historical record). All new open-scope ADRs go here."
authoritative_for:
  - ADR placement policy (which repo each ADR lives in)
  - etzhayyim/root as canonical home for open religious-corp ADRs
  - ID convention for etzhayyim/root ADRs
depends_on: []
related:
supersedes: []
superseded_by: []
---

# ADR-2605170900: etzhayyim/root as canonical home for religious-corp open ADRs

**Status**: active
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

ADR-2605152100 (held in a separate private repo) established the GitHub org boundary and migrated open religious-corp content into `etzhayyim/root`. Steps 1-7 of that ADR's migration plan are complete:

1. ✅ `etzhayyim.com` registered (Cloudflare, 2026-05-15T12:08:36Z)
2. ✅ `github.com/etzhayyim` org created (2026-05-10T14:23:43Z)
3. ✅ `github.com/etzhayyim/root` monorepo created (2026-05-15T12:20:47Z, public, Apache 2.0)
4. ✅ ADR-2605152100 status: proposed → active
5. ✅ Scaffold (LICENSE / README / CLAUDE.md / deps.toml / .gitignore / lefthook.yml)
6. ✅ Content seed: Tranches A-E (00/10/20/30/50/60/90) + Tranche Wave 2 (19 protocol/SDK/infra repos)
7. ✅ Existing standalone open repos archived with `[MOVED → github.com/etzhayyim/root]` description prefix (26 repos)

What remains undecided after Step 7: **where new ADRs about open-scope work should live**.

# Decision

**etzhayyim/root is the canonical home for all new open religious-corp ADRs**, starting 2026-05-17.

## Placement matrix

| Scope | Canonical home |
|---|---|
| **Open religious-corp activities** (blockchain / baien / bpmn / lexicon / pregel / atproto / ameno / open-data 22 本 / public governance / open infrastructure) | **`etzhayyim/root/90-docs/adr/`** |

When in doubt: **new open-scope ADRs go here.**

## ID convention

`YYMMDDhhmm-<topic-slug>.md` ID format. etzhayyim/root starts at **2605170000** series and continues forward in time.

## Migration of existing open-scope ADRs

**No physical migration.** Pre-existing open-scope ADRs (baien series, ameno, open-ot, bonsai, Shannon-Optimal, etc.) remain in their original locations as their **historical canonical**. The alternative (copy here) would violate the "single canonical source" rule from `90-docs/CLAUDE.md`.

Going forward, references to prior open-scope ADRs cite by ID and short title only. If a follow-up ADR supersedes a pre-existing open-scope ADR, the new ADR lives in etzhayyim/root and uses `supersedes: [adr-2605...]`.

# Consequences

## 正の効果

- **New open ADRs co-locate with implementation.** Reduces distance for contributor / agent reading code-then-ADR-then-code.
- **Clear ID range** (etzhayyim/root ≥2605170xxx) makes the canonical home of any ADR ID immediately clear.
- **Apache 2.0 attribution preserved** for new ADRs (etzhayyim/root is Apache 2.0).

## 負の効果 / コスト

- **ADR registry maintenance** for `90-docs/_registry/docs.json` (pending). Tooling work required.
- **Backward URL link rot risk** if pre-existing open-scope ADRs move. Mitigation: keep historical ADRs in their original location.

## Migration plan

This decision is active immediately. No migration of historical ADRs.

- [x] `etzhayyim/root/90-docs/CLAUDE.md` — docs system rules with placement policy
- [x] `etzhayyim/root/90-docs/adr/README.md` — ADR index
- [x] `etzhayyim/root/90-docs/adr/template.md` — ADR template
- [x] `etzhayyim/root/90-docs/adr/2605170900-...md` — this ADR
- [ ] Future: `90-docs/_registry/docs.json` + validator tooling
- [ ] Future: lefthook `adr-validate` hook adapted for etzhayyim/root (currently only trailing-ws + EOF checks)

# Alternatives Considered

## A. Move ALL open-scope ADRs to etzhayyim/root

Physically migrate every pre-existing open-scope ADR (baien, ameno, open-ot, bonsai 10+, Shannon-Optimal, MCP-cell-membrane, LangGraph series, Pydantic/SQLAlchemy/Alembic/SQLMesh contracts, etc.) to etzhayyim/root, leaving stub redirects upstream.

却下理由: 30+ file moves with associated cross-reference updates is a huge surface area for breakage. Pre-existing URLs (in commit messages, external blog posts, AI Search engines, directory_index entries) would 404. Cost > benefit.

## B. Single ADR home in a third repo (e.g., `etzhayyim/adrs`)

Create a dedicated ADRs-only repo and house everything there.

却下理由: separates ADRs from implementation (worst of all worlds for cross-reference distance). Also adds a third repo unnecessarily.

# References

- `90-docs/CLAUDE.md` (this repo) — docs system rules
- `90-docs/adr/README.md` (this repo) — ADR index
- `CLAUDE.md` (repo root) — operating entity identity
