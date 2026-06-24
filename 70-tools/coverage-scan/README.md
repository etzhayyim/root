# covscan.scan — accurate, regenerable test-coverage signal

A bb-native scan of the monorepo's per-area test coverage. It exists because the
committed `apps_maturity_report.csv` is a **stale hand-maintained artifact** (no
generator in the tree) whose crude `has_test` notion misses the clj-native test
forms actually used here (`methods/test_*.cljc`, `run_tests*`).

`covscan.scan` recognises **every** test form in the tree:

```
run_tests*  ·  tests/ · test/ · __tests__/ · e2e/  ·  methods/test_*.cljc
test_*.py  ·  *_test.{clj,cljc,py,ts,js}  ·  *.{test,spec}.{ts,tsx,js,jsx}
```

```bash
bb scan          # per-area coverage over ../.. (the repo root)
bb scan /path    # explicit root
bb test          # detector unit tests (pure `tested?` + a tmp-dir fixture)
```

## Snapshot (2026-06-24)

```
20-actors   tested 1189 / 1253  ( 94.9%)   ← clj-native actors: mature
30-graph    tested    1 /    3  ( 33.3%)
40-engine   tested    2 /    9  ( 22.2%)
50-infra    tested   16 /   60  ( 26.7%)
60-apps     tested   53 /  573  (  9.2%)   ← the real coverage frontier
70-tools    tested   13 /   39  ( 33.3%)
TOTAL       tested 1274 / 1937  ( 65.8%)
```

The headline: the **clj-native actor layer is ~95% tested** (the org's core is
mature), while **`60-apps` is the coverage frontier** — many are generated
wasm/appview wrappers, but the real gaps live here, not in the actors. A future
`/loop coverage` iteration should target high-value `60-apps` projects.

## Design

- `tested?` is a **pure predicate** over project-relative paths (one regex,
  unit-tested as the spec).
- `project-tested?` applies it via **targeted globs** over source roots only
  (`src` / `lib` / `app` / `appview` / `worker` / `packages` / `test*` / `e2e`)
  — never walks `node_modules` or build output, so it stays fast and avoids
  vendor false-positives.
- `scan` classifies each area's immediate subdirs; `-main` prints the table.

clj/bb per the repo "operational code = clj/bb" convention; no external deps.
