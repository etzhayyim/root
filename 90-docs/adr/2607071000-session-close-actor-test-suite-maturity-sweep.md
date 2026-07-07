---
id: adr-2607071000-session-close-actor-test-suite-maturity-sweep
title: "ADR-2607071000: Session close — actor test-suite maturity sweep (33 PRs): .clj/.cljc shadow-pair cleanup, Foundry CI wiring, and the bb test:actors System/exit landmine fix"
status: accepted
doc_type: adr
topic: session-close-actor-test-suite-maturity-sweep
authoritative: false
last_verified: 2026-07-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "non-authoritative process record; authoritative design = ADR-2606131800 (the py->clj refactor arc + bb test-discovery this session continues) + ADR-2606160842 (py->clj port wave)"
authoritative_for: []
depends_on:
  - adr-2606131800-session-close-python-to-clojure-tier-b-refactor-arc
  - adr-2606160842-kotoba-code-actor-py-to-clj-port-wave
related: []
supersedes: []
superseded_by: []
---

# ADR-2607071000: Session close — actor test-suite maturity sweep

**Status**: accepted (process record — non-authoritative)
**Date**: 2026-07-07
**Deciders**: Jun Kawasaki

## Context

A recurring `/loop` session ("improve maturity — these are set in motion by land / building /
cash / stock donations") ran an extended, self-paced sweep across the repo's test
infrastructure. It directly continues the py→cljc refactor arc closed out in
ADR-2606131800: that session shipped `bb test:actors` (auto-discovery over the ported
Tier-B actor corpus, superseding hand-maintained per-actor lists); this session spent most
of its time discovering that discovery mechanism, and the actor corpus it covers, still had
real, previously-invisible bugs — some dating back to the original port wave, one in the
discovery tool itself.

Three phases, in the order they were actually found (each phase's own finding motivated the
next):

1. **`.clj`/`.cljc` shadow-pair cleanup** — the same bug class ADR-2606131800 already knew
   about (stale `.clj` duplicates of a ported `.cljc` file, non-deterministically shadowing
   it on babashka's classpath), swept much further across the actor corpus than that session
   reached, using both manual grep sweeps and the repo's own existing
   `70-tools/scripts/test-health/audit.clj` detector (previously unused this session; its
   final read confirmed the sweep was complete modulo one already-documented, deliberately
   out-of-scope case).
2. **Foundry/Solidity CI health** — while looking for the next gap, found that only 1 of 12
   Foundry projects under `50-infra/` had any CI wiring at all; wiring it in immediately
   surfaced two real, previously-invisible bugs (a stale Charter Rider genesis hash, and a
   macOS-only-passing case-sensitive-import bug) that had never been caught because there
   was no CI for them to fail in.
3. **The `bb test:actors` `System/exit` landmine** — investigating whether the same
   "no CI, so real bugs go unnoticed" pattern applied to the actor test suite itself led to
   discovering that `bb test:actors` — the flagship task from ADR-2606131800 — has
   apparently never once completed a full run: 6 files call `(-main)` unguarded at the top
   level, ending in `System/exit`, silently killing the whole discovery-driven test process
   the instant any of them is `require`d.

## Decision (what landed)

### Phase 1 — `.clj`/`.cljc` shadow-pair cleanup (22 PRs, #2929–#2950)

Each PR: confirmed the stale `.clj`'s declared `ns` matches its `.cljc` sibling exactly
before deleting; re-ran the actor's own `run_tests.sh`/`run_tests.clj` before and after to
confirm no regression (assertion counts frequently *dropped slightly* post-fix — proof the
stale `.clj` had actually been winning classpath resolution with a thinner/different test
body, not a no-op cleanup).

| PR(s) | Actor(s) | Notes |
|---|---|---|
| #2929 | ake | Original precedent: `state_machine.py`/`cell.py` existence checks → `state_machine.cljc` |
| #2930 | suki, seigyo, suimin, igata, hodoki, kanayama, makura | 7-actor batch, dead `bb test:<name>` shim rewrite |
| #2931 | kakaku | 3 real bugs: duplicate namespaces, wrong fn name, key-type NPE, stale CI workflow |
| #2932 | mizuho | Ported `_substrate.cljc` helpers from noroshi; fixed defrecord keyword-access bug |
| #2933 | matsurigoto | 14 duplicates; fixed `D/ALLOWED-*` constant casing |
| #2934 | amime | File-path/namespace collision (`(ns amime)` bare file sitting at `methods/mesh.clj`) |
| #2935 | hirameki | `--classpath` override in `run_tests.sh` silently dropped git deps |
| #2936 | kabuto | 10 duplicates; 4 orphan CID-parity `.clj` files left unwired (genuine gap) |
| #2937 | kanjo | Diagnosed + killed an 8+ minute hang (test silently processing a real 4.4 MB corpus) |
| #2938 | keizu | 9 duplicates |
| #2939 | kosatsu | Self-corrected an over-eager deletion of non-duplicate orphan tests; `*file*`-in-`defn-`-body bug |
| #2940 | tasuke | 4 duplicates |
| #2941 | watatsuna | Fixed 2 orphan CID-parity files' real bugs (string vs keyword keys, stale pin) |
| #2942 | watari | Same CID-parity bugs as watatsuna, independently confirmed |
| #2943 | shionome | 14 duplicates |
| #2944 | 15 actors (funadaiku, futawa, hodoki, kanayama, makura, omise, organizer, ossekai, shukubo, silicon, sumitsubo, talent, tsubasa, yakushi, yotei) | Batched: identical `py/agent.clj` shadow across all 15 |
| #2945 | niyaku | 8 duplicates + 3 genuine stale-API bugs in orphan parity tests (`move`→`make-move` etc.) |
| #2946 | funadaiku | A second, separate duplicate pair; regenerated a stale committed golden artifact |
| #2947 | ainori, kawaraban, sanae, kasa | Batched; correctly identified non-duplicates to leave alone (ainori's `.clj`-only `py/agent`, kasa's incomplete `ingest.cljc` port) |
| #2948 | himotoki | Duplicate masked a broken `.cljc` test (wrong arity call, never actually run before) |
| #2949 | tazuna | Same masked-breakage pattern; rewrote 22 call sites to the real map-based API |
| #2950 | sentei | Same pattern; rewrote 17 call sites (positional+map vs the assumed keyword-varargs shape) |

Also #2955 (kakaku, phase-3 adjacent): one more shadow pair found via `test-health/audit.clj`,
missed by the manual sweep.

**Left deliberately unfixed (documented, not a regression):** `post_quantum-compat/methods/test_suite.clj`
— a genuine, separate structural bug (namespace/directory-name mismatch; no `run_tests.sh` at
all), confirmed via `test-health/audit.clj`'s own re-scan to be the only remaining shadow pair.

### Phase 2 — Foundry/Solidity CI (4 PRs, #2951–#2954)

- **#2951** — `etzhayyim-chain-contracts`'s Charter Rider genesis-hash drift-lock
  (`ConstitutionInvariants.t.sol::test_rider_text_hash_matches_file`) had been silently
  broken since the Rider was last bumped v3.0→v3.6 (six revisions); `Deploy.s.sol`'s pinned
  hash/version literal was never updated. Recomputed the correct hash via a throwaway
  `vm.readFile`+`keccak256` Foundry probe (not a shell pipe, to avoid encoding drift) and
  fixed all 3 places it's mirrored.
- **#2952** — 4 of 12 Foundry projects (`l2-anchor-contract`, `openmail-postage`,
  `etzhayyim-membership-contract`, `etzhayyim-paymaster`) could not even *compile*: no
  `forge-std` git submodule registered at all. Added it, pinned to the same commit 3 sibling
  projects already use.
- **#2953** — Added `.github/workflows/foundry-test.yml`: a `discover` job globs every
  `foundry.toml` under `50-infra/` (excluding vendored `lib/*`), a `test` job matrices
  `forge test` over each. Only `warifu-contracts` had CI before this.
- **#2954** — The new workflow's own first run immediately caught 2 of its 12 projects
  failing on Linux (macOS's case-insensitive filesystem had been silently tolerating
  `import {X} from "../src/x.sol"` against an actual file `X.sol` this whole time). Fixed 7
  import-path strings across 4 files in `etzhayyim-chain-contracts` and
  `vultr/geth-private/contracts`.

### Phase 3 — the `bb test:actors` landmine (2 PRs, #2955–#2956)

- **#2956** (the core finding) — 6 files
  (`test_bb_migration_{dns_sync,wave6a,wave6b,wave7a,wave8a}.clj`,
  `etzhayyim-organism/.../test_sensors.cljc`) call `(-main)` unguarded at the top level, where
  `-main` ends in `(System/exit ...)`. Discovery's `(apply require nss)` over the ~1037
  discovered namespaces hits one of these (alphabetically, always within roughly the first
  150) and the whole `bb` process is killed there — `System/exit` bypasses even
  `(catch Throwable ...)`, so there is no error, no stack trace, just a short, falsely-green
  exit. Confirmed by bisecting `(apply require (take N nss))`: N=50/100 completed with a real
  summary; N=150+ silently truncated. Added the standard
  `(when (= *file* (System/getProperty "babashka.file")) (-main))` guard to all 6. Also fixed,
  while in there: a stale fixture reference in the discovery tool's own test
  (`test_discovery.clj` pointed at a `danjo` file already deleted by an earlier, unrelated
  cleanup) and a `bb.edn` `test:aburi` shell-out to a legacy `test_ingest.py` already ported
  to `.cljc` (plus deleted the fully-dead sibling `test_bridge.py`, whose own imports
  reference python modules that no longer exist anywhere in that actor).

## Honest notes / debt carried forward

- **`bb test:actors`/`test:clj` are still not wired into CI.** Fixing the 6 landmines moves
  the crash boundary from ~1 namespace to several hundred, but a full run does not yet reach
  a clean pass: auto-discovery does not know about several actors' own deliberate
  per-actor exclusions of known-broken orphan `.clj` files (the same class of file phase 1
  repeatedly left "documented, deliberately unwired" — e.g. kabuto's `test_ingest.clj`,
  excluded from kabuto's own `run_tests.sh` for a separate CID-byte-parity reason).
  Discovery re-includes them anyway, and at least one throws an uncaught exception,
  again killing the whole run. Scoping and fixing this is the natural next step before CI
  wiring is possible; it was not attempted this session given the size already reached.
- **`etzhayyim.tools.discovery`'s "classpath-safe" filter has at least one more edge**:
  `etzhayyim-organism/.../test_sensors.cljc` declares a namespace that needs a non-standard
  classpath root (`20-actors/etzhayyim-organism/src`, not plain `20-actors`), which
  discovery's path-derived-ns check does not model — it is correctly excluded from the
  discovered set today, but for the "wrong" reason (a classpath mismatch happens to look the
  same as a root.-prefixed exclusion). This file also hangs indefinitely when run to
  completion (a separate, pre-existing, unrelated bug in its own test bodies) — not
  chased down this session.
- **The local shared checkout used for scoping/reading throughout this session
  (`orgs/etzhayyim/root`, viewed from within the west-managed superproject) was repeatedly
  stale relative to `origin/main`** — most notably, an initial investigation into whether the
  land-donation Foundry contracts (`TitheRouter`, `DisplacementDividend`, `PublicLandRegistry`,
  `LandClassRegistry`, `StewardTenureRegistry`, `LandRegistry`) had test coverage wrongly
  concluded they did not, purely because the shared checkout was behind; a fresh worktree off
  `origin/main` showed all 6 already covered (PRs #2924–#2928, an earlier part of this same
  session, confirmed still landed). Always verify file existence against `origin/main`
  directly (`git show`/`git ls-tree`/GitHub API) before concluding something is missing.
- **Sparse-checkout scoping produced several false-positive "failures" this session**
  (missing `CHARTER-RIDER.md`/lexicon `fs_permissions` targets, a missing cross-actor
  `todoke` dependency, a missing `90-docs` tree for the docs-registry test, a missing
  `cells.edn` for `test:mimamori`) — each confirmed as a checkout-scope artifact, not a real
  bug, by expanding the worktree's sparse-checkout and re-running. Worth remembering as a
  standing gotcha for future worktree-scoped investigation.

## Consequences

- The actor test corpus this repo has been building since ADR-2606131800 is measurably more
  trustworthy: 22+ actors' test suites now provably exercise their real `.cljc`
  implementation rather than a possibly-stale `.clj` shadow, and several previously-broken
  tests (masked by that same shadowing) are now fixed and actually asserting something.
- Foundry/Solidity now has CI coverage for the first time outside `warifu-contracts`,
  and the two real bugs that surfaced on its first run are fixed — future Solidity changes
  in any of the 12 covered projects get real, automatic verification instead of relying on
  someone remembering to run `forge test` locally on macOS (which, per this session, silently
  tolerates at least one whole class of Linux-fatal bug).
- The precise, previously-undiagnosed reason `bb test:actors` "worked" (exit 0) while
  covering only a tiny fraction of the actor corpus is now understood and fixed at the root
  cause, unblocking a future session's path to actually wiring it into CI.
