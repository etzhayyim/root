---
id: adr-2606082500-kaizen-github-independent-self-evolution-kotoba-git
title: "ADR-2606082500: GitHub-independent Kaizen self-evolution via kotoba git-protocol (GitRemote abstraction + live fleet)"
status: accepted
doc_type: adr
topic: kaizen-github-independent-self-evolution
authoritative: true
last_verified: 2026-06-08
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "Removes GitHub as a hard dependency of the self-evolution loop: the Kaizen actuator now publishes its patch branch either to GitHub (default, back-compat) or — GitHub-independently — into kotoba's content-addressed Datom log over the kotoba server's git smart-HTTP receive-pack endpoint. Proven end-to-end (real git push + clone-back byte-exact + kotoba approval → fitness update). Also fixes the live pr-agent crash-loop so the loop actually runs."
authoritative_for:
  - Kaizen GitRemote abstraction (GithubRemote / KotobaRemote / select_remote)
  - KAIZEN_GIT_REMOTE env switch + KotobaRemote env contract
  - kotoba-git fleet deployment (git smart-HTTP push target)
  - kaizen-pr-agent fleet resource/clone crash-fix
depends_on:
  - adr-2605240200-unispsc-organism-kaizen-self-reflection
  - adr-2605266200-kaizen-pr-agent-wave-4
related:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605231525-etzhayyim-no-server-key-invariant
supersedes: []
superseded_by: []
---

# ADR-2606082500: GitHub-independent Kaizen self-evolution via kotoba git-protocol

**Status**: accepted
**Date**: 2026-06-08
**Deciders**: Jun Kawasaki

# Context

The Kaizen self-evolution loop (ADR-2605240200) is a two-process organism:

- **`KaizenObserver`** probes the fleet (shard healthz + post queues + classification
  stream), runs rules, and appends `KaizenProposal` NDJSON records to a shared queue.
- **`KaizenPrAgent`** (the *actuator*) drains the queue, applies each proposal's patch on
  a fresh branch, commits, and **opens a change for review**. Wave-4 (ADR-2605266200)
  enabled it to open *real* PRs/issues.

Until now the actuator's only publish target was **GitHub** (`gh pr create`). That made
GitHub a hard dependency of the religious-corp's self-evolution: the loop could not evolve
itself without github.com, GHCR, and a `GH_TOKEN`. This sits awkwardly with the substrate
boundary — kotoba's Datom log is the first-class canonical state (ADR-2605312345), and the
project's direction is to route around centralized dependencies.

kotoba already implements the git wire protocol: `kotoba-git` stores every git object as a
content-addressed `KotobaCid` block + `:git/*` Datom projection, and `kotoba-server`
exposes git **smart-HTTP** at `GET /git/:repo/info/refs`, `POST /git/:repo/git-upload-pack`,
and `POST /git/:repo/git-receive-pack` (push) — the push lands objects as blocks + Datoms,
then `git_persist` snapshots the oid↔cid index. The push gate accepts an operator Bearer
JWT, a CACAO `git.receive/push` capability, or `KOTOBA_GIT_ALLOW_ANON_PUSH=1`.

So the substrate to self-evolve **without GitHub** already exists. What was missing was (a)
an actuator that can target it, and (b) it actually running on the fleet.

# Decision

## 1. Pluggable `GitRemote` in the Kaizen actuator

Introduce `kotodama/organism/kaizen/git_remote.py` — a `GitRemote` protocol with two
implementations, selected by `KAIZEN_GIT_REMOTE` (default `github`):

- **`GithubRemote`** (default, back-compat): `gh auth setup-git` → `git push` →
  `gh pr create --head`; change-state via `gh pr view --json state`.
- **`KotobaRemote`** (`KAIZEN_GIT_REMOTE=kotoba`): a **real `git push`** to
  `<KAIZEN_KOTOBA_GIT_URL>/git/<repo> refs/heads/<b>:refs/heads/<b>` →
  `POST /git/<repo>/git-receive-pack`. No GitHub / GHCR. Auth via operator Bearer JWT
  (`KAIZEN_KOTOBA_GIT_TOKEN` — operator-injected via `-c http.extraHeader`, never written
  to disk or the URL) or anon (`KAIZEN_KOTOBA_GIT_ANON=1`) when the node sets
  `KOTOBA_GIT_ALLOW_ANON_PUSH=1`.

`KaizenPrAgent.__init__` takes a `remote` (default `GithubRemote`); `gh auth` is only
verified for the GitHub remote. `consume_one` delegates the publish to
`remote.open_change(...)`. `kaizen_pr_agent_main` resolves the remote via `select_remote()`
and delegates outcome resolution to `remote.change_state(...)`.

## 2. kotoba approval → fitness signal

`KotobaRemote.change_state` maps a kotoba ref's operator/Council approval
(`KAIZEN_KOTOBA_APPROVED_REFS` / `KAIZEN_KOTOBA_REJECTED_REFS`, normalized so a bare branch
or a full `kotoba:<repo>/refs/heads/<b>` ref both match) to the same `merged`/`closed`/`open`
states the MetaReflector fitness ledger already consumes for GitHub PRs. The self-scoring +
rule-pruning loop is therefore substrate-agnostic.

## 3. Live operation

- **Fleet crash-fix (the loop *actually runs*)**: the `kaizen-pr-agent` Deployment
  crash-looped on the live fleet — `git clone --depth 50` of the monorepo overflowed the 1Gi
  `repo-checkout` emptyDir (yoro static-asset churn; HEAD tracked-files are only ~54 MiB) →
  *Evicted*, and a 512Mi memory limit → *OOMKilled (137)*. Fixed to
  `git clone --depth 1 --single-branch --no-tags`, repo-checkout 2Gi, memory 2Gi.
- **kotoba-git fleet endpoint**: a `kotoba serve` Deployment + Service
  (`kotoba-git.etzhayyim-organism.svc:8080`, anon push, `KOTOBA_IPFS=off`) is the
  GitHub-independent push target. Requires a kotoba image built from `origin/main`
  (the git_http endpoints postdate the monorepo's stale kotoba submodule pin).

# Consequences

- The self-evolution loop is no longer GitHub-bound: one env switch
  (`KAIZEN_GIT_REMOTE=kotoba` + `KAIZEN_KOTOBA_GIT_URL`) makes it publish into the
  content-addressed Datom log instead. Default stays GitHub (no behavior change for
  existing deployments).
- **No-server-key (ADR-2605231525) preserved**: the kotoba push uses an operator-injected
  short-lived token (or anon for cluster-internal), never a platform-held key — same model
  as `GH_TOKEN`.
- The actuator stays alive on the fleet (0-restart) after the resource/clone fix.
- **Open follow-ups**: (a) the monorepo's kotoba **submodule pin is ~30 commits behind
  `origin/main`** — the published images predate git_http, so a kotoba image must be built
  from `origin/main` to serve `/git`; (b) `kaizen-slim` must be rebuilt from current main to
  ship `git_remote.py` before the live pr-agent can use `KotobaRemote`; (c) the UNSPSC fleet
  shards are down (`reachable=0/3`), so the observer currently only raises infra-outage
  proposals (not code-patchable).

# Verification

- Unit: 9 `git_remote` tests + 48 kaizen tests green (incl. ref↔branch normalization).
- **Live end-to-end (GitHub-independent)**: the real `KaizenPrAgent` consumed a real
  proposal, patched (`CACHE_SIZE 128→256`), committed, and `git push`ed into a live
  `kotoba serve` → cloned back byte-exact (commit `912ae07`); marking the kotoba ref approved
  raised `lru-saturation` fitness 0.5 → 0.667 in the MetaReflector ledger.
- kotoba-git wire suite 13/13 + `real_git_repo` 2/2 green.
- Live fleet: `kaizen-observer` + `kaizen-pr-agent` both Running (pr-agent 0-restart after
  the fix); `kotoba-git` 1/1 Running.

# Alternatives Considered

- **Add a `kotoba git import` CLI wrapping `GitStore.import_repo`** — rejected: the server's
  smart-HTTP `git-receive-pack` is the genuine, already-implemented, durable push surface
  (objects → blocks + Datoms + persisted index). A standalone in-process CLI would not
  persist the Datom projection and would duplicate the wire layer.
- **Keep GitHub-only** — rejected: makes self-evolution depend on a centralized service,
  contrary to the substrate boundary and the recurring directive to evolve without GitHub.
- **Server-signed pushes** — rejected: violates the no-server-key invariant
  (ADR-2605231525); credentials must be operator-injected.

# References

- ADR-2605240200 — KaizenObserverCell + PR-agent contract (parent)
- ADR-2605266200 — kaizen-pr-agent Wave-4 (real PR/issue enablement)
- ADR-2605262130 — kotoba storage substrate unification
- ADR-2605312345 — kotoba Datom log = first-class canonical state
- ADR-2605231525 — no-server-key invariant
- kotoba PR #73 (`7644076c`) — GitRemote abstraction + KotobaRemote (merged)
- root PR #1472 — fleet pr-agent crash-fix
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/kaizen/git_remote.py`
- `40-engine/kotoba/crates/kotoba-server/src/git_http.rs` (`/git/:repo/git-receive-pack`)
- `50-infra/k8s/unispsc-organism-fleet/kaizen-pr-agent/deployment.yaml`
