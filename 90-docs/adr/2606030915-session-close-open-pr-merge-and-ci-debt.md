---
id: adr-2606030915
title: "ADR-2606030915: Session close — merge all open PRs (#779/#784/#789/#792/#793/#807/#798) + recorded CI debt"
status: active
doc_type: adr
topic: session-close-open-pr-merge-and-ci-debt
authoritative: false
last_verified: 2026-06-03
priority: 4.0
axis: process
weight: 0.40
priority_note: "session-close record; PR-merge triage with two red-CI merges accepted by operator and recorded as fix-forward debt"
authoritative_for: []
related:
  - adr-2606023200-session-close-ooyake-world-government-atlas
  - adr-2606021600-ooyake-world-government-atlas-tier-b-actor-r0
  - adr-2606021730-latent-entity-kotoba-datomic-refactor
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606021730 (latent-entity refactor — #798 is its P9/P10 RW-removal completion)
  - ADR-2606023200 (ooyake session-close — #807 records it + the deps.toml bump)
---

# ADR-2606030915: Session close — merge all open PRs + recorded CI debt

**Date**: 2026-06-03
**Status**: ACTIVE (documentation-only session closure)
**Deciders**: Jun Kawasaki

## Context

Operator request: 「https://github.com/etzhayyim/root/pulls を git merge」 — merge
every open PR. At session start the repo had **7 open PRs**, all targeting `main`,
all `MERGEABLE`. File-overlap analysis confirmed the seven touched **disjoint
paths** (the four ooyake PRs each touch one distinct file; #793 is dependabot;
#807 = `deps.toml` + a new ADR; #798 = kabuto/hagukumi/kataribe/kazaori/ossekai
files, no root `deps.toml`), so sequential squash-merges could not conflict.

Two of the seven were `UNSTABLE` (mergeable but red CI). Per AskUserQuestion the
operator chose **merge all 7** with **squash**.

## Decision (what shipped)

All 7 squash-merged into `main` (oldest→newest, no `--admin` needed — branch
protection did not block the red checks):

| PR | Branch | CI | Maps to |
|---|---|---|---|
| #779 | ooyake-world-government-atlas | clean | ADR-2606021600 (ISO3 country-unit names) |
| #784 | ooyake-maturity-refresh | clean | ADR-2606021600 (MATURITY.md) |
| #789 | ooyake-consumer-examples | clean | ADR-2606021600 (5-consumer examples) |
| #792 | ooyake-toolchain-docs | clean | ADR-2606021600 (deploy README + run_tests.sh) |
| #793 | dependabot/npm_and_yarn (3 dirs) | clean | — npm bump |
| #807 | ooyake-session-close | **red** | ADR-2606023200 + deps.toml |
| #798 | refactor/latent-entity-kotoba-datomic | **red** | ADR-2606021730 (RW→kotoba P9/P10) |

## Consequences

- All operator-named open PRs are merged; **zero open PRs** remained at session
  end. (A *separate* concurrent automation independently opened+merged the
  vendor-resident / RW→kotoba migration wave #800–#809 during the same window —
  out of scope here, noted only because it kept `main`'s HEAD moving.)

- **Recorded CI debt** — #807 and #798 carried three failing checks onto `main`.
  Root causes diagnosed from the job logs, all fix-forward:
  1. `docs-graph-jsonld-freshness` — `graph.jsonld` drift (disk 788 nodes vs
     committed 787): #807's new ADR-2606023200 node was not regenerated into the
     registry. **Fix**: regenerate `graph.jsonld` + `docs.json`, commit.
  2. `monorepo-health` — `test_simple_audits.py::TestDependabotDefunct::test_strict_passes_at_zero`
     now exits 1: the dependabot-defunct audit finds entries in
     `.github/dependabot.yml` pointing at directories removed by the concurrent
     vendor-resident migrations. **Fix**: prune defunct dependabot config entries.
  3. `lint-and-test` → substrate-boundary backstop — #798's migration diff has
     direct substrate imports outside the `@etzhayyim/sdk` seam. **Fix**: route
     the flagged imports through the SDK.

- This ADR + the `deps.toml` `[[adrs]]` entry are the only artifacts authored by
  *this* session; the working tree's other modified/untracked files (aratame
  actor, kabuto edits, kotoba submodule bump, etc.) belong to concurrent sessions
  and were left untouched — the commit is scoped to exactly these two paths.

## Alternatives Considered

- **Merge only the 5 clean PRs**, hold the 2 red ones for a fix-first pass.
  Offered; operator chose merge-all. The red checks are documented here as debt
  rather than silently absorbed.
- **Fix the CI failures in this session before closing.** Deferred — `main` was
  being actively churned by the concurrent #800–#809 migration wave, so the
  dependabot-defunct surface (and node counts) were a moving target; fixing
  against a settled HEAD avoids a race / re-clobber.
- **`gh pr merge --admin`.** Not needed — plain squash-merge succeeded for the
  red PRs (no enforced required-check gate on the merges).

## References

- Open-PR snapshot at session start: #779/#784/#789/#792/#793/#807/#798 (all merged)
- Failure logs: `docs-graph-jsonld-freshness` (#807 run), `monorepo-health` /
  `test_simple_audits.py::TestDependabotDefunct`, `lint-and-test` substrate-boundary (#798 run)
- Related closes: `90-docs/adr/2606023200-session-close-ooyake-world-government-atlas.md`,
  `90-docs/adr/2606021730-latent-entity-kotoba-datomic-refactor.md`
