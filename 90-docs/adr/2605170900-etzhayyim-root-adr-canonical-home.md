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
priority_note: "Establishes the per-repo ADR placement policy. Active immediately; no migration needed for existing vendor ADRs (they remain in vendor as historical record). All new open-scope ADRs go here."
authoritative_for:
  - ADR placement policy (which repo each ADR lives in)
  - etzhayyim/root as canonical home for open religious-corp ADRs
  - ID convention to avoid collision with vendor monorepo
depends_on: []
related:
  - https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605152100-etzhayyim-github-org-boundary.md
  - https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/CLAUDE.md
supersedes: []
superseded_by: []
---

# ADR-2605170900: etzhayyim/root as canonical home for religious-corp open ADRs

**Status**: active
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

ADR-2605152100 (vendor monorepo) established the GitHub org boundary and migrated open religious-corp content from `gftdcojp/ai-gftd-apps-gftdcojp` into `etzhayyim/root`. Steps 1-7 of that ADR's migration plan are complete:

1. ✅ `etzhayyim.com` registered (Cloudflare, 2026-05-15T12:08:36Z)
2. ✅ `github.com/etzhayyim` org created (2026-05-10T14:23:43Z)
3. ✅ `github.com/etzhayyim/root` monorepo created (2026-05-15T12:20:47Z, public, Apache 2.0)
4. ✅ ADR-2605152100 status: proposed → active
5. ✅ Scaffold (LICENSE / README / CLAUDE.md / deps.toml / .gitignore / lefthook.yml)
6. ✅ Content seed: Tranches A-E (00/10/20/30/50/60/90) + Tranche Wave 2 (19 protocol/SDK/infra repos)
7. ✅ Existing standalone open repos in `gftdcojp` archived with `[MOVED → github.com/etzhayyim/root]` description prefix (26 repos)

What remains undecided after Step 7: **where new ADRs about open-scope work should live**. The vendor monorepo's `90-docs/adr/` directory has been the de-facto canonical ADR location for the entire platform (open + vendor). But now that etzhayyim/root is the canonical home for open content, it would be inconsistent for new open-scope ADRs to keep landing in the vendor monorepo.

# Decision

**etzhayyim/root is the canonical home for all new open religious-corp ADRs**, starting 2026-05-17.

## Placement matrix

| Scope | Canonical home | Rationale |
|---|---|---|
| **Open religious-corp activities** (blockchain / baien / bpmn / lexicon / pregel / atproto / ameno / open-data 22 本 / public governance / open infrastructure) | **`etzhayyim/root/90-docs/adr/`** | Same repo where the implementation lives → cross-reference distance = 0 |
| **Source-control boundary** (principal-vs-vendor split, org transfer, monorepo seed strategy, future re-org) | `gftdcojp/ai-gftd-apps-gftdcojp/90-docs/adr/` | Boundary ADRs are authored from the vendor perspective and reference both repos. They are written-once historical records. |
| **Vendor business operations** (lawfirm / vault / kaisya / microsoft / accounts / finance / billing / malak case-anchored Pregels / akuma redteam authorization / HR / family-office) | `gftdcojp/ai-gftd-apps-gftdcojp/90-docs/adr/` | Vendor implementation is there; ADRs co-located. |
| **Shared foundational ADRs** (Shannon-Optimal 8-Layer, MCP-as-Cell-Membrane, Bonsai Cultivar series, LangGraph patterns, Pydantic/SQLAlchemy/Alembic/SQLMesh contracts) | `gftdcojp/ai-gftd-apps-gftdcojp/90-docs/adr/` (historical) | Predate the org split. Used by both repos. Etzhayyim/root references them by full URL rather than duplicating. |

### Tie-breaker

When an ADR is ambiguous (e.g., a new open protocol design that also affects vendor infrastructure), **default to etzhayyim/root**. The principal owns the open ecosystem; vendor implementation follows.

## ID convention to avoid collision

Both repos use the `YYMMDDhhmm-<topic-slug>.md` ID format. To avoid cross-repo confusion:

- Vendor monorepo currently uses up to **2605152000** series (latest: 2605152100 was a vendor-side ADR for the org boundary)
- **etzhayyim/root starts at 2605170000 series** and continues forward in time

Cross-repo cross-references use full GitHub URLs:

```markdown
- [ADR-2604251830 Shannon-Optimal 8-Layer](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2604251830-shannon-optimal-layered-architecture.md)
```

## Migration of existing open-scope ADRs

**No physical migration.** Existing ADRs in `gftdcojp/ai-gftd-apps-gftdcojp/90-docs/adr/` that are open-scope (baien series, ameno, open-ot, bonsai, Shannon-Optimal, etc.) remain in the vendor monorepo as their **historical canonical**. Reasons:

1. **Cross-repo links rot less than file moves.** If we move `2605092350-baien-...` to etzhayyim/root, every URL pointing at the old vendor path 404s. Leaving it in place preserves backward compatibility.
2. **Vendor monorepo's docs registry stays intact.** `90-docs/_registry/docs.json` indexes all ADRs by repo-relative path. Moving files would require coordinated registry surgery.
3. **No duplication.** The alternative (copy to both repos) violates the "single canonical source" rule from `90-docs/CLAUDE.md`.

Going forward, etzhayyim/root references these by URL. If a follow-up ADR supersedes an open-scope vendor ADR, the new ADR lives in etzhayyim/root and uses `supersedes: [adr-2605...]` with a full URL pointer in `references`.

# Consequences

## 正の効果

- **New open ADRs co-locate with implementation.** Reduces cross-repo distance for contributor / agent reading code-then-ADR-then-code.
- **Vendor monorepo's ADR registry remains stable.** No churn from cross-repo file moves.
- **Clear ID range partitioning** (vendor ≤2605152xxx, etzhayyim/root ≥2605170xxx) makes the canonical home of any ADR ID instantly clear without checking both repos.
- **Apache 2.0 attribution preserved** for new ADRs (etzhayyim/root is Apache 2.0; vendor is proprietary).

## 負の効果 / コスト

- **Two ADR registries to maintain** (vendor's `90-docs/_registry/docs.json` + etzhayyim/root's eventual equivalent). Tooling parity work required.
- **Cross-repo URL link rot risk** if either repo is renamed or transferred. Mitigation: monitor with link checker, prefer `main` branch URLs over commit SHAs for stability.
- **Contributor onboarding** must explain the two-repo, two-ADR-home pattern. Mitigation: `90-docs/adr/README.md` explains the placement matrix; CLAUDE.md reinforces.

## Migration plan

This decision is active immediately. No migration of historical ADRs.

- [x] `etzhayyim/root/90-docs/CLAUDE.md` — docs system rules with placement policy
- [x] `etzhayyim/root/90-docs/adr/README.md` — ADR index with URL-linked vendor refs
- [x] `etzhayyim/root/90-docs/adr/template.md` — ADR template
- [x] `etzhayyim/root/90-docs/adr/2605170900-...md` — this ADR
- [ ] Future: `90-docs/_registry/docs.json` + validator tooling parity with vendor monorepo (Phase 2)
- [ ] Future: lefthook `adr-validate` hook adapted for etzhayyim/root (currently only trailing-ws + EOF checks)

# Alternatives Considered

## A. Keep all ADRs in vendor monorepo

All ADRs, including new open-scope ones, continue landing in `gftdcojp/ai-gftd-apps-gftdcojp/90-docs/adr/`.

却下理由: contradicts ADR-2605152100 § "Decision" which established etzhayyim/root as the canonical home for open content. Co-locating ADRs with implementation reduces cognitive distance. Vendor-side ADRs would be the wrong attribution license-wise (proprietary vs Apache 2.0).

## B. Move ALL open-scope ADRs from vendor to etzhayyim/root

Physically migrate every open-scope ADR (baien, ameno, open-ot, bonsai 10+, Shannon-Optimal, MCP-cell-membrane, LangGraph series, Pydantic/SQLAlchemy/Alembic/SQLMesh contracts, etc.) to etzhayyim/root, leaving stub redirects in vendor.

却下理由: 30+ file moves with associated cross-reference updates is a huge surface area for breakage. Existing URLs (in commit messages, external blog posts, AI Search engines, deps.toml directory_index entries) would 404. Cost > benefit; the placement matrix achieves the same logical outcome via URL references.

## C. Single shared ADR registry across both repos (submodule or sync script)

Add etzhayyim/root as a git submodule into vendor's `90-docs/adr/etzhayyim-root/`, or vice versa, with a sync script keeping `_registry/docs.json` aware of both.

却下理由: submodule complexity, sync drift risk, and breaks the org boundary that ADR-2605152100 establishes. Each repo owning its own ADR space is structurally simpler.

## D. Single ADR home in a third repo (e.g., `etzhayyim/adrs`)

Create a dedicated ADRs-only repo and house everything there.

却下理由: separates ADRs from implementation (the worst of all worlds for cross-reference distance). Also adds a third repo when the boundary is fundamentally two-way (principal-open vs vendor).

# References

- ADR-2605152100 [etzhayyim GitHub Org Boundary + Monorepo Seed Strategy](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605152100-etzhayyim-github-org-boundary.md) (vendor)
- `90-docs/CLAUDE.md` (this repo) — docs system rules
- `90-docs/adr/README.md` (this repo) — ADR index + placement matrix
- `CLAUDE.md` (repo root) — operating entity identity (etzhayyim = principal, Gftd Japan = vendor)
- vendor `90-docs/CLAUDE.md` [docs system rules](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/CLAUDE.md)
