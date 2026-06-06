---
id: doc-260425-gameka-operator-runbook
title: "gameka.etzhayyim.com operator runbook (P1–P14)"
status: active
doc_type: how-to
topic: gameka-rollout
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - gameka-operator-rollout
  - gameka-deployment-order
  - gameka-smoke-test
related:
  - adr-2604250900-gameka-bpmn-langgraph-game-studio
  - adr-2604250836-langgraph-as-zeebe-servicetask
  - adr-0056-bpmn-as-actor
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0023-auth-shannon-optimal-4-layer
---

# gameka.etzhayyim.com operator runbook

A single page covering every step needed to bring `gameka.etzhayyim.com`
online from a clean repo. Authoritative for the rollout order;
ADR 2604250900 owns the design rationale.

## Phase index (P1–P14)

| # | What | Live deliverable |
|---|---|---|
| P1  | Ideate (LangGraph 5-node studio)             | `proposeGame.bpmn` + `agents/gameka_studio.py` |
| P2  | Codegen (kami-app-{slug} sources)             | `gameka.codegen.renderKamiApp` task type |
| P3  | wasm-pack runner pod                          | `50-infra/vultr/gameka-build-runner/` |
| P4  | Visual + perf QA loop                         | `playtestGame.bpmn` + `agents/gameka_visual_critic.py` |
| P5  | Playtest shell HTML + `js_url` migration      | `gameka-playtest-shell` Worker + 20260425100000 |
| P6  | Publish (sub-DID + title + profile + post)    | `publishGame.bpmn` |
| P7  | Autonomous tick (R/PT2H, 14-day soak)         | `tickStudio.bpmn` + `vertex_gameka_studio_config` |
| P9  | Audio (4 BGM drone + 13 SFX synth presets)    | shell `SFX_PRESETS` + lib.rs `play_sfx`/`start_bgm` |
| P10 | Procedural avatar                             | `gameka.avatar.render` task + 20260425130000 |
| P11 | In-game share/follow UI                       | shell social-bar + Worker URL injection |
| P12 | Rollout sanity lint                           | `70-tools/scripts/lint/lint-gameka-rollout.mjs` |
| P13 | Real merge mechanics (3 state machines)       | `gameka_codegen.py` `_MECHANIC_TEMPLATES` |
| P14 | Mechanic DOM overlay (kami-engine compliant)  | shell `MECHANIC_RENDERERS` |

(P8 is reserved for the bsky-AppView routing follow-up; not required
for the gameka pipeline.)

## Prerequisites

The shared platform must already be running:

| Component | Owner | Notes |
|---|---|---|
| `atproto.etzhayyim.com` (PDS Worker) | infra | NSID routing table reads gameka entries |
| `dispatcher.etzhayyim.com:8080` (bpmn-dispatcher) | infra | `BPMN_URL` binding in PDS Worker |
| Zeebe broker (`zeebe-gateway.mitama-udf.svc:26500`) | infra | shared with yabai/yoro/etc. |
| `mitama-udf` namespace zeebe-worker pod | infra | rebuild on each gameka task addition |
| Kotoba/Datomic + Hyperdrive `e84c0a2b…` | infra | shared graph DB |
| Backblaze B2 account + Bandwidth Ally enabled | infra | `B2_*` Secrets reused from patent-blob-converter |
| Murakumo LLM tier | infra | yoro / news already use it |
| `playwright` actor (Layer-10 Worker) | apps | QA loop's `goto`/`evaluate`/`screenshot` |
| `authn.etzhayyim.com` with sub-DID provisioning NSID | apps | the **only** operator hook (see §Hook 1) |

## Operator hooks (the only 2 things you must wire by hand)

### Hook 1 — `com.etzhayyim.authz.provisionSubDid`

`publishGame.bpmn` `Task_ProvisionSubDid` calls
`com.etzhayyim.authz.provisionSubDid` with input
`{ parentDid, path, displayName, description }` and expects
`output.did`. If your authn surface uses a different NSID, swap the
literal in `publishGame.bpmn` — everything downstream consumes the
returned `subDid` string.

### Hook 2 — flip tickStudio live (day +14)

The migration `20260425110000_vertex_gameka_studio_config.ts` seeds
`tick_live_mode=false`. Every R/PT2H tick logs a dryRun audit.
After 14 days of clean dryRun audits, run:

```sql
INSERT INTO vertex_gameka_studio_config (
  vertex_id, owner_did, rkey, repo,
  config_id, tick_live_mode, max_iterations, score_threshold,
  note, created_at
) VALUES (
  'at://did:web:gameka.etzhayyim.com/com.etzhayyim.gameka.studioConfig/global',
  'did:web:gameka.etzhayyim.com', 'global', 'did:web:gameka.etzhayyim.com',
  'global', true, 3, 0.8,
  'P7 cutover', NOW()::text
);
```

(RW PK-upsert — same `vertex_id` overwrites in place. Hard rollback
is the same INSERT with `false`.)

## Rollout order — fresh repo to live

Every step is idempotent except secret creation; re-running is safe.

```bash
REPO=/path/to/etzhayyim-root
DATABASE_URL=$(security find-generic-password -s etzhayyim.rw -a ROOT_URL -w)

# ── 0. lint baseline ───────────────────────────────────────────
node $REPO/70-tools/scripts/lint/lint-gameka-rollout.mjs
# expect: ✓ gameka rollout invariants intact

# ── 1. apply migrations (5 timestamp files, 20260425090000-130000) ──
cd $REPO/30-graph/graph-schema
DATABASE_URL=$DATABASE_URL pnpm db:migrate latest
DATABASE_URL=$DATABASE_URL pnpm db:gen
DATABASE_URL=$DATABASE_URL pnpm db:drift

# ── 2. sync BPMN registry rows ─────────────────────────────────
python3 $REPO/70-tools/scripts/contract/sync-bpmn-actors.py --apply --only gameka
# expect: 5 rows touched (proposeGame / generateGame / playtestGame /
#                         publishGame / tickStudio)

# ── 3. provision Secrets for the wasm-pack runner pod ──────────
kubectl create secret generic gameka-runner-b2 -n mitama-udf \
  --from-literal=B2_KEY_ID="$(security find-generic-password -s etzhayyim.r2 -a ACCESS_KEY_ID -w)" \
  --from-literal=B2_APPLICATION_KEY="$(security find-generic-password -s etzhayyim.r2 -a SECRET_ACCESS_KEY -w)" \
  --from-literal=B2_BUCKET=etzhayyim-gameka \
  --from-literal=B2_ENDPOINT=https://s3.us-west-004.backblazeb2.com \
  --from-literal=B2_REGION=us-west-004
kubectl create secret generic gameka-runner-runtime -n mitama-udf \
  --from-literal=ZEEBE_ADDRESS=zeebe-gateway.mitama-udf.svc:26500
b2 bucket create etzhayyim-gameka allPrivate

# ── 4. build + push the wasm-pack runner image ─────────────────
cd $REPO
docker build -f 50-infra/vultr/gameka-build-runner/Dockerfile \
  -t ghcr.io/etzhayyim/gameka-build-runner:$(date +%Y%m%d-%H%M%S) \
  -t ghcr.io/etzhayyim/gameka-build-runner:latest .
docker push ghcr.io/etzhayyim/gameka-build-runner:latest
kubectl apply -f 50-infra/vultr/gameka-build-runner/deployment.yaml

# ── 5. rebuild + roll the zeebe-worker pod (registers 4 task types) ──
# com.etzhayyim.agent.gameka.studio
# com.etzhayyim.agent.gameka.visualCritic
# gameka.codegen.renderKamiApp
# gameka.avatar.render
cd $REPO/20-actors/magatama/py
docker build -t ghcr.io/etzhayyim/zeebe-worker:$(date +%Y%m%d-%H%M%S) \
              -t ghcr.io/etzhayyim/zeebe-worker:latest .
docker push ghcr.io/etzhayyim/zeebe-worker:latest
kubectl rollout restart deployment/zeebe-worker -n mitama-udf

# ── 6. deploy the playtest-shell Worker (claims game-play.etzhayyim.com/play/* + /__playtest__.html) ──
cd $REPO/50-infra/cloudflare/workers/gameka-playtest-shell
pnpm install
pnpm typecheck
pnpm deploy

# ── 7. deploy the PDS routing-table update (5 gameka NSIDs → BPMN_URL) ──
cd $REPO/50-infra/cloudflare/workers/atproto
pnpm test  # 16/16 routing-table tests must pass
pnpm deploy

# ── 8. wire your authn surface for com.etzhayyim.authz.provisionSubDid ──
# (see §Hook 1)

# ── 9. final lint after live ──────────────────────────────────
node $REPO/70-tools/scripts/lint/lint-gameka-rollout.mjs
```

## Smoke tests

### Smoke 1 — the studio loop (P1 only, no build)

```bash
curl -X POST https://atproto.etzhayyim.com/xrpc/com.etzhayyim.gameka.proposeGame \
  -H "authorization: Bearer $etzhayyim_TOKEN" \
  -H "content-type: application/json" \
  -d '{"brief":"a cozy quarry-walk roguelike with one weather rune"}'
```

Expect within ~60s: 1 row in `vertex_gameka_spec` with `score >= 0`.

### Smoke 2 — generate from a seed merge spec (P2 + P3)

```bash
SPEC=spec-merge-grid-2048   # or spec-merge-drop-suika / spec-merge-field-triple
curl -X POST https://atproto.etzhayyim.com/xrpc/com.etzhayyim.gameka.generateGame \
  -H "authorization: Bearer $etzhayyim_TOKEN" \
  -d "{\"specId\":\"$SPEC\"}"
```

Expect within ~5 min (cold sccache):
- `vertex_gameka_artifact -sources` row (`build_status=sources_ready`)
- `vertex_gameka_artifact -built`   row (`build_status=built`, `wasm_url` non-empty, `js_url` non-empty)

### Smoke 3 — full chain via tickStudio

Manual fire of the autonomous tick (skips the 2h timer):

```bash
curl -X POST https://atproto.etzhayyim.com/xrpc/com.etzhayyim.gameka.tickStudio \
  -H "authorization: Bearer $etzhayyim_TOKEN" -d '{}'
```

In dry-run mode (default seed): 1 audit row `gameka.tick.dryRun`, no
spec / artifact / qa / title written.
After cutover (Hook 2): 1 spec row + the full ideate→publish chain
fires asynchronously over the next ~5-15 min.

### Smoke 4 — manual end-user play page

```bash
curl -I https://game-play.etzhayyim.com/play/grid-merge-quarry
# expect: 302 Found, Location: /__playtest__.html?c=…&w=…&j=…&e=run_grid_merge_quarry&d=did:web:gameka.etzhayyim.com:game:grid-merge-quarry&t=ttl…&a=data:image/png;base64,…

curl -I 'https://game-play.etzhayyim.com/__playtest__.html'
# expect: 200, content-type: text/html

# Pull the page in a browser and verify:
#  - kami-pipelines biome scene renders (Sky+Terrain+Water)
#  - Splatoon-pastel mechanic stage overlay (top-left)
#    - grid_2048: 4×4 swipe board, arrow keys swipe + merge
#    - drop_suika: jar with bouncing balls, click top to drop
#    - field_triple: 5×5 board with rank labels, click empty cell
#  - in-game share/follow pills (bottom-right)
#  - audio: BGM drone + SFX on click/swipe (after first user gesture)
#  - avatar in browser tab favicon
```

## Failure-mode index

| Symptom | Probable cause | Fix |
|---|---|---|
| `proposeGame` returns 501 | PDS routing-table missing the gameka NSID | redeploy PDS Worker; rerun lint |
| `404 title not found: {slug}` on `/play/{slug}` | publishGame hasn't run for this slug yet | check `vertex_gameka_title`; if empty, run smoke 2 then publishGame |
| `404 built artifact missing for slug=…` | spec was published but no `-built` artifact row | wasm-pack runner failed; tail `kubectl logs -n mitama-udf -l app.kubernetes.io/name=gameka-build-runner`; rerun generateGame |
| `wasm-pack: not found` (rc=127) | runner image broken | rebuild + push (P3 step 4) |
| `Killed` during build | memory pressure | bump `resources.limits.memory` in `deployment.yaml` |
| All builds time out at 600s | cold sccache + 250-dep cargo build | bump `WASM_PACK_TIMEOUT_SEC` env to 1200 once, let cache warm, drop back |
| `pkg/*.wasm missing` after rc=0 | wasm-bindgen output target mismatch | pin wasm-pack version in Dockerfile |
| All ticks fire `gameka.tick.briefError` | Murakumo LLM tier down | check yoro/news to confirm Murakumo health; tickStudio retries automatically each 2h |
| All visual critic verdicts are `degraded-no-vision` | LLM `tier="vision"` not configured | set `LLM_VISION_TIER=…` in zeebe-worker env or wire vision endpoint; until then the critic falls back to score=0.5 |
| `502 backend error` from playtest-shell | Hyperdrive / Kotoba/Datomic unreachable | check RW health: `kubectl logs -n kotoba …`; B2 SlowDown 503 storm? see `50-infra/vultr/kotoba/deps.toml` |
| `400 invalid slug` from /play/{slug} | slug doesn't match `[a-z0-9-]{1,32}` | publish path produced an unexpected slug — investigate codegen `_slug()` |
| Visual critic publishes nothing for 3 iterations | spec is fundamentally broken | the chain ends with `outcome=exhausted`, lineage stays in graph for post-mortem |
| `gameka.tick.live` fires but no spec row | LangGraph studio LLM error | check `vertex_repo_commit WHERE collection='com.etzhayyim.bpmn.audit'` for `briefError` events |
| `gameka.title.published` audit shows empty `launchPostUri` | sub-DID provisioned but firehose post failed | manual fix: re-emit the post with the title's `subDid`; provisioning has already succeeded |

## Per-phase ownership map

| Phase | Code path | Tests | Lint coverage |
|---|---|---|---|
| P1  | `agents/gameka_studio.py` | `tests/test_gameka_studio.py` (offline LLM stub) | rollout lint §5 |
| P2  | `handlers/gameka_codegen.py` | `tests/test_gameka_codegen.py` (33 tests) | §3 §5 |
| P3  | `50-infra/vultr/gameka-build-runner/` | smoke only | §6 |
| P4  | `agents/gameka_visual_critic.py` | `tests/test_gameka_visual_critic.py` | §5 |
| P5  | `gameka-playtest-shell/src/worker.ts` | inline TS + `pnpm typecheck` | §7 |
| P6  | `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/gameka/publishGame.bpmn` | rollout lint NSID match | §1 §2 |
| P7  | `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/gameka/tickStudio.bpmn` + 20260425110000 | rollout lint | §1 §2 §3 |
| P10 | `handlers/gameka_avatar.py` + 20260425130000 | `tests/test_gameka_avatar.py` (13 tests) | §3 §5 |
| P11 | `gameka-playtest-shell/static/__playtest__.html` social-bar | manual browser smoke | §7 column round-trip |
| P12 | `70-tools/scripts/lint/lint-gameka-rollout.mjs` | n/a — IS the test | gates all others |
| P13 | `handlers/gameka_codegen.py` `_MECHANIC_TEMPLATES` | 10 P13 tests | §5 |
| P14 | `gameka-playtest-shell/static/__playtest__.html` MECHANIC_RENDERERS | manual browser smoke | §7 |

## CI

`.github/workflows/gameka-rollout-lint.yml` runs on every PR touching
gameka paths. Four steps, ~30s on a fresh runner:

1. `lint-gameka-rollout.mjs` (the 7-section P12 sweep)
2. AST-parse all 8 gameka Python files (`handlers/gameka_*.py` + `agents/gameka_*.py` + `tests/test_gameka_*.py` + `zeebe_worker_main.py`)
3. Run all `test_gameka_*` tests via a stdlib-only runner that stubs `pytest.skip` / `pytest.raises` (53 tests, 14 skip when langgraph isn't installed in the runner — those run separately in the zeebe-worker image build)
4. Parse `__playtest__.html` for well-formedness

Locally:

```bash
# Same 4 steps the workflow runs:
node 70-tools/scripts/lint/lint-gameka-rollout.mjs
python3 -c "import ast, glob; [ast.parse(open(p).read()) for p in sorted(glob.glob('20-actors/magatama/py/src/pymagatama/handlers/gameka_*.py') + glob.glob('20-actors/magatama/py/src/pymagatama/agents/gameka_*.py') + glob.glob('20-actors/magatama/py/tests/test_gameka_*.py') + ['20-actors/magatama/py/src/pymagatama/zeebe_worker_main.py'])]"
# Step 3 inline: see .github/workflows/gameka-rollout-lint.yml
python3 -c "import html.parser as h; \
  class V(h.HTMLParser):
    def __init__(s): super().__init__(); s.errs=[]
    def error(s,m): s.errs.append(m); \
  v=V(); v.feed(open('50-infra/cloudflare/workers/gameka-playtest-shell/static/__playtest__.html').read()); v.close(); assert v.errs == []"
```

## Cost notes

| Resource | Steady-state | Spike |
|---|---|---|
| zeebe-worker CPU | shared with yoro/yabai/news | tickStudio R/PT2H = 12 LLM calls/day; live mode = 12 spec lineages/day cap |
| Murakumo LLM | dryRun: 1 brief / 2h ≈ 12/day; live: + 3 deliberations + 1 critic per spec ≈ 60-80/day | iteration cap (3) prevents runaway |
| wasm-pack runner | idle most of the day; 5min/build cold, 30s warm sccache | live tickStudio ≈ 12 builds/day |
| B2 storage | 16-20 KB per build (wasm + glue) + 1-5 KB per avatar | 1 GB ≈ 25k builds; <$1/mo |
| Hyperdrive read | playtest-shell `/play/{slug}` 2 SELECTs per request | 60s CDN cache could be added if traffic grows |
| Kotoba/Datomic write | 1-2 rows per BPMN task; ~30 rows per full pipeline run | bounded by tickStudio cap |

## Decommission

If gameka needs to be archived:

1. Flip `tick_live_mode=false` (Hook 2 with `false`).
2. Wait for in-flight pipelines to drain (~15 min).
3. Drop the routing-table entries (5 lines) + redeploy PDS.
4. `kubectl scale deployment/gameka-build-runner -n mitama-udf --replicas=0`.
5. Leave migrations + lexicons in place for graph history (titles
   stay queryable; `/play/{slug}` 404s after the Worker is undeployed).

## Related

- ADR 2604250900 — design rationale for the 14-phase rollout
- ADR-0056 — BPMN-as-actor (the substrate gameka extends)
- ADR-2604250836 — LangGraph as Zeebe ServiceTask (the agentic spine)
- ADR-0036 — Worker-direct Hyperdrive persistence (write path)
- ADR-0023 — Auth Shannon-optimal 4-Layer (sub-DID custody)
- `60-apps/etzhayyim-project-gameka/CLAUDE.md` — per-phase deep-dive
- `50-infra/vultr/gameka-build-runner/README.md` — wasm-pack pod runbook
- `50-infra/cloudflare/workers/gameka-playtest-shell/README.md` — shell Worker runbook
