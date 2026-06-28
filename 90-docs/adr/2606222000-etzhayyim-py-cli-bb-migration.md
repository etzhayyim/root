---
id: 2606222000
title: etzhayyim-py CLI → babashka/Clojure migration plan (waves 1–8 + bb CLI capstone — module ports COMPLETE)
status: accepted
doc_type: adr
topic: bb-migration
authoritative: true
last_verified: 2026-06-23
priority: implementation
axis: substrate
weight: 0.20
priority_note: >
  Operational convention (実装/engineering) — changes the tooling substrate;
  no charter amendment required. Governed by CLAUDE.md §"Operational code = clj/bb
  over the kotoba Datom log".
authoritative_for:
  - etzhayyim-py CLI migration strategy + triage classification
  - the COMPLETE ~49-module cljc port record (waves 1–8) + the bb CLI capstone (etzhayyim.cli / `bb e7m`)
  - the bb/SCI IO-rewrite pattern (injectable :http-fn/:proc-fn/:fs-fn + build-X-request/command shape layer + dry-run)
  - the consolidated bb/SCI porting gotchas reference
  - babashka.cli / http-client / process mapping reference
depends_on:
  - 2605262130  # kotoba storage substrate
  - 2605312345  # kotoba Datom log first-class canonical state
related:
  - 2606101200  # ibuki bb pattern
  - 2606172100  # kaname deployed heartbeat pattern
  - 2606211712  # kafun cljc pattern
supersedes: []
superseded_by: []
---

# etzhayyim-py CLI → babashka/Clojure migration plan (wave 1)

## Context

`70-tools/etzhayyim-py/` is a ~45-module Python CLI package (`e7m` / `etzhayyim-cli`)
that covers workspace analysis (shannon/bonsai/identifier-audit), deployment ops
(deploy/metrics/kaizen), actor management (actors/identity/authz), and infrastructure
commands (dns-sync/projector/monitoring).

CLAUDE.md §"Operational code = clj/bb over the kotoba Datom log" requires NEW
operational/tooling code to be Clojure/babashka backed by the kotoba Datom log, NOT Python
or shell. The etzhayyim-py CLI predates this rule and is grandfathered, but new increments
MUST be in clj/bb. A phased migration strategy is needed.

---

## Decision

### Wave 1 (this ADR): Port 3 pure-logic leaf modules; publish migration plan

Port the 3 modules whose core logic can be extracted cleanly without click/httpx/subprocess:

1. **`etzhayyim.identifier-audit`** (`70-tools/src/etzhayyim/identifier_audit.cljc`)
   — nanoid/DID/name validation logic; pure regex + map transforms; no I/O dependency
2. **`etzhayyim.bonsai`** (`70-tools/src/etzhayyim/bonsai.cljc`)
   — workspace tier classification + prune scoring; pure file-scan logic
3. **`etzhayyim.source-graph`** (`70-tools/src/etzhayyim/source_graph.cljc`)
   — TS/Python import graph scanning + cycle detection + layer-violation analysis; pure logic

All three modules are **additive** (Python originals are NOT deleted). The `.cljc` files
sit on the bb classpath at `70-tools/src/` (declared in `bb.edn :paths`).

---

## Full Triage Table (~45 modules)

| Module | Class | Notes |
|---|---|---|
| `cli.py` | (b) CLI entry | click entrypoint; migrates last as bb.edn tasks |
| `shannon.py` | (a)+(c) mixed | PURE: WEIGHTS dict, `_cap`, `_sh_entropy`, `build_report`, DSM math — PORT in wave 2. IO/subprocess: `_walk`, `_sh_scan`, filesystem checks — defer |
| `bonsai.py` | (a) ported | Wave 1: `bonsai.cljc` |
| `identifier_audit.py` | (a) ported | Wave 1: `identifier_audit.cljc` |
| `source_graph.py` | (a) ported | Wave 1: `source_graph.cljc` |
| `kosei.py` | (a)+(c) mixed | PURE: `_TIER_ETA`, `_suggest_tier` — PORT in wave 2. IO: duckdb subprocess, filesystem scan — defer |
| `haisen.py` | (c) IO/subprocess | runs clang-tidy/flake8/semgrep; defer until bb.process wrapper |
| `kashika.py` | (c) IO/haisen | calls haisen scan; defer |
| `process_mining.py` | (c) IO | reads BPMN/event-log files; defer |
| `systemofsystem.py` | (c) IO/haisen | calls haisen; defer |
| `mokuteki.py` | (c) IO/subprocess | duckdb + shannon + filesystem; defer |
| `dodaf.py` | (c) IO/subprocess | duckdb CLI subprocess; Parquet seed data; defer |
| `actors.py` | (c) httpx | actor registry HTTP; defer |
| `agent_cmd.py` | (c) httpx | agent HTTP client; defer |
| `agent_runtime.py` | (c) httpx | runtime HTTP; defer |
| `agent_token.py` | (c) httpx | token HTTP; defer |
| `apps.py` | (c) httpx | apps HTTP; defer |
| `auth.py` | (c) subprocess | git/keychain; defer |
| `authn.py` | (c) subprocess | identity subprocess; defer |
| `authz.py` | (c) httpx | authz HTTP; defer |
| `bunseki.py` | (c) httpx | analysis HTTP; defer |
| `code_quality.py` | (c) subprocess | linting subprocess; defer |
| `cohort.py` | (c) httpx | cohort HTTP; defer |
| `complex_stubs.py` | (c) subprocess | stubs subprocess; defer |
| `coverage.py` | (c) httpx | coverage HTTP; defer |
| `database.py` | (c) httpx | DB HTTP; defer |
| `deploy.py` | (c) httpx+subprocess | deployment; defer |
| `deps.py` | (c) httpx | deps HTTP; defer |
| `dns_sync.py` | (c) httpx | Cloudflare DNS HTTP; defer |
| `hinshitsu.py` | (c) httpx | quality HTTP; defer |
| `identity.py` | (c) httpx | identity HTTP; defer |
| `kagami.py` | (c) httpx | mirror HTTP; defer |
| `kaizen.py` | (c) httpx | kaizen HTTP; defer |
| `lint.py` | (d) RETIRED | ported to `etzhayyim.lint.cljc` → `bb e7m lint [all\|rules\|<rule>] [--root D] [--json]`; read-only parity verified green, update-target node-script leg preserved; `lint.py` + its python tests `git rm`'d (finish pass) |
| `logs.py` | (c) httpx | logs HTTP; defer |
| `metrics.py` | (c) httpx | metrics HTTP; defer |
| `mitama.py` | (c) httpx | mitama HTTP; defer |
| `monitor.py` | (c) httpx | monitor HTTP; defer |
| `murakumo_cmd.py` | (c) httpx | Murakumo HTTP; defer |
| `nono.py` | (c) httpx | nono HTTP; defer |
| `organism.py` | (d) superseded | → `70-tools/src/etzhayyim/organism.cljc` |
| `projector.py` | (c) httpx | projector HTTP; defer |
| `training.py` | (c) httpx | training HTTP; defer |
| `vertex.py` | (c) httpx | Vertex AI HTTP; defer |
| `workspace.py` | (c) httpx | workspace HTTP; defer |
| `xrpc.py` | (c) httpx | XRPC client; defer |
| `yoroshiku.py` | (c) httpx | yoroshiku HTTP; defer (cljc exists co-located but not on classpath) |

**Summary**: class (a) pure-logic = 4 (3 ported wave 1, shannon + kosei-tiers wave 2 ✅); class (b) CLI entry = 1; class (c) IO/network = 38; class (d) superseded = 1.

---

## Migration Order Recommendation

**Wave 1 (merged PR #2173)**: `identifier_audit`, `bonsai`, `source_graph` → `.cljc` pure logic extracted.

**Wave 2 (landed ✅)**: 2 new `.cljc` files:
- `shannon_scores.cljc` — WEIGHTS/cap/sh-entropy/build-report + DSM/Bayes/bottleneck/minimize math (pure math port of `shannon.py`)
- `kosei_tiers.cljc` — `tier-eta`/`tier-order`/`suggest-tier`/`next-tier`/`prev-tier` (pure classification port of `kosei.py`)
- `test_bb_migration_wave2.clj` — 38 tests / 67 assertions, all green under `bb`
- Bug fixed: `.indexOf` on Clojure persistent vector is not supported in bb/SCI — use `keep-indexed` instead
- Bug fixed: `min-key` over string elements fails in cycle-canonicalization — use `compare` + `reduce`

---

## Migration status: module ports COMPLETE (waves 1–8 + bb CLI capstone)

All ~49 command modules now have an additive `etzhayyim.<name>.cljc` port under
`70-tools/src/etzhayyim/` (the `.py` originals are kept). Pure logic is parity-verified;
IO/subprocess legs use the injectable-fn + shape-layer pattern (below) and are dry-run-safe.

| Wave | PR(s) | Modules | Kind |
|---|---|---|---|
| 1 | #2173 | identifier_audit, bonsai, source_graph | pure logic |
| 2 | #2174 | shannon_scores, kosei_tiers | pure logic |
| 3a / 3b | #2178 / #2177 | coverage, dodaf, deps, metrics / mokuteki, haisen, hinshitsu, code_quality | pure + IO |
| 4a / 4b | #2180 / #2182 | kashika, logs / bunseki, process_mining, systemofsystem, complex_stubs | pure + IO |
| 5a / 5b | #2184 / #2186 | auth, authn, authz, agent_token, agent_runtime, identity / kagami, kaizen, vertex | pure helpers (crypto deferred) |
| IO-pattern | #2189 | dns_sync | **established the IO-rewrite pattern** |
| 6a / 6b / 6c | #2218 / #2220 / #2223 | actors, apps / deploy, agent_cmd / kosei, shannon (remaining) | httpx / subprocess / large-pure |
| 7a / 7b | #2221 / #2222 | monitor, xrpc / murakumo_cmd, database | http+ws / infra-subprocess |
| 8a / 8b | #2228 / #2227 | cohort, nono, mitama, yoroshiku / projector, training, workspace, lint | small IO |
| capstone | (this PR) | `etzhayyim.cli` (`bb e7m`) | CLI dispatcher |

### The IO-rewrite pattern (reusable; established by dns_sync #2189)

Every side-effecting command is split into a PURE shape layer + an INJECTABLE executor:

- `build-X-request` → `{:method :url :headers :body?}` (httpx) / `build-X-command` → argv vector
  (subprocess, injection-safe — a string vector, never shell-interpolated). These are pure and
  unit-tested by asserting the constructed shape matches the Python's request/command **without
  executing it**.
- The executor takes an injectable `:http-fn` / `:proc-fn` / `:fs-fn` (default = the real
  `babashka.{http-client,process,fs}`); tests inject a fake that records calls.
- A `--dry-run` / `:apply? false` / `:no-X?` mode performs zero mutating calls.
- Secrets are read lazily from the env at call time, never at load time.
- **Honest limit**: live behavioral parity (against real PDS / Cloudflare / docker / kubectl)
  needs operator credentials and is NOT exercised offline — only the request/command SHAPING is.

### bb CLI capstone (`etzhayyim.cli` / `bb e7m`)

`70-tools/src/etzhayyim/cli.cljc` is the bb counterpart of `cli.py`'s click dispatcher:
`bb e7m list` prints the migration record (every ported module), `bb e7m <cmd>` dispatches
commands that expose a `-main` (murakumo, vitals). A module without a wired CLI entry reports
honestly that it is ported as a **library** (`ns etzhayyim.<cmd>`) and that its per-command
argv-wiring (click options → `babashka.cli` spec) is the remaining mechanical finish — the Python
`e7m` runs alongside until then. No business logic lives in the dispatcher; it only routes.

### Deferred (operator-IO legs that are live-verification-gated, by design)

These need a live host / credentials / a lib bb lacks, so they stay behind the injectable fn with a
documented note: `murakumo_cmd` fleet-watch poll-loop + concurrent-SSH models-list + fleet-plan;
`database` repair-order (`psycopg`); `actors` async concurrency (`asyncio.gather` → sequential);
the file-IO scan legs of `kosei`/`shannon`/`coverage`; `monitor` live websocket connect.

### Consolidated bb/SCI porting gotchas (discovered across waves — apply preemptively)

- `.indexOf` on a Clojure **vector** is unsupported in bb/SCI → use `keep-indexed` (`.indexOf` is fine on strings).
- `min-key`/`max-key` require **numeric** keys; over strings → rewrite with `compare` + `reduce`.
- Python `a or b` treats `0`/`""` as falsy; Clojure `or` does not → a `py-or` helper where it matters.
- `(or (seq s) …)` returns a **char-seq**, not the string → use `(or (when (seq s) s) …)`.
- `re-seq` with non-capturing `(?:…)` groups returns **strings** (don't `map first`); with capture groups → `map second`.
- `str/trimr` has **no 2-arg form** in SCI; `format "%.2f"` on a `Long` throws → coerce `(double x)`.
- `#?(:bb …)` reader-conditional: use **separate** forms, never two `:bb` keys in one `#?`; `sort` returns a **seq**, not a vector.
- bb loads `.clj` **before** `.cljc` (shadow hazard) — a stale `.clj` silently wins.

### Remaining mechanical finish (low-leverage, optional)

Per-command argv-wiring for the ~47 library-only commands (each click command's options →
`babashka.cli` spec + dispatch in `etzhayyim.cli`) + the deferred operator-IO legs above. The
Python `e7m` keeps working in parallel, so this is convention-completion, not a blocker.

---

## Babashka → Python Mapping Reference

| Python | babashka | Notes |
|---|---|---|
| `click.group` / `click.command` | `bb.edn :tasks` + `babashka.cli/dispatch` | Multi-level: outer `:tasks` key, inner dispatch |
| `click.option` | `babashka.cli/parse-opts` | Auto-converts `--foo-bar` → `:foo-bar` |
| `click.argument` | positional in `babashka.cli/parse-opts` | `{:coerce {:args []}}` |
| `httpx.get` / `.post` | `babashka.http-client/get` / `/post` | Same API shape; supports `:headers` `:body` `:query-params` |
| `subprocess.run` | `babashka.process/shell` or `/process` | `(shell "git status")` for simple; `(process args)` for streams |
| `os.environ["K"]` | `(System/getenv "K")` | Plain JVM call under bb |
| `json.dumps` | `cheshire.core/generate-string` | Already on bb classpath |
| `json.loads` | `cheshire.core/parse-string` | Same |
| `pathlib.Path.rglob` | `babashka.fs/glob` | `(fs/glob "." "**/*.ts")` |
| `asyncio` | `future` / `pmap` | Babashka does not support async; use futures or agents |

---

## What Wave 1 PR (#2173) Landed

3 new `.cljc` files on the bb classpath (`70-tools/src/etzhayyim/`):

- `identifier_audit.cljc` — `audit-jsonld-data`, `run-audit`, `violations->report`
- `bonsai.cljc` — `classify-tier`, `score-node`, `scan-workspace`, `growth-health`
- `source_graph.cljc` — `parse-ts-imports`, `parse-py-imports`, `scan-source-graph`, `orphan-paths`, `cycles`, `layer-violations`

1 test file:
- `test_bb_migration_wave1.clj` — 29 tests / 44 assertions, all green under `bb`

Python originals are **not deleted** (additive porting).

---

## What Wave 2 Lands

2 new `.cljc` files on the bb classpath (`70-tools/src/etzhayyim/`):

- `shannon_scores.cljc` — `weights`, `cap`, `sh-entropy`, `build-report`, `dsm-cuthill-mckee`, `dsm-detect-cycles`, `dsm-find-clusters`, `build-dsm-report`, `build-bayesnet-report`, `build-bottleneck-report`, `build-minimize-report`
- `kosei_tiers.cljc` — `tier-eta`, `tier-order`, `default-tier`, `valid-tier?`, `tier-eta-of`, `suggest-tier`, `tier-index`, `next-tier`, `prev-tier`

1 test file:
- `test_bb_migration_wave2.clj` — 38 tests / 67 assertions, all green under `bb`

IO/subprocess functions (`_walk`, `_sh_scan`, duckdb) remain in Python (not ported).

---

## Parity Notes (vs Python originals)

- **`identifier_audit`**: regex patterns ported 1:1; `re-matches` = Python `re.fullmatch`; `re-seq` = Python `re.findall`. JSON parsing uses `cheshire` (bb classpath) when `:data` not pre-supplied.
- **`bonsai`**: tier-hint order uses an ordered vector (not map) so `seed > leaf` wins for `CLAUDE.md`. `str/blank?` check = Python `content.count("\n") == 0` semantics. `elif` structure preserved via `(and (pos? lines) (< lines 5))` guard.
- **`source_graph`**: relative-import edges use the raw import string as target (no filesystem resolution in pure mode — callers supply pre-read content). Layer-violation direction matches Python `src_idx > tgt_idx`.

---

## Honest Remaining Scope

- **38 class-(c) IO/network modules** remain in Python (httpx + subprocess). They require either `babashka.http-client` wrapper ports (waves 4+) or are superseded by the kotoba substrate / actor SDKs directly.
- **`shannon.py` scoring math** (wave 2) — ✅ LANDED as `shannon_scores.cljc`.
- **CLI entry replacement** (`cli.py` → `bb.edn :tasks`) is wave 5+, after most modules are ported.
- **The Python CLI is NOT deprecated** — it remains the production CLI. This is wave 1 of a multi-wave migration; do NOT claim the CLI is migrated.

---

## Consequences

- `etzhayyim.identifier-audit`, `etzhayyim.bonsai`, `etzhayyim.source-graph` are now callable from any bb task or Clojure code on the `70-tools/src` classpath.
- Future workspace-analysis bb tasks should compose these namespaces rather than shelling out to Python.
- The test file serves as a parity regression guard — any future `.cljc` changes that break behavior vs. the documented Python semantics will fail the suite.

---

## Alternatives Considered

1. **Full big-bang port** — rejected; too risky with 45 modules, many IO-heavy.
2. **Keep only Python, never migrate** — violates CLAUDE.md §"Operational code = clj/bb" convention.
3. **Wrap Python from bb via subprocess** — valid short-term tactic but not a migration; still creates Python dependency.

---

## References

- `70-tools/etzhayyim-py/src/etzhayyim/` — Python CLI source
- `70-tools/src/etzhayyim/` — bb/cljc tooling home (classpath root per `bb.edn :paths`)
- CLAUDE.md §"Operational code = clj/bb over the kotoba Datom log"
- ADR-2605312345 (kotoba Datom log first-class canonical state)
- ADR-2606172100 (kaname deployed heartbeat — reference bb pattern)
