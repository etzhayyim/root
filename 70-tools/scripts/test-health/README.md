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
