---
id: 2606222000
title: etzhayyim-py CLI → babashka/Clojure migration plan (wave 1)
status: accepted
doc_type: adr
topic: bb-migration
authoritative: true
last_verified: 2026-06-22
priority: implementation
axis: substrate
weight: 0.20
priority_note: >
  Operational convention (実装/engineering) — changes the tooling substrate;
  no charter amendment required. Governed by CLAUDE.md §"Operational code = clj/bb
  over the kotoba Datom log".
authoritative_for:
  - etzhayyim-py CLI migration strategy + triage classification
  - wave-1 cljc ports (identifier-audit, bonsai, source-graph)
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
| `lint.py` | (c) subprocess | lint subprocess; defer |
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

**Summary**: class (a) pure-logic = 4 (3 ported wave 1, shannon wave 2); class (b) CLI entry = 1; class (c) IO/network = 38; class (d) superseded = 1.

---

## Migration Order Recommendation

**Wave 1 (this PR)**: `identifier_audit`, `bonsai`, `source_graph` → `.cljc` pure logic extracted.

**Wave 2** (next increment):
- `shannon_scores.cljc` — WEIGHTS, `_cap`, `_sh_entropy`, `build_report` (pure math)
- `kosei_tiers.cljc` — `_TIER_ETA`, `_TIER_ORDER`, `_suggest_tier` (pure classification)
- Add bb tasks to `bb.edn` that run these as CLI commands (replacing `e7m shannon`/`e7m bonsai`)

**Wave 3** (IO layer — `babashka.process` wrappers):
- `haisen.cljc` — wraps flake8/clang-tidy/semgrep via `babashka.process/shell`
- `kashika.cljc` — calls `haisen.cljc`
- Filesystem-walk host wrappers that supply `{:path :content}` maps to the pure-logic fns

**Wave 4** (HTTP commands — `babashka.http-client` wrappers):
- Start with the highest-value commands (deploy, metrics, kaizen, actors)
- Each Python `@click.group` → a `bb.edn` task + `babashka.cli/dispatch`

**Wave 5** (CLI entry consolidation):
- Replace `cli.py` entry with a bb.edn `:tasks` map + `babashka.cli`
- Delete or archive the Python package once all tasks are ported

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

## What This PR Lands

3 new `.cljc` files on the bb classpath (`70-tools/src/etzhayyim/`):

- `identifier_audit.cljc` — `audit-jsonld-data`, `run-audit`, `violations->report`
- `bonsai.cljc` — `classify-tier`, `score-node`, `scan-workspace`, `growth-health`
- `source_graph.cljc` — `parse-ts-imports`, `parse-py-imports`, `scan-source-graph`, `orphan-paths`, `cycles`, `layer-violations`

1 test file:
- `test_bb_migration_wave1.clj` — 29 tests / 44 assertions, all green under `bb`

Python originals are **not deleted** (additive porting).

---

## Parity Notes (vs Python originals)

- **`identifier_audit`**: regex patterns ported 1:1; `re-matches` = Python `re.fullmatch`; `re-seq` = Python `re.findall`. JSON parsing uses `cheshire` (bb classpath) when `:data` not pre-supplied.
- **`bonsai`**: tier-hint order uses an ordered vector (not map) so `seed > leaf` wins for `CLAUDE.md`. `str/blank?` check = Python `content.count("\n") == 0` semantics. `elif` structure preserved via `(and (pos? lines) (< lines 5))` guard.
- **`source_graph`**: relative-import edges use the raw import string as target (no filesystem resolution in pure mode — callers supply pre-read content). Layer-violation direction matches Python `src_idx > tgt_idx`.

---

## Honest Remaining Scope

- **38 class-(c) IO/network modules** remain in Python (httpx + subprocess). They require either `babashka.http-client` wrapper ports (waves 4+) or are superseded by the kotoba substrate / actor SDKs directly.
- **`shannon.py` scoring math** (wave 2) is extractable but deferred to keep wave 1 focused.
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
