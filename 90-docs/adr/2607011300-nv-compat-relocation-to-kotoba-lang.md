---
id: adr-2607011300-nv-compat-relocation-to-kotoba-lang
title: "ADR-2607011300: nv-compat relocation from etzhayyim-sdk to kotoba-lang/kami-nv-compat"
status: accepted
doc_type: adr
topic: nv-compat-relocation
authoritative: true
last_verified: 2026-07-01
priority: 3.0
axis: architecture
weight: 0.30
priority_note: "Housekeeping/placement ADR, not a design change to the facade itself."
authoritative_for:
  - kami-nv-compat repo location
depends_on:
  - adr-2605261800-nvidia-omniverse-stack-api-compat
related:
  - adr-2606011500-kami-engine-reusable-vs-repo-specific-separation-plan
supersedes: []
superseded_by: []
---

# ADR-2607011300: nv-compat relocation from etzhayyim-sdk to kotoba-lang/kami-nv-compat

**Status**: accepted
**Date**: 2026-07-01
**Deciders**: Jun Kawasaki

# Context

`20-actors/etzhayyim-sdk/src/nv-compat/` (ADR-2605261800) is the TypeScript +
WGSL API-compat facade for NVIDIA Omniverse / Isaac Sim / Isaac Lab / OptiX /
RTX Renderer / Replicator / DriveSim / Omniverse Cloud / Nucleus / Alpamayo,
backed by KAMI-native canonical engines. It carries no etzhayyim-specific
business logic — no religious-corp identity, no CACAO auth, no charter
governance flow. It is generic robotics/rendering/simulation tech: WGSL
compute kernels, Featherstone articulated dynamics, a USD reader, a
Replicator-style domain-randomization sampler, drive-sim sensor models, an
extension-loader app shell, and a content-addressed store client.

The superproject's org taxonomy (ADR-2606302300, `manifest/repos.edn`)
partitions repos along "what kind of thing": `kotoba-lang` is the
language/substrate home consumed by all orgs (already hosting the sibling
`kami-engine` Rust workspace this facade's own README points to as the
longer-term backend — `kami-genesis`, `kami-articulated`, `kami-rt`,
`kami-usd`, etc.); `etzhayyim` is for agent-centric, public-interest actors.
The taxonomy's stated placement rule is explicit: "any library/substrate ...
→ kotoba-lang". `kami-engine` and `kami-engine-sdk` already made this move
(ADR-2606011500); nv-compat had not.

A grep across the whole `etzhayyim/root` monorepo found zero code-level
consumers of `20-actors/etzhayyim-sdk/src/nv-compat/` outside the facade's
own `test/` and `examples/` — it was never wired into `@etzhayyim/sdk`'s
public `package.json` exports map, nor imported by any actor
(wadachi/suki/sarutahiko/etc. still reference it only in ADR prose as a
future consumer). Relocating it now, before real consumers exist, is the
cheapest time to do it.

# Decision

Physically relocate `20-actors/etzhayyim-sdk/src/nv-compat/` (39 test files /
486 tests, 15 example HTML demos + README, ~15K lines of source) to a new
standalone repo **`kotoba-lang/kami-nv-compat`**, as-is (TypeScript + WGSL,
git history not preserved — see Alternatives Considered).

- New repo layout flattens the old `src/nv-compat/*` up to its own `src/*`
  root (so `omni-usd.ts`, `isaac-sim.ts`, `kami-rt/`, `dynamics/`, `warp/`,
  etc. become top-level); `test/` and `examples/` follow the same flattening,
  with internal relative imports (`../src/nv-compat/X` → `../src/X`)
  rewritten accordingly.
- npm package name kept in the `@etzhayyim/` scope
  (`@etzhayyim/kami-nv-compat`) per the `@etzhayyim/kami-engine-sdk`
  precedent — npm publish scope is a separate concern from which GitHub org
  hosts the source.
- License carried over unchanged: Apache 2.0 + Charter Compliance Rider v3.6
  (`LICENSE` / `CHARTER-RIDER.md` / `NOTICE` copied verbatim from
  etzhayyim/root's canonical copies), matching the `kami-engine` /
  `kami-engine-sdk` / `kotoba` precedent of kotoba-lang repos still carrying
  the Rider despite living outside the `etzhayyim` GitHub org — the Rider is
  a licensing condition Jun Kawasaki attaches to the code, independent of
  which org hosts it.
- `CHARTER-RIDER.md` §7.1's trademark-facade-namespace pointer updated (both
  in this repo and in the new repo's copy) from
  `20-actors/etzhayyim-sdk/src/nv-compat/` to `kotoba-lang/kami-nv-compat`.
- Registered in `manifest/repos.edn` (`:extra-projects`, `kotoba-lang`
  remote) + `manifest/west.yml` regenerated or the superproject.
- `etzhayyim-sdk` gets no new dependency: since nothing in the monorepo
  imported nv-compat via `@etzhayyim/sdk`'s own exports, there was nothing to
  rewire to point at the new package. `git rm -r src/nv-compat test/
  examples` is the entire etzhayyim-sdk-side diff (plus the CHARTER-RIDER.md
  pointer). `npm run typecheck` / `npm test` both stay green (143 tests,
  down from including nv-compat's now-relocated 486).
- ADR-2605261800 is **not** rewritten: its D1-D12 decisions (canonical KAMI
  names, trademark boundary, phase plan, Genesis backend choice, etc.) still
  govern the facade's design wherever it lives. Only this ADR's own
  `authoritative_for` path list and the two CHARTER-RIDER.md path references
  needed updating; ADR-2605261800's own body is left as the historical record
  of what was decided and where it was first built.

# Consequences

- `kami-nv-compat` becomes independently versioned and installable by any
  future consumer (a robotics actor, a different org's app) without pulling
  in the rest of `@etzhayyim/sdk` (AT Protocol / IPFS / Base L2 / payments —
  none of which nv-compat needs).
- Git history for the facade was not preserved: the local `etzhayyim/root`
  checkout is a shallow clone (`clone-depth: 1`) that only exposed a single
  commit of history for this path, so `git subtree split` / `git
  filter-repo` would have needed a full unshallow fetch of the whole
  170+-actor monorepo for a facade whose real development history (the D12
  amendment's "iter 71–109" trail) already sits past the shallow boundary.
  The ADR trail (2605261800 + this ADR) is the durable record of *why* and
  *when*; per-line blame is not preserved.
- The eventual Rust `kami-engine` backend swap (ADR-2605261800 §D6/§D7,
  `kami-genesis`/`kami-articulated`/`kami-rt`/`kami-usd` — currently mostly
  path-reservation stubs vs. the TS facade's more complete implementation)
  is now a same-org (`kotoba-lang`) refactor instead of a cross-org one.

# Alternatives Considered

## A1. Preserve git history via `git subtree split` / `git filter-repo`

Rejected for now: the local `etzhayyim/root` clone is shallow
(`clone-depth: 1`), and `git log -- 20-actors/etzhayyim-sdk/src/nv-compat`
showed only 1 commit locally. Unshallowing the whole monorepo just to recover
blame for one facade was judged disproportionate. Running `git filter-repo`
inside a linked worktree was also rejected as unsafe — it rewrites all
refs/objects in the shared `.git`, which would have clobbered other
concurrent agents' worktrees sharing the same object store.

## A2. Port to Rust (`kami-engine`) instead of relocating TypeScript as-is

This is ADR-2605261800's own eventual plan (§D6/§D7) and remains the
longer-term direction. Rejected as the *first* move here: a TS→Rust port of
~15K lines with 486 passing tests is 5-10× the effort of a same-language
relocation (cf. ADR-2605261800 §D10.5's "from-scratch fallback" honesty
framing) and was not what was asked for. Physically relocating first (this
ADR), then porting backend-by-backend into the already-registered
`kotoba-lang/kami-engine` crates later, de-risks the bigger move.

## A3. Leave nv-compat in etzhayyim-sdk, just document the taxonomy exception

Rejected: ADR-2606302300's placement rule is unconditional ("any
library/substrate → kotoba-lang"), nv-compat has zero etzhayyim-specific
coupling (confirmed by the zero-remaining-references grep), and `kami-engine`
/ `kami-engine-sdk` already set the precedent of making this exact move for
adjacent code.

# References

- ADR-2605261800 (NVIDIA Omniverse stack API-compat layer — design authority,
  unchanged by this move)
- ADR-2606011500 (kami-engine reusable-vs-repo-specific separation plan —
  precedent for TS-SDK/Rust-engine relocation to kotoba-lang)
- ADR-2606302300 (org-taxonomy 4-orgs — the library-placement rule this ADR
  executes)
- `kotoba-lang/kami-nv-compat` (new repo, `README.md` for provenance)
