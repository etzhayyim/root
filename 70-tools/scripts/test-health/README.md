# test-health audit

A read-only repo-wide audit of actor test-suite health, institutionalising the manual
"measure the debt" scans that surfaced the **py→cljc port-wave** debt:

- **#2041** tsumugi seed-drift (count assertions lagged the grown seed)
- **#2042** uchiwake `.clj` shadows (a stale `.clj` shadowed the canonical `.cljc` port — babashka prefers `.clj`)
- **#2043** broken `bb test:<actor>` shims (run_tests.sh pointing at tasks removed when `test:actors` auto-discovery superseded per-actor lists)

## Run

```bash
bb 70-tools/scripts/test-health/audit.clj            # print the triage summary (fast static scan)
bb 70-tools/scripts/test-health/audit.clj --check    # + self-check the detector's invariants (exit 1 on violation)
bb 70-tools/scripts/test-health/audit.clj --probe    # + RUN each broken shim's tests in isolation → classify
bb 70-tools/scripts/test-health/audit.clj --write    # + (re)write AUDIT.md, the committed snapshot
```

## Companion: `fn-coverage.clj` — per-function coverage triage

`audit.clj` finds *suite*-level debt (shadows, broken shims). Its companion `fn-coverage.clj`
finds *function*-level gaps: it classifies every PUBLIC `defn` in an actor's `methods/*.cljc` as
**tested** (a `test_*.cljc` names it), **internal** (only a sibling method fn calls it — likely
exercised indirectly), or **ISOLATED** (no test and no internal caller — the strongest gap
candidate). This institutionalises the manual scan that surfaced the analytical-validation wave
(suji #2169, funamori #2175, busshi #2179, iryo #2185 were all ISOLATED public functions with a
real closed-form worth pinning).

```bash
bb 70-tools/scripts/test-health/fn-coverage.clj             # summary table, all actors
bb 70-tools/scripts/test-health/fn-coverage.clj --isolated  # + the full ISOLATED worklist
bb 70-tools/scripts/test-health/fn-coverage.clj <actor>     # one actor, full per-fn breakdown
```

It is a **triage aid, not a verdict**: an ISOLATED fn may still be exercised by an integration
test that builds it from data, or be a CLI entry (`-main`/`-report`) that needs no unit test, or be
reached only via `resolve` (textual matching can't see that). Verify a candidate before testing it.

An actor flagged **`†`** (e.g. `ibuki †`, `mimamori †`, hyphenated-dir actors) is **excluded from
the `bb test:actors` discovery runner** and run by its own dedicated bb task — so a new
`test_*.cljc` you add there will NOT be picked up by the discovery runner; verify it via that
actor's task instead. The flag is computed from the real `etzhayyim.tools.discovery/actor-test-nss`
output, not re-derived, so it tracks the runner exactly.

`--probe` (opt-in, slower) actually runs each broken-shim actor's auto-discovered tests in an
isolated subprocess and classifies it **clean-repoint** (safe #2043 fix) / **tests-fail** /
**load-error** — so the register says *which* shims are mechanically fixable vs need investigation.
Truth source is the `PROBE <fail> <error>` line printed by `run-tests`, NOT the subprocess exit code
(the probe runner does not `System/exit` on failures, so a red suite still exits 0).

## What it measures (two deterministic debt classes; no test execution, no writes unless `--write`)

1. **`.clj`/`.cljc` shadow pairs** — a `foo.clj` beside `foo.cljc` resolves to the SAME namespace; bb loads the `.clj`, so a stale `.clj` shadows the canonical `.cljc`. Classified `:identical` (harmless dup) vs `:different` (stale-risk cleanup candidate).
2. **Broken `bb test:<name>` shims** — `run_tests.sh` whose `exec bb test:<name>` names a task not defined in `bb.edn` (the suite never runs). (Mentions of the old task name in `#` comments are ignored.)

## Not an auto-fixer

A `:different` shadow is a **candidate**, not an auto-fix — which side is canonical is the actor owner's call (sizes/scope diverge mid-migration; the #2042 fix removed `.clj` only after the `.cljc` port proved complete via a green suite). A broken shim is a safe mechanical repoint **iff** the actor's tests pass once invocable (#2043 pattern); otherwise it surfaces a real pre-existing failure to triage. See `AUDIT.md` for the current register.

## Two sub-classes of the shadow bug (empirically separated via the safe oracle)

Removing a stale `.clj` shadow → running the suite → keeping the removal **only if green** (the
"oracle") splits the debt into two kinds:

- **clean — keyword/string key-access bug.** The stale `.clj` reads `(get state :items)` (keyword)
  while the caller + the canonical `.cljc` use `(get state "items")` (string); babashka loads the
  `.clj`, so the handler silently sees nothing. Removing the `.clj` fully greens the suite.
  **Verified clean + fixed: uchiwake (#2042), meyasu + the cross-actor kakaku agent (#2048).**
- **deeper — PAUSED MID-MIGRATION between two CID families (ADR-gated, NOT autonomous).** The
  root cause of the `.clj`-vs-`.cljc` divergence for the kotoba-emitter actors is a documented
  cross-actor split: per `70-tools/scripts/clj-test-sweep/canonical_form_invariant.clj`, the
  commit-DAG emitters fall into **two content-addressing families** — **Family A** (Clojure
  `{:datoms <pr-str> :prev <pr-str>}`, empty-tx cid `b752d9f3…`: **kabuto · watatsuna · watari ·
  kanjo**) and **Family B** (JSON `{"datoms":…,"prev":…}`, empty-tx cid `b2fc787b…`: kakaku ·
  meyasu · uchiwake). Each affected actor ships BOTH a `.clj` kotoba (Family A — the *current*
  canonical that bb loads) and a `.cljc` kotoba (Family B — the future form); the broken shim +
  keyword/string test divergence are symptoms of a migration **paused** partway. A full attempt
  (kabuto, 2026-06-22) made the 59-test suite green by completing the `.cljc` (string keys +
  re-exposing `gated-source?`/`merge-bridged` + `canonical-order` + re-pinned CIDs) — but that
  **migrates kabuto from Family A → Family B, which the sweep tool explicitly flags as a
  CID-breaking change reserved for a future canonical-form-unification ADR** (it pins the split so
  exactly this is caught). **Reverted in full.** So these are not "choose a design" — they are
  blocked on a governance decision (which family is canonical, when to unify). Oracle-verified
  members: **kanjo / kabuto / watatsuna** (Family-A, paused → Family-B); **tasuke / kosatsu /
  keizu** additionally mix cwd-relative `slurp` path bugs in `test-no-external-io`.

So: probe `tests-fail` / `load-error` actors with the oracle; the key-access ones (where the stale
`.clj` is the ONLY thing wrong and its `.cljc` is the complete canonical) are a safe mechanical fix;
the divergent-design ones are deferred to their owners — the fix is a design decision, not a port.

## Scan from a worktree, NOT the shared checkout (avoid stale-file false positives)

**Run any suite scan from a fresh git worktree off `origin/main`, never from the shared main
checkout.** The shared checkout (`CLAUDE.md` § Worktree isolation) is chronically *behind*
`origin/main` (observed 127 commits) and carries other agents' in-flight + leftover files. Babashka
loads whatever is on disk, so a file that `origin/main` already **deleted** (e.g. a pre-port
`autorun.clj` superseded by `autorun.cljc`) still sits in the stale checkout and gets loaded — the
classic `.clj`-shadow failure mode — producing a **load error that does not exist on `origin/main`**
(verified 2026-06: a `danjo` "load error" was purely a stale local `methods/autorun.clj`; danjo is
24/24 green on a fresh worktree). It cuts both ways: a stale *passing* `.clj` can also mask a real
`.cljc` failure (false green). EnterWorktree (or `git worktree add … origin/main`) gives a clean
`origin/main` tree; the safe-oracle fixes in this lineage (meyasu/haraedo/todoke/fuchi/kanae) were
all done in worktrees for exactly this reason. Only trust a red/green verdict produced against
`origin/main`.
