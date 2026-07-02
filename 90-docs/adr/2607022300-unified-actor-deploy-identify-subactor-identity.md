---
id: adr-2607022300-unified-actor-deploy-identify-subactor-identity
title: "ADR-2607022300: unified actor deploy — identify facet (per-actor self-sovereign did:key), sub-actor identity (path did:web + own did:key), central custody"
status: accepted
doc_type: adr
topic: unified-actor-deploy-identify
authoritative: true
last_verified: 2026-07-02
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - e7m-actor-unified-deploy
  - aozora-identify-facet
  - per-actor-self-sovereign-did-key
  - sub-actor-identity-model
  - path-did-web-allowance
  - central-identity-custody
depends_on:
  - 2606231200
  - 2606232100
  - 2606291700
  - 2606292000
  - 2606281500
  - 2605231525
related:
  - 2607010001
  - 2606111400
  - 2606251700
supersedes: []
superseded_by: []
---

# ADR-2607022300: unified actor deploy — identify facet (per-actor self-sovereign did:key), sub-actor identity (path did:web + own did:key), central custody

**Status**: accepted
**Date**: 2026-07-02
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1; owner directives 2026-07-02: "cli をベースして、特別な操作を不要に" / "sub actor も id を持つように. コレは kotoba-lang/did で did 公式に合わせて. path did を許容")
**Merged**: root PR #2842 (identify facet auth flow) + this ADR's PR; live-proven against pds.aozora.app 2026-07-02

## Context

- `e7m actor {mesh,publish,pin,reside,identify,deploy --all}` was unified in code
  (`etzhayyim.cli` / `etzhayyim.actor-deploy` / `etzhayyim.aozora-deploy`) citing
  this ADR id before the ADR existed. This document is the missing decision
  record.
- The **identify facet** is live: the central CLI (`bb aozora:deploy <name>
  --apply` / `e7m actor identify <name> --apply`) loads or first-run-generates
  the actor's OWN self-sovereign Ed25519 did:key (`etzhayyim.aozora-identity`),
  mints a CACAO, exchanges it at `com.atproto.server.createSession` for a
  session JWT, then `createRecord`s the profile (Bearer JWT, repo = did:key;
  the PDS enforces session DID == repo DID). Proven live 2026-07-02
  (tashikame / kouhou; root PR #2842, actor PRs #3 each).
- Audit 2026-07-02: 175 published actor repos, **2 deployed**. RAD ledger: 320
  identity journals, 316 still pointing `:rad/aozora-pds` at the legacy
  `https://pds.etzhayyim.com`; the live write endpoint is
  `https://pds.aozora.app` (aozora.app is the AppView; no /xrpc).
- **Sub-actor collision**: ADR-2606292000 shipped 148 toritsugi per-regime
  children as *keyless* mirrors (`verificationMethod: []`, shared placeholder
  genesis RID) and ADR-2606232100 said "no key minting". But app-aozora-pds
  auth requires the repo's OWN did:key to open a session — a keyless child
  cannot own an aozora repo. Cells (`cells/*.edn`) are NOT identities (internal
  compute units; no did, no collection, no RAD entry) and are out of scope.

## Decision

1. **Identify facet (ratifies the shipped behavior).** Every actor addressed by
   the central CLI gets a self-sovereign Ed25519 **did:key** on first `--apply`:
   the aozora repo identity. This *supersedes the "no key minting" language* of
   ADR-2606232100 / ADR-2606292000 **for agent actors only**: the no-server-key
   principle (ADR-2605231525) is fully preserved — the key is generated and held
   OFF-platform in the operator's checkout, never by a Worker/pod/CI; writes
   remain autonomous speech under ADR-2606281500 with the revocable member CACAO
   leash as the off-switch (ADR-2606111400).

2. **Sub-actors get real identities** (owner directive). A fan-out child (e.g.
   `toritsugi-<regime>`) is a first-class actor: its own **did:key** (aozora
   repo) + its own **path did:web** (public handle) + its own RAD identity
   journal (already present). One profile record per child DID, `rkey=self`,
   idempotent; children keep the parent's shared collection
   (`com.etzhayyim.apps.toritsugi`) with `parent`/`regime` fields in the profile
   so consumers can walk the topology.

3. **DID handling aligns to the official W3C DID Core / did:web method via
   `kotoba-lang/did`** (`did.core` — now a root `bb.edn` dep). **Path did:web is
   explicitly allowed**: `did:web:etzhayyim.com:actor:toritsugi-jp-national`
   parses with `did.core/parse`, and `did.core/did-web-url` resolves it to
   `https://etzhayyim.com/actor/toritsugi-jp-national/did.json` per the did:web
   spec. The deploy tool validates every public handle with `did.core/did?`
   before writing.

4. **RAD-journal-driven deploy.** For actors WITHOUT a manifest (all fan-out
   children + fleet/junbi/sng/tsumugu until manifested), the deploy source of
   truth is the RAD identity journal
   (`80-data/kotoba-rad/<name>.identity.journal.edn`): `:rad/name`,
   `:rad/did-web`, `:rad/aozora-collection`, `:rad/parent`, `:rad/regime`.
   Manifest wins when both exist.

5. **Central identity custody.** First-run identities persist to
   **`.e7m/identity/<name>.edn`** under etzhayyim/root (ONE gitignored dir),
   NOT into each actor repo: per-repo dot-dirs have unverified .gitignore
   coverage across 175 repos, and sub-actors have no repos at all (their
   `:rad/repo` values are aspirational). Existing per-repo identities
   (tashikame/kouhou `.{name}/identity.edn`) stay honored (resolution order:
   `AOZORA_IDENTITY` env → existing per-repo file → existing 20-actors file →
   central). Custody hardening (Keychain/1Password, no-server-key §mechanics)
   is a follow-up; the private key material NEVER enters git.

6. **Ledger correction.** Append (never rewrite — journals are append-only)
   `:rad/aozora-pds "https://pds.aozora.app"` facts to the 316 stale journals,
   and `:rad/did-key <public did:key>` facts for every identified actor and
   sub-actor, at the journal's next seq. Public leg only.

## Consequences

- 175 published actors + 148 sub-actors become identifiable/deployable with
  ZERO special per-actor operation: `bb aozora:deploy <name> --apply`.
- The toritsugi children's shared placeholder genesis RID
  (`bafyreiplaceholder…`) remains — minting real per-child genesis blocks
  (kotoba-rad RID, ADR-2606231200) is follow-up work; `:rad/did-key` gives them
  a real cryptographic identity in the meantime.
- Namespace divergence noted, NOT resolved here: RAD collections are
  `com.etzhayyim.apps.<name>` while manifests/contracts declare
  `com.etzhayyim.<name>.*` lexicons, and the synthesized `.profile` type has no
  materialized lexicon schema. Reconciliation is a separate ADR.
- `did:web` documents for path DIDs (`https://etzhayyim.com/actor/<name>/did.json`)
  should eventually publish the actor's did:key in `verificationMethod`
  (did:web ↔ did:key linkage) — follow-up, tracked with the did-web worker.
- Deploy state stays implicit (ADR-2606291700): the profile record on the PDS
  is the registry; the read path (getRecord/listRecords) is live as of
  2026-07-02 (app-aozora PR #38).
