# covscan.scan — accurate, regenerable test-coverage signal

A bb-native scan of the west workspace's per-area test coverage. It exists because the
committed `apps_maturity_report.csv` is a **stale hand-maintained artifact** (no
generator in the tree) whose crude `has_test` notion misses the clj-native test
forms actually used here (`methods/test_*.cljc`, `run_tests*`).

`covscan.scan` recognises **every** test form in the tree:

```
run_tests*  ·  tests/ · test/ · __tests__/ · e2e/  ·  methods/test_*.cljc
test_*.py  ·  *_test.{clj,cljc,py,ts,js}  ·  *.{test,spec}.{ts,tsx,js,jsx}
```

```bash
WEST_TOPDIR=/path/to/west bb scan
bb scan /path/to/west
bb test          # detector unit tests (pure `tested?` + a tmp-dir fixture)
```

## Snapshot (2026-07-19)

```
apps        tested   54 /  572  (  9.4%)
etzh-repos  tested  158 /  183  ( 86.3%)
graph       tested    0 /    3  (  0.0%)
infra       tested   16 /   58  ( 27.6%)
tools       tested   13 /   38  ( 34.2%)
TOTAL       tested  241 /  854  ( 28.2%)
```

The headline: the **flat etzhayyim repositories are ~86% tested**, while
**root-owned `60-apps` is the coverage frontier** — many are generated
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
  Flat repositories come from `orgs/etzhayyim`; root-owned projects come from
  `orgs/etzhayyim/root/{30-graph,50-infra,60-apps,70-tools}`. Retired numbered
  actor/engine directories are never treated as operational sources.

clj/bb per the repo "operational code = clj/bb" convention; no external deps.
