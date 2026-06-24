---
id: adr-2606241500-sops-age-kotoba-rad-actor-git-evolution
title: "ADR-2606241500: sops/age secrets + kotoba-rad — actor self-evolution of code AND data via git"
status: accepted
doc_type: adr
topic: actor-git-evolution
authoritative: true
last_verified: 2026-06-24
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "C-axis (self-evolution): an actor evolves code + data + secrets through ordinary git, anchored to its kotoba-rad sovereign identity."
authoritative_for:
  - actor-git-evolution
  - sops-age-secrets
depends_on:
  - adr-2606231200  # kotoba-rad — sovereign per-actor repo identity (A/B axes)
  - adr-2605231525  # no-server-key / member-held keys
  - adr-2605312345  # kotoba Datom log = first-class canonical state
related: []
supersedes: []
superseded_by: []
---

# ADR-2606241500: sops/age secrets + kotoba-rad — actor self-evolution of code AND data via git

**Status**: accepted
**Date**: 2026-06-24
**Deciders**: Jun Kawasaki

# Context

ADR-2606231200 (kotoba-rad) gave each actor a **sovereign identity** — an RID
(genesis-block CIDv1) + `did:key`, signed on an append-only kotoba Datom journal
(`80-data/kotoba-rad/<name>.identity.journal.edn`), the member's Ed25519 key in
macOS Keychain — and a **code-distribution** path (josh-proxy / `git subtree`
mirror to `com-etzhayyim-<name>`). That covers the A-axis (code) and B-axis
(identity).

What was still missing is the **C-axis = self-evolution**: an actor evolving
*both* its **code** (`20-actors/<name>/**`) *and* its **data** (`80-data/<name>/**`
+ its identity journal) through ordinary git — `add / commit / branch / push / PR
create / merge` — the same operations the question asked for. Two gaps blocked it:

1. **Secrets in git.** Actors hold operational credentials (API keys, B2 auth,
   OAuth tokens). The repo rule is "never commit secrets" and today they live in
   Keychain + 1Password and are piped via env at runtime. To let an actor's
   *data* travel in git, secrets must be carryable **as ciphertext** so a
   credential is never committed in the clear — and decryptable with **only
   GitHub (for the ciphertext) + Apple Keychain (for the key)**, no cloud KMS.
2. **A git lifecycle bound to the sovereign identity.** Each code/data step
   should be witnessed by the same content-addressed, signed identity that names
   the actor, so the evolution history is tamper-evident and attributable.

The substrate already pointed at this answer: kotoba's blocks are content-addressed
(CIDv1) with IPFS/B2 as *export tiers, not the system of record*, and `kotoba init`
already persists keys to macOS Keychain. So "store data in git, key in Keychain,
decrypt locally" is the established grain of the system, not a new dependency.

# Decision

Add a **secrets layer (sops + age)** and a **git-evolution orchestrator**, both
clj/bb over the kotoba Datom log, integrated with kotoba-rad. No new runtime
service; no cloud KMS; nothing platform-held.

## 1. Secrets = sops + age, key in macOS Keychain (`etzhayyim.sops-age`)

- Each actor has an **age identity**. Its **secret key** lives in macOS Keychain
  under service `etzhayyim.sops-age`, account `<actor>` — one service over from
  kotoba-rad's signing key (`etzhayyim.kotoba-rad`). **Two distinct keys** (sign
  vs encrypt) by hygiene; **both member-held, never platform-held** (no-server-key,
  ADR-2605231525). An org-wide **recovery recipient** (`__org__`) is also added so
  the org can always decrypt (sops multi-recipient — any one key suffices).
- Only **ciphertext** is committed: plaintext `20-actors/<name>/secrets/*.{env,
  yaml,json,edn}` is **git-ignored**; sops produces `*.enc.*` siblings that ARE
  committed. For structured types the keys stay visible and only values are
  encrypted (`ENC[...]`); other types are encrypted whole (binary → sops JSON).
- The actor's **age recipient (public key)** is recorded as a datom on its
  kotoba-rad identity journal — `[<RID> :rad/age-recipient age1… tx :add]` — so
  the **sovereign identity declares who can decrypt its secrets**. `.sops.yaml`
  is **generated from those journals** (the SoT), so the human `sops` workflow
  and the sovereign identity never drift.

## 2. `bb actor:evolve <name>` — the code+data git lifecycle

DRY-RUN by default. `--apply` permits local mutation; the outward legs are
separately gated (`--push` → `--pr` → `--merge`, each needing the previous).
Steps:

```
0. bind   record :rad/age-recipient onto the identity log (if a Keychain key
          exists and the journal doesn't yet declare it)
1. secrets  sops-encrypt every plaintext secret → *.enc.* ; regenerate .sops.yaml
2. branch   git checkout -B evolve/<actor>/<slug>
3. stage    git add -- 20-actors/<name>  80-data/<name>  <identity-journal>  .sops.yaml
4. attest   append [:rad/evolution "<branch>|<slug>"] + re-sign the data-log head
            (sigref) with the member key → code+data step witnessed by the RID
5. commit   git commit  (commit body carries  rad:<RID>)
6. push/PR/merge   member gh+git creds (no-server-key); each leg gated
```

Signing uses kotoba-rad's existing `:sign-fn` seam: if the member's key is in
Keychain the evolution head is **signed**, else it is published **unsigned + warn**
(pilot/`--no-network` degenerate case), exactly as `publish-identity!`.

## 3. Why GitHub + Keychain is sufficient (the question's two asks)

- **"Store data on GitHub and query by CID?"** kotoba's blocks are already CIDv1
  content-addressed with IPFS/B2 as *export tiers*. Committing CARs/ciphertext to
  a repo (served, if desired, over GitHub Pages) is a valid read/query/export
  tier — Pages becomes a static CID gateway. This ADR lands the **git transport
  + secrets** half; a `GitHubPagesBlockStore` read tier (CAR + Range) is a
  follow-up, not required for code+data git evolution.
- **"Encrypt secrets with sops + GitHub + Apple Keychain only?"** Yes — age key
  in Keychain, ciphertext in GitHub, no KMS. `age-plugin-se` (Secure-Enclave /
  Touch-ID, non-exportable) is the recommended hardening and drops in
  transparently (sops age-plugin support); multi-device = add each recipient and
  `sops updatekeys`.

## Files

- `70-tools/src/etzhayyim/sops_age.cljc` — keygen / recipient / encrypt / decrypt
  (Keychain-sourced), `:rad/age-recipient` binding, `.sops.yaml` generation.
- `70-tools/src/etzhayyim/actor_evolve.cljc` — `bb actor:evolve` orchestrator.
- `70-tools/src/etzhayyim/test_sops_age.cljc` — hermetic invariants (no Keychain).
- `.sops.yaml` (generated), `.gitignore` (plaintext secrets), `bb.edn` tasks
  `actor:evolve` / `sops:keygen` / `sops:yaml` / `sops:encrypt` / `sops:decrypt`
  / `test:sops-age`.

# Consequences

**正**
- An actor evolves code + data + secrets through one familiar git flow; every
  step is witnessed by its content-addressed, signed sovereign identity.
- Secrets become **versioned and committable** without leaking — removes the
  1Password runtime dependency for repo-resident secrets (e.g. the B2 auth the
  kotoba-b2-pin tier pulls from 1Password can move to a sops `*.enc.*` file).
- Zero new services / no cloud KMS; recovery via the org recipient; reuses the
  Keychain custody and `:sign-fn` seam already shipped for kotoba-rad.

**負 / リスク**
- macOS Keychain is per-machine: multi-device/team needs per-device age
  recipients (`sops updatekeys`) — the cost of no-shared-secret crypto.
- Plaintext secrets are git-ignored, not blocked at write time; the guard is the
  ignore rule + the `*.enc.*` convention + review. A pre-commit hook scanning for
  AGE/PEM/`AKIA`-shaped plaintext under `secrets/` is a follow-up.
- `actor:evolve` shells `git`/`gh`; the merge leg is gated and never auto-runs
  without `--merge` (and the repo's `closing` discipline).

# Alternatives Considered

- **DataLad/git-annex for secrets** — already used for *large binary* cold-pin to
  B2 (ADR-2605241500); wrong tool for small text credentials (annex overhead, no
  value-level encryption). Kept for big data, not secrets.
- **git-crypt / blackbox** — git-crypt encrypts whole files (no visible keys, no
  multi-recipient ergonomics); blackbox is GPG-centric. sops+age gives
  structured value-level encryption + clean multi-recipient + age/Keychain fit.
- **Cloud KMS (AWS/GCP/Vault) via sops** — violates the no-cloud-dependence grain
  and adds lock-in (scored negative by the ECL objective function); age+Keychain
  is self-hosted and member-held.
- **A new mutable-state DB (Automerge/dolt/Zed)** — the kotoba Datom log already
  is the canonical append-only state (ADR-2605312345); git carries the materialized
  EDN + ciphertext. No second ledger.

# References

- ADR-2606231200 (kotoba-rad — sovereign per-actor repo identity)
- ADR-2605231525 (no-server-key / member-held signing)
- ADR-2605312345 (kotoba Datom log = first-class canonical state)
- ADR-2605241500 (DataLad + git-annex + IPFS dataset substrate — big-binary tier)
- `70-tools/src/etzhayyim/{sops_age,actor_evolve}.cljc`
- sops <https://github.com/getsops/sops> · age <https://github.com/FiloSottile/age>
