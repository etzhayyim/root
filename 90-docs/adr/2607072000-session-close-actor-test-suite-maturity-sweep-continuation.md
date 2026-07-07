---
id: adr-2607072000-session-close-actor-test-suite-maturity-sweep-continuation
title: "ADR-2607072000: Session close (continuation) — actor test-suite maturity sweep, 19 PRs: the recurring string/keyword key-convention bug class, stale golden-value pins, and the no-new-shell enforce-forward gate"
status: accepted
doc_type: adr
topic: session-close-actor-test-suite-maturity-sweep-continuation
authoritative: false
last_verified: 2026-07-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "non-authoritative process record; authoritative design = ADR-2606131800 (the py->clj refactor arc) + ADR-2606160842 (py->clj port wave) + ADR-2606072802 (no-new-shell enforce-forward)"
authoritative_for: []
depends_on:
  - adr-2607071000-session-close-actor-test-suite-maturity-sweep
  - adr-2606131800-session-close-python-to-clojure-tier-b-refactor-arc
  - adr-2606160842-kotoba-code-actor-py-to-clj-port-wave
related: []
supersedes: []
superseded_by: []
---

# ADR-2607072000: Session close (continuation) — actor test-suite maturity sweep

**Status**: accepted (process record — non-authoritative)
**Date**: 2026-07-07
**Deciders**: Jun Kawasaki

## Context

Direct continuation of ADR-2607071000: fixing the `bb test:actors` `System/exit` landmine
(that ADR's phase 3) moved the discovery process's crash boundary from ~1 namespace to
several hundred, which immediately surfaced a long tail of individual, previously-invisible
real bugs across the ported actor corpus — each namespace discovery could now actually reach
and run. This ADR documents that tail: 19 PRs (#2958–#2976) fixing one well-scoped cluster
of failures/errors at a time, following the same `/loop` self-paced pattern (worktree →
diagnose → fix → verify → PR → CI → merge → cleanup → next cluster), plus one out-of-band
task (reviewing and merging external contributor PR #2910, a paymaster factory-allowlist
security fix, on explicit request).

The work kept re-discovering the same handful of bug classes in different actors, which is
the more useful finding than any single fix:

1. **String-vs-keyword key convention.** Production `.cljc`/`.clj` modules across the actor
   corpus consistently use STRING keys (often colon-prefixed string VALUES like
   `":resilience"`, `":station"`) for Datom/tx/result maps — e.g. `{"ok" false "reason" "..."}`
   — never native Clojure keywords. Test/production code repeatedly got this wrong in BOTH
   directions: a caller doing keyword access (`:ok`) on an actually-string-keyed map (silently
   `nil`), or a caller building a keyword-keyed input (`{:items ...}`) where the callee does a
   string lookup (`(get m "items" [])`, silently falling through to a default). The meyasu fix
   (#2972) is the sharpest example: `run-cycle` had BOTH directions wrong at once — a
   keyword `:items` input key and keyword `:cards`/`:refused` output-access keys — meaning the
   actor's autonomous fuse→persist heartbeat had *never once* actually fused a card or
   persisted a real datom, for as long as the bug existed, while still exiting 0.
2. **Stale/never-independently-verified golden-value pins.** Several actors had hand-typed
   SHA256 hex literals pinned as "golden" CIDs that were never actually cross-checked against
   an independent implementation of the documented algorithm. Fixed for kosatsu (#2973) by
   dumping the exact datoms the Clojure implementation produces and re-implementing the
   documented canonical-JSON+SHA256 algorithm from scratch in plain Python (not reusing any
   Clojure code) — it reproduced the identical CID, proving the implementation was correct
   and only the pin was stale.
3. **Tests whose fixtures were orphaned by legitimate forward progress**, not regressions.
   `etzhayyim.cli`'s test suite (#2974) used `"bunseki"` as its example of a still-unwired
   library-only command and `"murakumo"` as its example of a command with a real `-main` —
   both assumptions had been legitimately overtaken (`bunseki` gained a real `-main` and
   moved to the wired `dispatchable` map; `murakumo-cmd` was deliberately kept a
   pure+injectable-IO library with no `-main`, correctly routed through the safer guarded
   `library-commands` path since it's fleet ops). `actor-publish`'s test (#2975) asserted a
   PDS host (`pds.etzhayyim.com`) that predated the real, deliberately-named
   `canonical-aozora-pds` constant (`aozora.app`) being finalized. In every case the fix was
   updating the test's assumption to match current, correct, intentional production
   behavior — not touching production code.
4. **Sparse-checkout false negatives, in both directions.** The usual failure mode (a test
   needing a file outside the worktree's sparse-checkout scope throws a
   `FileNotFoundException` that looks like a real bug) recurred for meyasu (needed
   `20-actors/mitooshi` + `20-actors/kakaku` transitively) and kosatsu (needed
   `00-contracts/schemas/crime-sanctions-ontology.kotoba.edn`). The no-new-shell fix (#2976)
   surfaced the INVERSE failure mode for the first time this session: a test that scans a
   real directory (`20-actors`) for violations trivially and falsely *passes* when that
   directory is outside sparse-checkout scope (scan finds nothing, vacuously satisfies the
   invariant) — the opposite of the usual false-positive-failure pattern, and easy to miss
   precisely because it looks like success.

## Decision (what landed)

### PRs #2958–#2971 (this session, pre-compaction)

| PR | Actor(s) / area | Notes |
|---|---|---|
| #2958 | `bb test:actors` | Further resilience + landmine fixes continuing ADR-2607071000 phase 3 |
| #2959 | maps | `ingest.cljc` API fix |
| #2960 | kabuto | ingest + kotoba_cid fixes |
| #2961 | kanjo | concept-map + ingest fixes |
| #2962 | paymaster | Follow-up fix: a stale branch's `remappings.txt` change would have silently reverted this session's earlier `forge-std` submodule cleanup (ADR-2607071000 phase 2) |
| #2963 | todoke | last-mile-parity fix |
| #2965 | mitooshi | forecast-parity fix |
| #2966 | mizuho | pid-parity fix |
| #2967 | uchiwake | crosscheck + fetch-off fix |
| #2968 | maps (4 files) | `HttpURLConnection/setRequestMethod` reflection is disallowed in babashka's SCI sandbox; switched to `babashka.http-client` (already used 8+ places in the repo) in `ingest.cljc`'s `push-batch` and `search.cljc`'s `http-avet-fn` |
| #2969 | kanjo | Deleted `test_analyze.clj`, a genuine orphan duplicate of an already-working test file with wrong API assumptions, never wired into `run_tests.sh` — the single largest cluster fixed this session (39 failures/errors) |
| #2970 | keizu | `*file*`-in-`defn-`-body bug (only reliably bound during a file's own top-level compilation, not when captured lazily inside a function body under `bb test:actors`'s auto-discovery model) + `verify-chain` fix + a genuinely-stale CID pin (15 failures/errors) |
| #2971 | funadaiku, kakaku, hodoki | `py/test_agent_parity.clj` key-convention bugs across all 3 (16 failures/errors); introduced a `py-list-repr` helper in `agent.cljc` for hodoki's Python-`repr(list)`-vs-Clojure-`pr-str` message-format mismatch |

Also reviewed and squash-merged **PR #2910** (external contributor `dir445`'s paymaster
factory-allowlist security fix, closing issue #1518) on explicit request: ran the real
Foundry test suite in an isolated worktree, traced the vulnerability logic, approved with a
detailed review comment. #2962 above is its direct follow-up.

### PRs #2972–#2976 (this session, post-compaction)

| PR | Actor(s) / area | Bug class | Notes |
|---|---|---|---|
| #2972 | meyasu | string/keyword key convention (both directions) | `run-cycle` passed `{:items items}` (keyword) into `handle-fuse`, which reads `(get state "items" [])` (string) — always empty, so fusion never ran; separately read the string-keyed return via `(:cards fused)`/`(:refused fused)` (keyword access) — always nil. Also removed a counterproductive `normalize-item` step that keywordized the seed's already-correct colon-prefixed string values, working against `agent.cljc`'s actual `RESILIENCE-USES` string-set convention. A second commit on the same PR fixed `meyasu-test.yml`'s CI workflow, which had never been updated to install babashka after the actor's py→cljc port (confirmed failing identically on `main` already — a pre-existing, unrelated infra gap, not caused by the code fix) |
| #2973 | kosatsu | stale golden-value pin | `test_kotoba.clj`'s pinned `tx_cid` didn't match; every other structural assertion in the file (datom counts, ordering, round-trip, tamper-detect) already passed. Independently re-derived the correct CID (see Context §2) and updated the pin; wired the previously-excluded namespace into `run_tests.sh` |
| #2974 | etzhayyim.cli (70-tools) | stale test assumption vs. legitimate forward progress | See Context §3 |
| #2975 | etzhayyim.actor-publish (70-tools) | stale test assumption vs. legitimate forward progress | See Context §3 |
| #2976 | 9 actors (denwaban, hibiki, hirameki, kotodama, magatama, meibo, saisei, tsuchifumi) + matsurigoto | no-new-shell enforce-forward gate (ADR-2606072802) | See Context §4 for how the gap was found. Ported each actor's `run_tests.sh`/`build.sh` to a `.clj` runner, verifying byte-identical stdout + exit code against the original before deleting it (matsurigoto's `wasm/build.sh` couldn't be run end-to-end — the `componentize-py` toolchain isn't installed in this environment — but lints clean under `clj-kondo` and its pure logic, camelCase derivation, was independently cross-checked against GNU `sed`'s documented `\U` behavior). `hibiki` already had an unused, equivalent `run_tests.clj` sitting next to its stale `.sh` — just deleted the leftover. Regenerated `shell-baseline.edn` via `--update`: a pure shrink (218→213 grandfathered), also dropping 5 already-stale entries from earlier, unrelated ports that had never been shrunk. Confirmed none of these 9 actors has a dedicated CI workflow — `bb test:actors` uses its own namespace auto-discovery, independent of these wrapper scripts, so coverage is unaffected either way |

Every PR followed the same verification ritual before merge: pre-commit sync check
(`git fetch` + `git rev-list --left-right --count origin/main...HEAD` = `0 0`), scoped
`git status`/`git diff --stat` review, the actor's own full test suite green, CI green
(`Analyze (actions)` / `CodeQL` / `lint-and-test`, monitored via a background `Monitor` +
`ScheduleWakeup` fallback), squash-merge, remote branch deletion, and local worktree/branch
cleanup.

## Consequences

- The actor test corpus is measurably more trustworthy in the same way ADR-2607071000
  described: several actors' tests now provably exercise real behavior instead of a bug that
  silently exited 0. meyasu's case is the starkest — its autonomous heartbeat had never once
  actually done its one job.
- The string-vs-keyword key-convention bug class is now a named, recognized pattern rather
  than a series of surprises; future actor work (and future test-authoring) can check for it
  directly instead of rediscovering it per-actor.
- `bb lint:no-new-shell` — the enforce-forward gate from ADR-2606072802 — is green again for
  the first time since 9 actors' `run_tests.sh`/`build.sh` were added after the baseline was
  set; the shrinks-only baseline is current and slightly smaller than before.

## Honest notes / debt carried forward

- **Remaining known singleton failures from the original triage, not yet reached**:
  `okaimono/kotoba/test_ingest_internal.cljc` (1), `maps/methods/test_reverse.cljc` (1). Given
  this session's track record, each is more likely a sparse-checkout or stale-assumption
  artifact than a real production bug, but neither has been verified yet.
- **`bb test:actors`/`test:clj` are still not wired into CI** — same debt ADR-2607071000
  already carried forward; not resolved by this continuation.
- **matsurigoto's `wasm/build.clj` port (#2976) could not be run end-to-end** in this
  environment (missing `componentize-py`); verified by lint + independent cross-check of its
  pure logic only. Worth a real end-to-end run wherever the full toolchain is available.
- The other ~209 grandfathered `.sh` files in `shell-baseline.edn` are intentionally NOT
  mass-ported (the gate is enforce-forward, not retroactive; per ADR-2606072802 they convert
  opportunistically).

## References

- ADR-2607071000 (Session close — actor test-suite maturity sweep, 33 PRs)
- ADR-2606131800 (Session close — Python→Clojure Tier-B refactor arc)
- ADR-2606160842 (kotoba code actor py→clj port wave)
- ADR-2606072802 (no-new-shell enforce-forward gate)
