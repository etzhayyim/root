<!-- ⚠️  STEP 8 CUTOVER MATERIAL — DO NOT RENAME IN ISOLATION ⚠️  -->
<!--
  This file is part of the Step 8 cutover sequence (CLAUDE.md status table).
  Renaming or moving it without updating deps.toml [[migrations]] shinka-mst-rewrite
  AND the ADR reference in ADR-2605215200 will break the cutover runbook.
-->

# SHINKA-MIGRATION-NOTES.md

Authoritative ADR: **ADR-2605215200** (`90-docs/adr/2605215200-etzhayyim-shinka-pregel-mst-rewrite.md`)

This document is the per-function migration table for the `shinka-mst-rewrite` migration tracked in
`deps.toml`. It is the sister document to `PYMAGATAMA-MIGRATION-NOTES.md` and follows the same format.

Scope: vendor `pymagatama.primitives.shinka` + `pymagatama.handlers.shinka` + `langgraph_graphs.shinka_cron_tick`.
16 findings from the 2026-05-21 substrate-fit audit (§2).

---

## 16-Row Migration Table

| # | File | Line(s) | Current (vendor) | Target (etzhayyim) | Verdict | Reason |
|---|---|---|---|---|---|---|
| 1 | `primitives/shinka.py` | 26-27 | `from pymagatama.db_sync import sync_cursor` | Remove; replace with `@etzhayyim/sdk` MST client | REIMPLEMENT | psycopg3/RW dependency root import |
| 2 | `primitives/shinka.py` | 26-32 | `with sync_cursor() as cur: cur.execute("SELECT shinka_tick_actor(%s)", ...)` | `KarmaHegemonObservationCell` + `EvolutionValidationCell` + `EvolutionEmissionCell` Pregel cells (ADR-2605215200 §1) | REIMPLEMENT | SQL UDF call against RisingWave — entire execution kernel |
| 3 | `primitives/shinka.py` | 57-60 | `from pymagatama.shinka import _load_state, _resolve_cadence` | `karma_hegemon_observation_cell()` in `shinka_murakumo.py` | REIMPLEMENT | _load_state reads `vertex_shinka_evolution` via RW SELECT |
| 4 | `primitives/shinka.py` | 86-88 | `from pymagatama.shinka import _compose_content` | RESOLVED M1: `_compose_content` is pure LLM composition — no RW write. Inputs: mood (str), axes (JouchoAxes), actions (list[str]), follower_delta_count (int). Calls `llm.call_tier_json("classifier", system=..., user=...)` → **vendor Vultr Serverless / OpenRouter** (`mistralai/Devstral-2-123B` or env override). Output: `compose_draft = {text: str≤300, tone: str, model: str, latencyMs: int, attempts: int}` stored in `vertex_shinka_evolution.props.draft`. Religious-corp MUST route LLM via **EVO-X2 LiteLLM** per ADR-2605215000, NOT vendor OpenRouter. Prompt is NOT copied here; write new prompt for religious-corp variant. | PORT-adapted (LLM coupling must change) | _compose_content itself does no RW SELECT/INSERT; the draft JSON schema is portable but LLM backend must be replaced |
| 5 | `primitives/shinka.py` | 112-114 | `from pymagatama.shinka import _write_heartbeat` | `shinka_heartbeat_cell()` in `shinka_murakumo.py` | REIMPLEMENT | _write_heartbeat → `INSERT INTO vertex_shinka_heartbeat` via RW |
| 6 | `primitives/shinka.py` | 134-137 | `from pymagatama.shinka import _emit_evolution` | `evolution_emission_cell()` in `shinka_murakumo.py` | REIMPLEMENT | _emit_evolution → `INSERT INTO vertex_shinka_evolution_event` via RW |
| 7 | `primitives/shinka.py` (file level) | ALL | `task_shinka_tick` synchronous SQL UDF call pattern | `shinka_tick()` in `shinka_murakumo.py` (Pregel super-step orchestration) | REIMPLEMENT | Entire primitives/shinka.py is a thin wrapper around `shinka_tick_actor` SQL UDF |
| 8 | `langgraph_graphs/shinka_cron_tick.py` | 43-45 | `from pymagatama.primitives.shinka import task_shinka_tick` | Pregel cell dispatch via `magatama-cell-runner` cron (ADR-2605202100) | REIMPLEMENT | Graph entry calls vendor SQL UDF — not a portable LangGraph pattern |
| 9 | `langgraph_graphs/shinka_cron_tick.py` | 63-72 | `build_graph()` StateGraph (START → shinka_tick → END) | 4-cell Pregel topology (ADR-2605215200 §1) — observation → validation → emission → heartbeat | REIMPLEMENT | Single-node graph wraps SQL UDF; religious-corp uses multi-cell Pregel |
| 10 | `langgraph_graphs/shinka_cron_tick.py` | 27 | `_DEFAULT_ACTOR = "did:web:yoro.gftd.ai"` | `did:web:etzhayyim.com` (religious-corp root DID) | PORT-adapted | Actor DID changes from vendor domain to religious-corp domain at Step 8 |
| 11 | `langgraph_graphs/shinka_cron_tick.py` | 47 | `asyncio.run(task_shinka_tick(...))` | Async cell dispatch via `magatama-cell-runner` — no `asyncio.run()` in cell body | PORT-adapted | asyncio.run() pattern is incompatible with launchd cell-runner async runtime |
| 12 | `handlers/shinka.py` | 14 | `from pymagatama.db_sync import sync_cursor` | Remove at Step 8 cutover; handler file becomes VENDOR-ONLY | VENDOR-ONLY | Handler file stays for vendor SaaS tier; religious-corp uses Pregel cells directly |
| 13 | `handlers/shinka.py` | 22-31 | `task_shinka_tick` → `SELECT shinka_tick_actor(%s)` | VENDOR-ONLY — keep for vendor paid SaaS evolution analytics | VENDOR-ONLY | Vendor SaaS callers need this exact handler; do NOT delete |
| 14 | `handlers/shinka.py` | 54-74 | `task_shinka_load_and_resolve` → `_load_state + _resolve_cadence` | RESOLVED M1: `_resolve_cadence` is a **pure function** — no RW access. Inputs: `ShinkaState{now_ms, last_heartbeat_ms, mood}`. Computes `elapsed_ms = max(0, now_ms - last_heartbeat_ms)`, then calls `_cadence_flags(mood, elapsed_ms)`. Returns 5 boolean flags: `should_post / should_engage / should_drill / should_validate / should_analyze`. Policy: mood × elapsed threshold table (joyful→post≥30min; calm→post≥2h; stressed→post=OFF; grateful→post≥1h; focused→post≥3h; neutral→post≥2h). New-actor default: mood="neutral", axes={joy:40,calm:40,stress:20,gratitude:30,focus:40}. `_load_state` is NOT portable (RW-backed), but `_resolve_cadence` + `_cadence_flags` can be ported as pure Python. | VENDOR-ONLY (task_shinka_load_and_resolve handler stays vendor); `_resolve_cadence` algorithm is PORT-adapted into `CadencePolicy` dataclass in `shinka_murakumo.py` | _load_state reads vertex_joucho + vertex_actor_shinka_state via RW; religious-corp reads from MST |
| 15 | `handlers/shinka.py` | 104-120 | `task_shinka_write_heartbeat` → `_write_heartbeat` | VENDOR-ONLY — keep for vendor SaaS; religious-corp uses `ShinkaHeartbeatCell` | VENDOR-ONLY | Vendor heartbeat writes to RisingWave; religious-corp writes to MST |
| 16 | `handlers/shinka.py` | 123-145 | `task_shinka_emit_evolution` → `_emit_evolution` | VENDOR-ONLY — keep for vendor SaaS; religious-corp uses `EvolutionEmissionCell` | VENDOR-ONLY | Vendor evolution writes to RisingWave; religious-corp writes to MST + IPFS + Base L2 |

---

## Known Intentional Remainders

The following vendor files are **intentionally kept intact** and must NOT be modified during the
Step 8 shinka cutover:

| File | Reason | Owner |
|---|---|---|
| `handlers/shinka.py` (entire file) | Vendor paid SaaS evolution analytics callers rely on `task_shinka_tick`, `task_shinka_load_and_resolve`, `task_shinka_write_heartbeat`, `task_shinka_emit_evolution` | Gftd Japan 株式会社 (vendor) |
| `primitives/shinka.py` (entire file) | Python handler that wraps `shinka_tick_actor` SQL UDF for vendor K8s LangServer pods | Gftd Japan 株式会社 (vendor) |
| `langgraph_graphs/shinka_cron_tick.py` (entire file) | Vendor K8s CronJob LangGraph graph; vendor K8s infra continues to drive this | Gftd Japan 株式会社 (vendor) |

The `shinka_tick_actor` SQL UDF in RisingWave is the vendor-canonical implementation for paid SaaS
evolution analytics. It has no religious-corp equivalent and will not be retired from vendor
infrastructure at Step 8.

---

## Cutover Procedure (when Step 8 fires)

Step 8 fires after legal registration (`amanomibashira` → `etzhayyim` registry change) and the 220-file
sed cutover (CLAUDE.md status table). The shinka-specific actions within Step 8 are:

1. **Verify M4 complete**: confirm the four Pregel cells (ports 13023-13026) are passing health checks
   on levi and simeon. Run the M4 e2e test against a live test adherent DID.

2. **Add `ETZHAYYIM_BUILD=1` import guard** to `handlers/shinka.py` and `primitives/shinka.py` — these
   files stay in the repo but must short-circuit with a clear error if accidentally imported in a
   religious-corp runtime context:
   ```python
   import os
   if os.environ.get("ETZHAYYIM_BUILD"):
       raise ImportError(
           "handlers/shinka.py is vendor-only. "
           "Use shinka_murakumo.py for religious-corp substrate."
       )
   ```

3. **Update `magatama-cell-runner` node config**: add the four shinka cell entries to
   `50-infra/murakumo/fleet.toml` if not already added at M3:
   - `KarmaHegemonObservationCell` on levi (port 13023)
   - `EvolutionValidationCell` on levi (port 13024)
   - `EvolutionEmissionCell` on simeon (port 13025)
   - `ShinkaHeartbeatCell` on levi (port 13026)

4. **Deploy `shinka_murakumo.py`** full M2 implementation to `levi` and `simeon` via the standard
   cell deploy path (`magatama-cell-runner --node levi --cell KarmaHegemonObservationCell`).

5. **Author and register the 6 new lexicons** (from ADR-2605215200 §3) in
   `00-contracts/lexicons/ai/gftd/apps/etzhayyim/shinka/` and run the PDS lexicon bundle regeneration
   step (see CLAUDE.md LLM Coding Guardrails: "新 Lexicon 追加後に PDS bundle 未再生成").

6. **Run end-to-end validation**: trigger a manual shinka tick against a test adherent DID. Verify
   that `evolutionEvent` appears in MST, the IPFS CID is pinned on `simeon`, and the Base L2 anchor
   tx hash is returned.

7. **Mark `shinka-mst-rewrite` as `completed`** in `deps.toml`.

8. **Update AUDIT-RUNPOD-RW-2026-05-21.md §2** to reflect RESOLVED status for all 8 REIMPLEMENT
   findings.

---

---

## Vendor Behaviour Appendix (M1 deep-dive, 2026-05-21)

Resolved by reading vendor source at commit HEAD on 2026-05-21. Source path:
`/Users/junkawasaki/github/ai-gftd-apps-gftdcojp/20-actors/magatama/py/src/pymagatama/shinka/__init__.py`
(495 LOC) and `llm.py` (180+ LOC). Files inspected (LOC):

| File | LOC | Notes |
|---|---|---|
| `pymagatama/shinka/__init__.py` | 495 | Core graph nodes: `_load_state`, `_resolve_cadence`, `_cadence_flags`, `_classify_mood`, `_kyumei_gather`, `_koji_validate`, `_shinka_analyze`, `_compose_content`, `_write_heartbeat`, `_emit_evolution`, `run_tick` |
| `pymagatama/primitives/shinka.py` | 146 | Task handler wrappers around `pymagatama.shinka` functions |
| `pymagatama/handlers/shinka.py` | 146 | LangServer HTTP handlers (vendor SaaS only) |
| `pymagatama/langgraph_graphs/shinka_cron_tick.py` | 73 | LangGraph StateGraph (START → shinka_tick → END) |
| `pymagatama/llm.py` | 180+ | LLM tier abstraction, backend routing |

### A1. `_resolve_cadence` — fully resolved

**Return shape**: mutates `ShinkaState` in-place, returns updated state dict. Adds 5 boolean keys:
`should_post`, `should_engage`, `should_drill`, `should_validate`, `should_analyze`.
Also sets `actions: []` (reset at start of each tick).

**Pure function**: no RW access. Inputs are `state["now_ms"]`, `state["last_heartbeat_ms"]`, `state["mood"]`.

**Policy table** (`elapsed_ms` = `now_ms - last_heartbeat_ms`; thresholds in minutes):

| mood | should_post | should_engage | should_drill | should_validate | should_analyze |
|---|---|---|---|---|---|
| joyful (joy≥60) | ≥30m | ≥15m | OFF | OFF | ≥60m |
| calm (calm≥60) | ≥120m | ≥60m | OFF | ≥120m | ≥60m |
| stressed (stress≥70) | OFF | OFF | ≥30m | ≥60m | OFF |
| grateful (gratitude≥60) | ≥60m | ≥10m | OFF | OFF | ≥60m |
| focused (focus≥60) | ≥180m | OFF | ≥60m | ≥120m | ≥30m |
| neutral (default) | ≥120m | ≥60m | ≥120m | ≥120m | ≥60m |

**Mood classification** (`_classify_mood`, priority order): stress≥70 → joyful(joy≥60) → calm(calm≥60) → grateful(gratitude≥60) → focused(focus≥60) → neutral.

**New-actor edge case**: `_load_state` assigns `axes={joy:40, calm:40, stress:20, gratitude:30, focus:40}` and `mood="neutral"` when no `vertex_joucho` row exists. `last_heartbeat_ms=None` → `last=0` → `elapsed=now_ms` (very large) → all time-based flags fire on first tick.

**Religious-corp note**: The algorithm is portable as a pure function. Implement as `_resolve_cadence(state: AdherentState) -> CadencePolicy` in `shinka_murakumo.py`. MST-backed `last_heartbeat_ms` replaces RW-backed value.

### A2. `_compose_content` — fully resolved

**Content type**: Bluesky-style short text post (≤280 chars). Draft is NOT posted from here — stored in `vertex_shinka_evolution.props.draft` for later promotion by a separate dispatcher job (PDS auth keys not available in the UDF pod).

**Guard**: only fires when `state["should_post"]` is True.

**Inputs** (from `ShinkaState`):
- `mood: str` — current joucho mood
- `axes: JouchoAxes` — `{joy, calm, stress, gratitude, focus}` int values
- `actions: list[str]` — actions taken earlier in this tick (e.g. `["kyumei", "shinka_analyze"]`)
- `follower_delta_count: int` — commits from followers in last 1h

**LLM coupling**:
- Calls `llm.call_tier_json("classifier", system=..., user=..., max_tokens=200, temperature=0.7)`
- Tier "classifier" routes via `TIER_ENDPOINT_OVERRIDES["classifier"]` → **vendor OpenRouter** by default (`deepseek/deepseek-chat` or `GFTD_LLM_URL`/`GFTD_LLM_MODEL` env override)
- **ADR-2605215000 violation if used verbatim**: religious-corp MUST use EVO-X2 LiteLLM, not vendor OpenRouter/Vultr
- **Vendor prompt NOT copied here** per task constraints. Religious-corp must write its own prompt.

**Output schema** (`compose_draft` field in state):
```
{
  "text":      str,    # post body, ≤300 chars (truncated from LLM output)
  "tone":      str,    # one of: reflective / celebratory / grateful / focused / observational
  "model":     str,    # LLM model ID used (from result["model"])
  "latencyMs": int,    # LLM round-trip latency
  "attempts":  int,    # retry count (from result["attempts"])
}
```
On LLM error: `compose_draft = {"error": ..., "attempts": ...}`, action `"compose_failed"` appended.
On success: action `"compose_draft"` appended.

**Religious-corp port**: The output schema is portable. Replace `llm.call_tier_json` with EVO-X2 LiteLLM call. Write a new prompt that expresses the religious-corp joucho mood context. Keep the same `compose_draft` field names for EvolutionEventRecord interop.

### A3. `axes` dict schema — fully resolved

**Type**: `JouchoAxes(TypedDict, total=False)` — all fields optional integers.

**Fields** (5 axes, all `int`, all optional, default 0 if absent):
```python
class JouchoAxes(TypedDict, total=False):
    joy:       int   # 0-100
    calm:      int   # 0-100
    stress:    int   # 0-100 (inverted — high = bad)
    gratitude: int   # 0-100
    focus:     int   # 0-100
```

**Source**: read from `vertex_joucho` table (`SELECT mood, joy, calm, stress, gratitude, focus FROM vertex_joucho WHERE owner_did = %s ORDER BY created_at DESC LIMIT 1`).

**Thresholds**: each axis has a single threshold (not cumulative, not weighted):
- joy ≥ 60 → joyful mood
- calm ≥ 60 → calm mood
- stress ≥ 70 → stressed mood (overrides all others — checked first)
- gratitude ≥ 60 → grateful mood
- focus ≥ 60 → focused mood
- otherwise → neutral

**New-adherent defaults** (no `vertex_joucho` row): `{joy:40, calm:40, stress:20, gratitude:30, focus:40}` → neutral mood.

**Mapping to `app.etzhayyim.shinka.kyumeiSignal.signalKind`**:

The vendor `axes` are emotional/attentional states emitted by joucho; they are NOT the same as kyumeiSignal kinds. They map to religious-corp equivalents as follows:

| Vendor axis | Religious-corp signal influence | kyumeiSignal.signalKind |
|---|---|---|
| `joy` | Driven by `ritual` participation and `kuniUmi-witness` events | `ritual` / `kuniUmi-witness` |
| `calm` | Driven by `oath` fulfilment and governance participation | `oath` / `governance-participation` |
| `stress` | Counter-signal: high `stress` inhibits post/engage; maps to governance blockers | `governance-participation` (negative) |
| `gratitude` | Driven by `contribution` acknowledgement | `contribution` |
| `focus` | Driven by deep `oath` practice and `contribution` work | `oath` / `contribution` |

**Religious-corp `AdherentState.axes` field**: the existing `axes: dict[str, Any]` field in `AdherentState` covers this. Add type annotation via new `JouchoAxes`-equivalent dataclass per A4 below.

**Confirmed**: the `app.etzhayyim.shinka.kyumeiSignal.signalKind` enum (`ritual / oath / contribution / governance-participation / kuniUmi-witness`) covers all 5 axes with no extension needed. `stress` has no direct positive signal kind — it is an inhibitor derived from absence of positive signals.

---

## Do Not

- **Do not** add backward-compat shims that call `shinka_tick_actor` SQL UDF from `shinka_murakumo.py`.
  The religious-corp and vendor implementations are parallel paths, not layered.
- **Do not** delete `handlers/shinka.py` or `primitives/shinka.py` at Step 8. They remain for vendor
  SaaS callers. Only add the `ETZHAYYIM_BUILD=1` import guard.
- **Do not** rename any file in this migration without updating both `deps.toml` and ADR-2605215200.
- **Do not** attempt Step 8 before M4 is verified — the full four-cell Pregel super-step must be
  passing e2e tests before any vendor path is guarded.
- **Do not** copy `RW_URL`, psycopg3, or `sync_cursor` into `shinka_murakumo.py`. The substrate-fit
  invariant check in `shinka_murakumo.py` will `raise ImportError` on RW/RunPod environment detection.
