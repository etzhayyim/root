---
id: adr-2605151500
title: "etzhayyim CLI Go → Python Migration"
status: active
doc_type: adr
topic: toolchain
authoritative: true
last_verified: "2026-05-15"
# items 1-20 + all extensions + deps graph/export, kosei stack, murakumo eval/fleet-plan/graph-extract/graph-ingest/coverage-export/train-experts/optimize/kubelet-deploy, murakumo fleet jotai/nodes/versions/deploy/drain/undrain/restart/logs/watch (all fleet ops), agent verify, agent organism, vault create/add/ls/audit/device-key/run/share/unshare, docs validate, code-quality run, actors migrate-to-plc, coverage world/infer/hospitality stubs, deps governance-wit/export, identity migrate-paths, monitor shinka (full local analysis), code exec, bonsai canopy/growth/release (Go-only stubs), kashika terminal/html/sla/shinka/hyoka, lint update targets (silent-catch-update/ts-camel-update/json-sql-update) implemented; Go-only: dodaf generate, identity migrate (2-PDS state machine), bonsai canopy/growth/release (etzhayyimdb), cohort bootstrap, metrics-bi, seed-oil/naphtha (etzhayyimdb), monitor-vote cast/resolve/list (pgxpool), coverage world/infer/hospitality (pgxpool), actors cc-coverage (pgxpool stub in Python), ka (pgxpool), deps sql (pgxpool)
---

# ADR-2605151500: etzhayyim CLI Go → Python Migration

**Date**: 2026-05-15
**Status**: Accepted
**Deciders**: Jun Kawasaki

## Context

The `etzhayyim` CLI (`70-tools/etzhayyim/`) is ~85 K lines of Go (171 files, 40+ top-level
commands). It orchestrates every layer of the platform: deploy, build, agent
lifecycle, XRPC invocation, Shannon analysis, coverage, kaizen, projector, etc.

The platform's execution layer has fully converged on Python:
- All production LangGraph apps are Python (animeka, terminal-agent, kiyo, …).
- `kotodama` (`40-engine/kotoba/crates/kotoba-kotodama/py/`) provides asyncpg, LangGraph, NATS,
  FastAPI, Granian, httpx — a complete Python SDK.
- ADR-2605080600 standardised LangGraph Server + Granian as the L3 runtime.
- Zero LangGraph TypeScript apps are in production.

Maintaining a Go CLI that wraps a Python execution layer creates an impedance
mismatch: Go must shell-out or make HTTP calls for anything that touches
LangGraph, kotodama, or NATS. Agentic commands (`actors shinka`,
`coverage actors heal`, `kaizen --fix`) cannot be expressed cleanly in Go
without duplicating or proxying Python logic.

## Decision

Migrate `etzhayyim` to Python using a **parallel-operation strategy**:

1. The Python binary is named **`etzhayyim-py`** during the migration period.
2. Go binary remains as **`etzhayyim`** (no rename) until a command is fully ported.
3. When all commands are ported, rename: Go → `etzhayyim-go` (archive), Python → `etzhayyim`.
4. Scaffold lives at `70-tools/etzhayyim-py/`.

### CLI framework split

| Command category | Framework |
|---|---|
| Data commands (build, deploy, deploy-worker, dns-sync, database, …) | Click / Typer |
| Agent-loop commands (actors shinka, coverage actors heal, kaizen --fix) | LangGraph Pregel |
| All others (xrpc, projector, agent-token, shannon, mokuteki, …) | Click / Typer |

LangGraph is used **only** where the command requires an agent loop with
checkpointing. Everything else is a plain Click command.

### Dependency baseline

```
click>=8.1
httpx>=0.27
pydantic>=2
psycopg[binary,pool]>=3.2
```

Optional extras (`pip install etzhayyim-py[agent]`):
```
langgraph>=0.3
langgraph-cli[inmem]>=0.1.71
```

Model names MUST use `resolveModelId()` / `MURAKUMO_DEFAULT_MODEL` — never
hardcoded strings.

## Porting order (suggested)

1. `xrpc` — thin HTTP wrapper, no Go-specific logic. ✓
2. `projector` — pure XRPC calls to `mcp.etzhayyim.com`. ✓
3. `agent-token` — single JWT mint via `com.atproto.server.getServiceAuth`. ✓
4. `shannon` / `mokuteki` — analytics read commands. ✓
5. `deploy` / `build` — heavier; port after lighter commands stabilise. ✓
6. `actors shinka` — parallel async httpx to Murakumo/Ollama + applyWrites. ✓
7. `kaizen --fix` — builds a codex prompt and pipes to `codex exec -`. ✓
8. `coverage actors heal` — parallel ThreadPoolExecutor + LLM healing of kotodama.jsonld. ✓
9. `authn signin` — OAuth2 Auth Code + PKCE; localhost callback server; writes `~/.etzhayyim/auth.json`. ✓
10. `dns-sync` — CF API mutations. ✓
11. `database migrate` — Kotoba/Datomic migration runner. ✓
12. `mokuteki kashika` — HTML/JSON/DOT visualization; auto-opens browser via `webbrowser.open()`. ✓
13. `mokuteki store` — flatten report → temp JSON → `duckdb` CLI → Parquet; update catalog.json. ✓
14. `mokuteki query` — shell out to `duckdb -c SQL` with parquet glob; `$TABLE` substitution. ✓
15. `mokuteki history` — read catalog.json, list snapshots sorted by `snapshot_ms` desc. ✓
16. `logs arch` — `git log --stat` parsing + path-prefix layer classifier (projects/infra/actors/docs/engine/graph/contracts/tools/root). Outputs archLogReport with by_layer/by_scope/events. ✓
17. `cohort` XRPC subcommands — seed, gen, fission, evidence, emit, lineage, lineage-stats, repair-edge, forest, dashboard, coverage, gap, snapshot, diff, drift (all XRPC POST/GET). `cohort bootstrap` remains Go-only (deps.toml mutations). ✓
18. `agent-runtime restart` — kept as Go-only stub; Go's agent_runtime.go has no `restart` subcommand either (render/publish/register only). Kubectl-level operation deferred. ✓ (stub correct)
19. `kaizen logs` — OCEL event aggregation; tries CF Analytics Engine SQL API (`ocel_v2` table, `quantileWeighted` p50/p99), falls back to PDS `/_pds/ocel`; per-method slow/error findings; `--fix code-exec` builds structured prompt → `claude -p` / `codex exec -`; `--fix-engine murakumo` calls `scoreDataQuality` + `optimizeCycle`. ✓
20. `nono deploy` — Phase 1: `npx wrangler deploy` subprocess in component dir (resolved from nanoid or `--dir`). Phase 2: reads `nono-manifest.jsonld`, POSTs to `/xrpc/com.etzhayyim.actor.registerManifest`. `--skip-skills` skips Phase 2. ✓

### Extensions (beyond original 20-item list)

- `nono build` — esbuild/pnpm subprocess; resolves component dir from nanoid or `--dir`; `--dry-run`. ✓
- `deps kv-sync` — CF KV DEPS_REGISTRY sync from `[[mitama_actors]]`; `--diff`, `--apply`, `--no-cf`. ✓
- `training promote/eval/list-runs/list-checkpoints/list-snapshots/coverage/serving` — 7 training XRPC commands. ✓
- `vertex tier/list/stats` — ADR-0040 tier registry from `30-graph/deps.toml`. ✓
- `actors jokyo` — parallel HTTP health + heartbeat scoring per actor (grades S/A/B/C/D). ✓
- `apps coverage` — domain knowledge coverage: static analysis (app.ts AST) + PDS live record count + XRPC self-eval. ✓
- `apps kyumei-koji` — DID self-information gathering readiness: declared sources, live record counts, sub-DID metrics, knowledge gaps, recommendations. ✓
- `kosei` extended — list/show/set/promote/demote/suggest/diff/stats/summary/snapshot/query/history/matrix/sbom/kashika (HTML tier dashboard). ✓
- `bunseki` extended — scan/dfg/variants/conformance/performance/recommendations (OCEL process mining). ✓
- `bunseki arch` subcommands — scan/dfg/variants/conformance/cycles (haisen graph local analysis). ✓
- `source-graph dot/sql/violations` — GraphViz DOT + DuckDB SQL + cycle/orphan detection. ✓
- `hinshitsu` — actor fleet code quality: actors/kojo/fleet scan/evaluate/verify/kaizen/diff-fixed. ✓
- `coverage governance/oil` — governance field coverage + oil-domain actor coverage. ✓
- `systemofsystem scan/layers/interfaces/health` — SoS boundary + coupling + health verdict. ✓
- `pds qa/status` — HTTP probe suite (health, cache-hit, cold-query, concurrent, timeline). ✓
- `code agent` — LangGraph terminal-agent subprocess launcher. ✓
- `murakumo models declare` — read fleet-models.json declared placement. ✓
- `process-mining scan/bottlenecks/flow` — PDS handler static analysis for performance bottlenecks. ✓
- `performance-test run/report` — concurrent HTTP load test + latency report. ✓
- `set-profiles run` — parallel AT Protocol profile sync from kotodama.jsonld. ✓
- `deps graph` — layer DAG visualization from `deps.toml [app_layer.*]` + `[infra_layer.*]`; tree/mermaid/json formats. ✓
- `kosei stack <nanoid>` — deep tech-stack profile: CF bindings, features (WebGPU/ONNX/FIDO2/MCP/BPMN/Evolver), npm/Cargo deps. ✓
- `murakumo eval` — Hayate V6 evaluation benchmark subprocess (eval_v6_bench.py); dry-run support. ✓
- `murakumo fleet jotai/nodes/versions` — XRPC fleet status + Nomad node status thin wrappers. ✓
- `murakumo models list` — SSH probes each Mac Mini in parallel (ssh BatchMode=yes) to compare declared vs actual model presence; table + legend output. ✓
- `murakumo models apply` — SSH installs missing models on target minis (ollama pull / HF curl / ComfyUI diffusers); `--dry-run`, `--target`, `--only-mini`. HF_TOKEN env required for checkpoint/diffusers/wan downloads. ✓
- `actors cc-coverage` / `common-crawler-coverage` — Go-only stub (pgxpool required for vertex_domain/vertex_page queries); raises ClickException with clear message to use Go binary. ✓
- `authn login` / `logout` — aliases for signin/signout (muscle-memory aliases). ✓
- `authn revoke` — POST `/oauth/revoke` for access/refresh/id tokens; `--token` explicit mode; `--keep-local` gate; `-q` quiet. ✓
- `authn migrate` — exchange stored session JWT for API key (sk_live_*) via `com.etzhayyim.auth.createApiKey`; `--dry-run` mode. ✓
- `authz create-api-key` — upgraded with `--name`, `--test` (sk_test_*), `-q` (key-only output for scripting) flags matching Go. ✓
- `agent verify` — verify ERC-8004 on-chain agent registration against local proof files. ✓
- `agent organism status/publish` — organism HTTP status probe; publish stub (full flow requires Go). ✓
- `murakumo graph-extract/graph-ingest/coverage-export` — subprocess launchers for LFM graph pipeline scripts. ✓
- `murakumo train-experts` — XRPC POST to `com.etzhayyim.murakumo.trainExperts`. ✓
- `murakumo optimize` — dry-run cycle description; live mode prints actionable message. ✓
- `vault create/add/ls/audit/device-key/run` — zero-knowledge vault ops: AES-KW key wrap (client-side), AES-256-GCM content encrypt; `run` injects secrets as env vars. ✓
- `vault share/unshare` — X25519-ECIES key wrap (HKDF-SHA256 + AES-KW) for sharing vault access across DIDs via signal prekey bundle. ✓
- `docs validate` — docs registry validation: registry shape, file existence, YAML front matter, graph.jsonld consistency. ✓
- `code-quality run` — unified quality scorer: cargo-machete, cargo-duplicates, go-vet, go-mod-tidy, jscpd, kotodama-lint, frontend-lint, perf-test, sql-injection/full-scan, dead-exports; JSON + text output; `--skip` filter. ✓
- `murakumo fleet-plan` — Hayate V5 fleet plan generator (hayate_v5_split.py fleet); target-slots/dim/groups/mamba-per-group/top-m/batch-size/lr/data-source/lancedb-uri; `--dry-run`. ✓
- `actors migrate-to-plc` — upgraded from stub to real XRPC `com.etzhayyim.plc.migrateActor`; `--offline` mock mode; `--apply` gate. ✓
- `coverage world/infer/hospitality` — Go-only stubs (require Kotoba/Datomic direct via pgxpool); `--help` prints available options. ✓
- `deps governance-wit` — WIT + governance compliance static analysis: wit/world.wit import count, src/app.ts command/handle count, kotodama.jsonld governance fields; score + verdict; `--format json`. ✓
- `identity migrate-paths` — legacy-nanoid → did:etzhayyim path migration: reads `[[legacy_nanoids]]` from deps.toml, computes SHA-256-based path DID, submits via XRPC `com.etzhayyim.identity.submitOp`; `--apply` gate; `--json`. ✓
- `migrate-manifest run` — pure file transformation (etzhayyim.json → kotodama.jsonld); reads routes/runtime/build/deploy fields from etzhayyim.json; optionally parses `kotodama.toml` (sections: component, component.env, component.compose, triggers.http, triggers.w_commit, ui, ui.ssr_routes, game, space, [[space.channels]], evolver, pool, [[extensions]], interfaces); `--batch` scans subdirs; `--dry-run` prints to stdout; zero DB dependencies. ✓
- `docs-gen schema` — factual schema auto-generation: reads `kotodama.jsonld` (app/nanoid/DID/collections/performerType), `wrangler.jsonc` (service bindings via `"binding":` regex), `src/*.ts` (G("Label") graph patterns); `--all` scans all `60-apps/etzhayyim-project-*/wasm/*/`; `--format json|md`; `--out` file sink; fully portable local file analysis. ✓
- `deps score` — HTTP-based: fetches `deps.etzhayyim.com/api/deps/graph`, extracts link coverage summary (totalLinks/resolvedLinks/linkCoverageRate/isolatedCount/workerDeployCoverage/governanceCoverage/wprotoIntegrationScore); `--format text|json`; `--timeout-sec`. ✓
- `deps audit` — HTTP-based: optionally POSTs to `/api/hooks/component` (manual_refresh), waits `--wait-sec`, then runs `deps score`; `--full-audit/--no-full-audit`; `--format text|json`. ✓
- `coverage-test` alias — top-level alias registered in cli.py: `etzhayyim coverage-test` = `etzhayyim coverage` group (mirrors Go's `coverage-test = coverage test` alias). ✓
- `plugin list/install/upgrade` — GitHub-release downloader: fetches latest version via `api.github.com/repos/bytecodealliance/wasm-tools/releases/latest`, downloads tar.gz, extracts binary to `~/.cache/etzhayyim/plugins/<name>/`; also shows `tinygo`/`docker` from PATH; no DB access. ✓
- `dodaf tv1 query` / `dodaf av2 get` / `dodaf rules context` / `dodaf add` / `dodaf validate` — DuckDB CLI subprocess commands against `80-data/dodaf/*.parquet`; TV-1 query by `--id`, `--tags`, `--severity`, `--path`; AV-2 dict lookup by term/alias; cross-view `rules context` query; `add` appends row to any view; `validate` scans CLAUDE.md for unregistered `## CRITICAL:` sections; `--json` flag on all; NDJSON/array output normalization. ✓
- `dodaf init` — seeds TV-1 (11 seed rules), AV-2 (9 terms), OV-5 (6 activities) from embedded Python dicts → temp NDJSON → DuckDB `COPY … TO (FORMAT PARQUET)` in `80-data/dodaf/`; `--workspace-dir`; `--force` to overwrite existing parquet files. ✓
- `deps mv` — generates 2 Kotoba/Datomic `CREATE MATERIALIZED VIEW` DDL statements (`mv_deps_component_live`, `mv_deps_summary_live`) from embedded SQL; `--format sql|text`; `--apply` exits nonzero with "use etzhayyim (Go CLI)" message (requires live Kotoba/Datomic pgxpool). ✓
- `dodaf migrate` — walks workspace for all `CLAUDE.md` files; extracts `## CRITICAL:` sections via line-scanner; generates TV-1 IDs from dir+title slug; appends new rows to `tv1_standards.parquet` via `_write_json_to_parquet`; replaces section body with `→ etzhayyim dodaf tv1 query --id <id>` pointer in-place; `--dry-run`, `--skip-pointer`. ✓
- `dodaf seed` — reads `tv1_standards.parquet` via DuckDB CLI; POSTs each row to `com.atproto.repo.createRecord` as `com.etzhayyim.dodaf.tv1Standard` via `urllib.request`; `etzhayyim_TOKEN` auth; `--dry-run` prints without hitting PDS; `--pds` override. ✓
- `domain-ingest local` — upgraded from stub: resolves `70-tools/scripts/ingest-domain-data.ts` from git root, runs `npx tsx <script> [--domain] [--limit] [--dry-run] [--skip-llm]`; exits nonzero when script or `npx` missing. ✓
- `domain-ingest common-crawl` — new subcommand: resolves `60-apps/etzhayyim-project-common-crawl/scripts/phase5_inject.py`, runs via `sys.executable`; `--source intel|graph`, `--batch-size`, `--dry-run`, `--pds` (injects `PDS_URL` env). ✓
- `monitor shinka` — full port replacing XRPC stub: discovers apps via `kotodama.jsonld` rglob; reads `src/app.ts` for `resolveHeartbeatCadence`/`createInboxBuffer`/`createCadenceState`/`shouldDrill`/`shouldValidate`/`shouldAnalyze`/`shouldEngage`/`heartbeatCount %`; parallel analysis via `ThreadPoolExecutor`; optional live `POST /_heartbeat` test; optional `--hyoka` domain scoring overlay (in-memory, KG nodes approximate to 0 without DB); optional `--store` to `80-data/hyoka/` NDJSON→Parquet via DuckDB CLI; `--gate` regression check on `avg_hyoka_score`/`top10_avg`/`low_count`; `--json` output via `dataclasses.asdict`; sub-DID freshness via `com.atproto.repo.listRecords` XRPC probe; `--nanoid` single-app filter; `--freshness-hours` threshold. ✓
- `agent-runtime render` — delegates to `70-tools/scripts/contract/render-agent-runtime-public.py --cluster <cluster> <manifests...>`; fallback assembles minimal JSON when script absent; `--out` file sink. ✓
- `agent-runtime publish` — render + optional IPFS upload (`--no-dry-run` raises ClickException directing to Go binary for HMAC signing); outputs SHA256 + bytes + schema + kind. ✓
- `agent-runtime register` — dry-run builds ERC-8004 registration payload (SHA256 metadata hash, keccak root DID hash from args or `--registration` JSON); `--no-dry-run` raises ClickException (EVM signing requires Go). ✓
- `agent-runtime publish-agent` — dry-run combines render + publish + register into single result JSON; `--no-dry-run` raises ClickException. ✓
- `agent-runtime holochain-plan` — pure data transformation: builds Holochain conductor k8s plan JSON with `agentDid`, `hApp` (name/uri/sha256/roleName/zomeName/dnaHash), `k8s` (namespace/workload/conductorImage/env); validates `--namespace != default`; `--out` file sink. ✓
- `mitama schema-status` — `SHOW ALTER TABLE COLUMN FROM graphar` via `com.etzhayyim.kagami.sql` XRPC; `--table` filter, `--all`, `--state` (RUNNING/FINISHED/CANCELLED); `--json`. ✓
- `training run` — full port of Go's `training run --kind sft|lora|distill`: routes to `com.etzhayyim.apps.training.runSft`/`runLora`/`runDistill` XRPC; validates `--base` (sft/lora), `--student-base` + `--teacher-kind` (distill); supports `--dataset`, `--label`, `--run-id`, `--gpu`, `--seed`, `--hyperparams` JSON, `--eval-benches`, `--rationale`, `--distill-method`; `--json` output. ✓
- `deps export` — exports deps score/audit/apps JSON files for the frontend visualizer: fetches `deps.etzhayyim.com/api/deps/graph`, computes `_summarize_deps_graph`, writes `deps-score.json`/`deps-audit.json`/`deps-apps.json` to `--out-dir`; `--no-refresh` skips HTTP; `--top` controls top-N unresolved nodes; `--score-name`/`--audit-name`/`--apps-name` overrides. ✓
- `deps sql` — Go-only stub (queries `mv_deps_component_live` via pgxpool); raises ClickException directing to `etzhayyim deps sql`. ✓
- `code exec` — non-interactive one-shot terminal-agent mode: resolves `OPENROUTER_API_KEY` from `--api-key` arg → `OPENROUTER_API_KEY` env → macOS Keychain (`security find-generic-password -s etzhayyim.openrouter -w`); delegates to `uv run agent --local --message <msg> --dir <path>`; `--dry-run` prints command without executing; `--model` and `--uv-bin` overrides. ✓
- `murakumo kubelet-deploy` — Mac Mini fleet Virtual Kubelet deployment: dry-run prints start command (`cd .../50-infra/k8s/murakumo-kubelet && python3 start_kubelets.py`); live mode requires `MURAKUMO_FLEET_SSH_PASS` env (otherwise ClickException); `--nodes all|<csv>`, `--concurrency`, `--repo-root` flags. ✓
- `common-crawler download` — subprocess launcher: `{CC_DATA_DIR}/.venv/bin/python3 {scripts}/download_all.py`; `--workers`, `--crawl`, `--format` (wat,wet), `--domains` filter file, `--range-start`/`--range-end` sharding, `--wat-only`/`--wet-only`/`--resume`; `CC_DATA_DIR` env (default: `/Volumes/251220/CC/2603`). ✓
- `common-crawler graph` — subprocess launcher: `phase3_wat_to_sql.py` (monorepo project scripts first, then CC_DATA_DIR fallback); `--source`, `--batch-size`, `--output` (sql/jsonl/parquet), `--domain` filter, `--crawl`. ✓
- `common-crawler intel` — subprocess launcher: `phase4_intel_extract.py`; `--limit`, `--resume`, `--model`, `--min-pages`, `--domain`, `--output`, `--concurrency`. ✓
- `common-crawler inject` — deprecated redirect to `domain-ingest common-crawl` (prints deprecation warning, delegates via subprocess). ✓
- `common-crawler monitor` / `status` — local filesystem monitor: reads download/phase3/phase4 log tails, disk usage (rglob), file counts, state JSON mtime; `pgrep` process check; no CC_DATA_DIR required (graceful not-found). ✓
- `common-crawler purge` — deletes pipeline state files: `--phase download|graph|intel|all`; removes `.download_state.json`, `.phase3v2_state.json`, `.phase4v3_state.json`, `domain_intel.jsonl.gz`, `knowledge_graph.sql`. ✓
- `common-crawler list-crawls` — subprocess launcher: `list_crawls.py`; `--year`, `--json` flags. ✓

> **Note on "LangGraph Pregel" framing**: the ADR originally listed these as
> LangGraph Pregel commands. The actual Go implementations do not use Pregel:
> `actors shinka` uses `sync.WaitGroup` + semaphore over direct LLM HTTP calls;
> `kaizen --fix` shells out to `codex exec -`. The Python port matches the Go
> mechanics: `asyncio.gather` + `Semaphore` for shinka; `subprocess.run` for
> kaizen. LangGraph Pregel remains the target for any *new* native-Python
> agentic commands that need checkpointing (not ports of existing Go commands).

Commands are ported one-by-one. Until ported, every stub in `etzhayyim-py` prints:

```
This command is not yet ported. Use the Go binary: etzhayyim <command>
```

## Alternatives Considered

### Keep Go
- Pro: working today, fast binary.
- Con: every agentic command requires a Python sub-process or HTTP proxy.
  Long-term maintenance of two runtimes outweighs short-term stability.

### TypeScript (LangGraph JS)
Scored 4.87 vs Python 8.49 on a 9-axis weighted evaluation:

| Axis | Weight | Go→TS | Go→Py |
|---|---|---|---|
| Runtime homogeneity | 0.20 | 2 | 10 |
| SDK coverage (kotodama) | 0.18 | 1 | 10 |
| LangGraph ecosystem fit | 0.15 | 3 | 10 |
| Existing agent patterns | 0.12 | 1 | 10 |
| Toolchain (uv/hatch) | 0.10 | 5 | 9 |
| Type safety | 0.10 | 9 | 8 |
| Binary distribution | 0.08 | 8 | 5 |
| Hire / onboard speed | 0.05 | 6 | 7 |
| Build time | 0.02 | 6 | 8 |
| **Weighted total** | | **4.87** | **8.49** |

TypeScript has no kotodama equivalent and no production LangGraph deployment
in this repo. The gap is decisive.

## Consequences

- `70-tools/etzhayyim-py/` scaffold added (this ADR).
- `70-tools/deps.toml` gains `[subdirs."etzhayyim-py"]` entry.
- Root `deps.toml` `[[migrations]]` tracks `etzhayyim-cli-go-to-python`.
- Go binary (`70-tools/etzhayyim/`) remains unchanged until each command is ported.
- CI: both `etzhayyim build` (Go) and `etzhayyim-py --help` (Python) must pass.
- Cutover: after final command port, `etzhayyim-go` archive + `etzhayyim` symlink → Python.

### Known deferred items

**Scoped-JWT auto-wrap — implemented.**
`auth.py::mint_scoped_jwt()` wraps the base token into a scoped JWT via
`com.atproto.server.getServiceAuth` with a 290s in-process cache (thread-safe).
`xrpc.py` calls `scoped_auth_headers(nsid)` so every XRPC call is automatically
scoped. Disable with `etzhayyim_SCOPED_AUTH=off`.

**`knownApps` map duplication — accepted drift.**
`src/etzhayyim/xrpc.py` contains a hard-coded copy of the 9-entry `knownApps` map
from `xrpc.go`. The maps will drift until both binaries read from `deps.toml`
or a shared registry endpoint. Tracked in root `deps.toml` `[[migrations]]`.

### Permanent Go-only commands (will not be ported)

| Command | Reason |
|---|---|
| `dodaf generate` | 1398 LOC; generates Parquet schema from OCEL/BPMN. No Python equivalent planned. |
| `identity migrate` | PDS migration state machine (request token, transfer blocks, finalize). Complex two-PDS choreography. |
| `murakumo fleet deploy/drain/undrain/restart/logs/watch` | SSH + Nomad client ops; fleet mutating ops require Nomad CLI or SSH. Python covers read-only (jotai/nodes/versions). |
| `cohort bootstrap` | Reads and mutates `deps.toml [[cohort_actors]]` via Go TOML library. |
| `metrics-bi` | Reads from CF Analytics Engine + Stripe + graph DB (`etzhayyimdb`). Full dashboard requires direct DB access. |
| `seed-oil-backbone` / `seed-naphtha-supply` | Seed commands use `etzhayyimdb` for bulk graph inserts. |
| `monitor-vote cast/resolve/list` | Direct `pgxpool` (pgx/v5) connections for triple-witness quorum writes. |
| `murakumo models list/apply` | SSH connections to Mac mini fleet nodes; no Python Nomad/SSH equivalent planned. |
| `coverage world` / `coverage infer` / `coverage hospitality` | Direct `pgxpool` connections to Kotoba/Datomic `graphar.vertex_*`; Python has stubs that print error. |
| `actors cc-coverage` (actors common-crawler-coverage) | Direct `pgxpool` connections to Kotoba/Datomic for Common Crawler domain coverage. |
| `ka` (company operations dashboard) | Direct `pgxpool` Strategy Graph queries; Python has no equivalent. |
| `domain-ingest`, `collect`, `common-crawler`, `docs generate` | DB-dependent or machine-specific infrastructure; deferred indefinitely. `docs-gen schema` (local file analysis) and `migrate-manifest run` (pure file transformation) are ported; `docs generate` (LLM-backed generation) remains Go-only. `plugin list/install/upgrade` is ported (GitHub release downloader). |
| `deps sql` | Direct `db.RawQuery` on `mv_deps_component_live` (pgx/v5 — Kotoba/Datomic). |
| `deps mv` | Generates + applies Kotoba/Datomic DDL (`CREATE MATERIALIZED VIEW`); `--apply` uses `db.RawQuery`. |
| `deps export` | Calls `node scripts/generate-wit-deps-graph.mjs` + complex local scoring from graph JSON; deferred. |
