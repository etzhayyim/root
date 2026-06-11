---
id: adr-2605212200-yorishiro-session-closure
title: "ADR-2605212200: yorishiro session closure (2026-05-21) — 19 commits, 16 yorishiri, all ADR-2605211900 phases delivered"
status: active
doc_type: explanation
topic: yorishiro-session-closure
authoritative: true
last_verified: 2026-05-21
priority: 5.0
axis: governance
weight: 0.50
priority_note: "Closing index for the 2026-05-21 yorishiro implementation arc on branch 260521-yorishiro-phase1 / PR #256. Captures what landed, what didn't, and where the work resumes. Companion to ADR-2605211900 (the umbrella spec) and ADR-2605212100 (the Stripe removal compliance pin)."
authoritative_for:
  - 260521-yorishiro-phase1 branch closure narrative
  - PR #256 contents map
related:
  - adr-2605211900-etzhayyim-yorishiro-external-actor-bridge
  - adr-2605212100-stripe-removed-from-religious-corp-canonical
  - runbook-2605212130-yorishiro-cell-runner-deploy
  - 50-infra/cluster/murakumo/cell-runner/cells.toml
supersedes: []
superseded_by: []
---

# ADR-2605212200: yorishiro session closure (2026-05-21)

**Status**: active
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

# Context

A single-day session executed ADR-2605211900 (yorishiro external-actor
bridge) end to end on branch `260521-yorishiro-phase1`. The work was
paced via a session-only cron `*/30 * * * *` (job `18fdf216`,
`/loop 残りをすべて進めて`) which re-entered every 30 minutes until the
roadmap closed. This ADR is the closing index — what each commit
delivered, what the survey ended at, and what remains as
operator-driven follow-up.

# Decision

Treat the 260521-yorishiro-phase1 branch as the **complete delivery
of ADR-2605211900 Phases 1, 2, 2.5, 2.5.1, 2.5.2, 2.5.2.1, 2.5.3,
2.5.3.1, 2.5.4, 2.5.4.1, 3, 4, 5**. No additional yorishiro work is
planned on this branch — further refinements (cobra subcommand-level
flag scoping, clap derive `flatten`, browser-only auth, MCP package
publishing) ship as their own PRs.

## 19 yorishiro commits

| Commit | Phase | Delivery |
|---|---|---|
| `6fb2404e` | 1 | ADR-2605211900 + generator skeleton + arxiv reference |
| `9e6cb375` | 1+ | operationalization (pnpm-workspace, cells.toml fragment, Claude Desktop config) |
| `8ff33790` | 1 | huggingface / openalex / crossref + generator bug fixes |
| `b77a68e1` | 2 | binary-cli mode + pdftotext (live-verified on real PDF) |
| `d5829b51` | 5 | CI audit gate workflow + regen idempotency (generatedAt preserve) |
| `bdc0dab5` | 2+ | cell-runner auto-discovery + xrpc trigger + __init__.py |
| `1c5640a7` | 3 | browser-only L1 + example-portal |
| `81545a9d` | 3 | browser-only L2/L3 Playwright driver |
| `4bb06d34` | 2.5 | source-repo mode (Click AST walker) |
| `a53233d0` | 4 | migration survey + bls reference |
| `3972dfbd` | 1+2.5.1 | HF-inference / fueleconomy / argparse walker (Phase 2.5.1) |
| `8f61943a` | 4 | recruit-ingest-bls callsite alignment |
| `ba2096a6` | 4+2.5.2 | EPA + HF inference docstring alignment + argparse subparsers |
| `9c5d8691` | 2.5.2.1+2.5.3+2.5.4 | argparse multi-parser + cobra + clap walkers |
| `beec1f9a` | 4 closure | Stripe removal (ADR-2605212100) + deploy runbook |
| `39d7a870` | 2.5.3.1+2.5.4.1 | cobra Args expansion + clap derive walker |
| `57361884` | 1 hardening | handle.ts headers option + POST body partition + mst-projector HF live migration |

## 16 shipped yorishiri

| Name | Kami | Mode |
|---|---|---|
| arxiv | arxiv.org | openapi-v3 |
| bls | api.bls.gov | openapi-v3 |
| crossref | api.crossref.org | openapi-v3 |
| fueleconomy | www.fueleconomy.gov | openapi-v3 |
| huggingface | huggingface.co | openapi-v3 |
| huggingface-inference | api-inference.huggingface.co | openapi-v3 |
| openalex | api.openalex.org | openapi-v3 |
| pdftotext | bin:pdftotext | binary-cli |
| demo-fixture | bin:demo-fixture | source-repo (Click) |
| argparse-demo | bin:argparse-demo | source-repo (argparse) |
| argparse-sub | bin:argparse-sub | source-repo (argparse subparsers) |
| argparse-multi | bin:argparse-multi | source-repo (argparse multi-parser) |
| cobra-demo | bin:cobra-demo | source-repo (cobra) |
| clap-demo | bin:clap-demo | source-repo (clap builder) |
| clap-derive-demo | bin:clap-derive-demo | source-repo (clap derive) |
| example-portal | browser:example-portal | browser-only |

## Survey state at branch tip

| Bucket | Count |
|---|---|
| matched | 3 (BLS / EPA docstring-aligned; HF inference **live-migrated**) |
| unmatched | 0 |
| violation | 0 (Stripe removed per ADR-2605212100) |
| substrate | 26 |
| noise | 7 |

`yorishiro audit` + `no-external-purchase-purpose` lefthook hook +
regen idempotency: clean across all 16 yorishiri.

## Adjacent work that landed on the same branch (NOT yorishiro)

The session also accreted three sibling initiatives that share the
"vendor centralized / etzhayyim decentralized substrate axis" framing
(ADR-2605211950):

- ADR-2605211950 + 2afcd934 — murakumo `fleet.toml` IP baseline
- 8dcf8c85 + aec6c9fd + e172fae2 + ea64238d + 59614a2a — etzhayyim-authz
  (Phase α P1, viem chain integration, Council Safe SOP, XRPC adapter)
- 620ddcb2 — etzhayyim-did-web per-actor DID Document resolution
- e4d9e7f3 — etzhayyim-k2 KarmaAnchor + CohortLifecycle (Phase β P0)
- LangserverHealthMonitoringCell registration in
  `50-infra/cluster/murakumo/cell-runner/cells.toml` (cron */5)

These are tracked in their own ADRs and not in scope for this
closure ADR — they are listed only so a reviewer of PR #256 isn't
surprised by their presence.

# Consequences

## Positive

- Every input mode in ADR-2605211900 D4 has a working reference impl
  + at least one shipped yorishiro
- CI gate (`.github/workflows/yorishiro-audit.yml`) enforces Charter
  compliance + regen idempotency on every push/PR touching the
  yorishiro tree
- Cell-runner discovers yorishiri zero-config (drop the generator
  output, restart launchd, healthz lists them)
- One concrete live callsite migration (mst-projector HF inference)
  proves the end-to-end consumer path
- The migration survey is a permanent fixture — re-running it
  catches new direct fetches before they land

## Negative / Carried forward

- Two callsite migrations remain docstring-only (BLS, EPA) because
  they are standalone scripts without a workspace context to resolve
  `@etzhayyim/yorishiro-*-mcp` packages. The canonical resolution is
  to move them in-cluster via the cell-runner's xrpc trigger, which
  is gated on Murakumo deploy
- Murakumo runtime deploy is operator-driven; the runbook is at
  `90-docs/runbooks/2605212130`. No yorishiro is actually running on
  a Murakumo node yet — only `yorishiro_arxiv` (Phase 1 sample) is
  declared in the religious-corp cell-runner config; the rest live
  in their fragment files and will pick up at next restart
- cobra subcommand-level flag scoping degrades for commands defined
  in different files (the regex scope is per-file). Multi-file cobra
  apps are best wrapped with a hand-authored kami manifest
- clap derive `#[command(flatten)]` and `Args` trait are not handled
- MCP packages are workspace-only (`workspace:*`). Publishing to
  npm under the `@etzhayyim` scope is deferred

# Cron + loop closure

The session-only cron `18fdf216` is cancelled with this commit. The
loop's job was to re-enter `/loop 残りをすべて進めて` every 30 min until
the user explicitly closed the session — this ADR is that closure.

# References

- ADR-2605211900 (umbrella spec)
- ADR-2605212100 (Stripe removal)
- `90-docs/runbooks/2605212130-yorishiro-cell-runner-deploy.md`
- PR https://github.com/etzhayyim/root/pull/256
- `70-tools/etzhayyim-cli/yorishiro/` (the generator)
- `70-tools/scripts/yorishiro/survey.mjs` (Phase 4 audit tool)
