# bpmn-engine-host — Cluster Apply Runbook

ADR 2605081200 PoC Phase 1。**1 回限りの初回 apply 用**。Roll-forward / rollback
手順は最後に。冪等性は各 step で `kubectl apply` / `IF NOT EXISTS` に依存。

## Pre-flight (operator 必須)

```bash
# from repo root
bash 50-infra/k8s/bpmn-engine-host/preflight.sh
```

すべて green でないと先に進まない。red 時の対処は preflight.sh 出力に記載。

## Step 1: Schema migration (Kotoba/Datomic)

`r_20260509110000_vertex_spiff_runtime` は Spiff runtime 層の 4 vertex table +
1 streaming MV を作る。Heavy DDL queue 不要のサイズ (各 table cardinality 数千、
MV は status filter のみ、GROUP BY なし) — 直接 alembic 経由で OK。
ただし `50-infra/CLAUDE.md` "Kotoba/Datomic Smooth Scaling Gate" の `rw-health-gate.sh`
は走らせる:

```bash
70-tools/scripts/ingest/rw-health-gate.sh   # 既知の incident hint がない事を確認
KOTOBA_URL="http://127.0.0.1:8077" \ # EXAMPLE
  cd 30-graph/graph-schema && pnpm db:migrate
```

成功条件:
- `alembic_version` の head が `r_20260509110000_vertex_spiff_runtime`
- `vertex_spiff_{instance,job,timer,history}` + `mv_spiff_ready_jobs` が `\dt+` で見える
- 既存 `vertex_bpmn_instance` (Zeebe shape) は **無変更**

```bash
DATABASE_URL=... pnpm db:gen && pnpm db:drift  # 0 drift 必須
```

## Step 2: Image build (BuildKit remote)

```bash
TS=$(date -u +%Y%m%d-%H%M%S)
# bpmn-engine-host (build context = this directory)
70-tools/scripts/buildkit/remote-build.sh \
  -d 50-infra/k8s/bpmn-engine-host \
  -t "ghcr.io/etzhayyim/bpmn-engine-host:${TS}"

# open-lei-mcp (build context = REPO ROOT — vendors pymagatama spiff_worker)
70-tools/scripts/buildkit/remote-build.sh \
  -f 50-infra/k8s/open-lei-mcp/Dockerfile \
  -d . \
  -t "ghcr.io/etzhayyim/open-lei-mcp:${TS}"
```

YAML の `image: ghcr.io/etzhayyim/...:latest` を実 tag に書き換えるか、
`kubectl set image` で patch する (latest tag は不変性保証なし、production 非推奨):

```bash
sed -i.bak "s|bpmn-engine-host:latest|bpmn-engine-host:${TS}|" \
  50-infra/k8s/bpmn-engine-host/deployment.yaml
sed -i.bak "s|open-lei-mcp:latest|open-lei-mcp:${TS}|" \
  50-infra/k8s/open-lei-mcp/deployment-spiff-worker.yaml
```

## Step 3: Secrets

```bash
# KOTOBA_URL を macOS Keychain から取得して mitama-udf namespace に注入
KOTOBA_URL_VALUE="$(security find-generic-password -s etzhayyim.kotoba -a KOTOBA_URL -w)"
printf '%s' "$KOTOBA_URL_VALUE" | kubectl create secret generic bpmn-engine-host-secrets \
  -n mitama-udf --from-file=KOTOBA_URL=/dev/stdin --dry-run=client -o yaml | kubectl apply -f -
```

## Step 4: Engine host + timer reconciler

```bash
kubectl apply -f 50-infra/k8s/bpmn-engine-host/deployment.yaml
kubectl apply -f 50-infra/k8s/bpmn-engine-host/cronjob-timer-tick.yaml
kubectl -n mitama-udf rollout status deploy/bpmn-engine-host --timeout=120s

# Sanity
kubectl -n mitama-udf port-forward svc/bpmn-engine-host 8080:80 &
PF_PID=$!
curl -fsS http://localhost:8080/healthz
curl -fsS http://localhost:8080/readyz
kill $PF_PID
```

## Step 5: open-lei spiff worker

```bash
kubectl apply -f 50-infra/k8s/open-lei-mcp/deployment-spiff-worker.yaml
kubectl -n open-lei rollout status deploy/open-lei-spiff-worker --timeout=120s
kubectl -n open-lei logs deploy/open-lei-spiff-worker --tail=20
# 期待: "spiff_worker: starting worker_id=... task_types=['gleif.collect', ...]"
```

## Step 6: Smoke (low-concurrency first)

```bash
kubectl -n mitama-udf port-forward svc/bpmn-engine-host 8080:80 &
PF_PID=$!
KOTOBA_URL="$KOTOBA_URL_VALUE" BPMN_ENGINE_URL=http://localhost:8080 \
  python3 50-infra/k8s/bpmn-engine-host/tests/smoke.py \
  --process-id lawfirm_intake_funnel --concurrency 3 --timeout-s 60
# JSON exit code 0 なら次へ。失敗時は kubectl logs を確認

# 100 並行 (acceptance test)
KOTOBA_URL="$KOTOBA_URL_VALUE" BPMN_ENGINE_URL=http://localhost:8080 \
  python3 50-infra/k8s/bpmn-engine-host/tests/smoke.py \
  --process-id lawfirm_intake_funnel --concurrency 100 --timeout-s 60 \
  --p95-budget-s 30
kill $PF_PID
```

Acceptance p95 is the DB-clock duration from `instance_started` history
to `vertex_spiff_instance.completed_at`. `observed_p95_s` is runner-side
polling/read visibility latency and is diagnostic only.

Verified on 2026-05-09:

- `bpmn-engine-host`: `ghcr.io/etzhayyim/bpmn-engine-host:20260509-1705no-inline-cache`
- `lawfirm-spiff-worker`: `ghcr.io/etzhayyim/lawfirm-spiff-worker:20260509-0250inline-default4`
- c100 smoke: `completed=100`, `p95_s=10.888`,
  `history_violations=[]`, `orphan_violations=[]`

## Step 7: Restart drill (replay 検証)

```bash
KOTOBA_URL="$KOTOBA_URL_VALUE" BPMN_ENGINE_URL=http://localhost:8080 \
  python3 50-infra/k8s/bpmn-engine-host/tests/smoke.py --concurrency 100 --timeout-s 180 &
SMOKE_PID=$!
sleep 10
kubectl -n mitama-udf delete pod -l app.kubernetes.io/name=bpmn-engine-host
wait $SMOKE_PID  # exit code 0 なら replay OK
```

Verified on 2026-05-09 with the same images: engine pod delete during c100
smoke completed `100/100`, `p95_s=12.861`, `history_violations=[]`,
`orphan_violations=[]`.

## Rollback

```bash
# 1. Worker stop (cron path は無関係、生かす)
kubectl -n open-lei delete -f 50-infra/k8s/open-lei-mcp/deployment-spiff-worker.yaml

# 2. Engine host stop
kubectl -n mitama-udf delete -f 50-infra/k8s/bpmn-engine-host/deployment.yaml

# 3. Schema rollback (orphan rows なし or 受容できる場合のみ)
DATABASE_URL=... cd 30-graph/graph-schema && \
  pnpm db:migrate:downgrade -- -1   # 1 revision 戻す

# 既存 Zeebe path は不変、`mcp_server.py` も BPMN_ENGINE_URL を unset すれば
# 自動で ZEEBE_GATEWAY fallback に戻る。
```

## Known caveats

- **lawfirm BPMN corpus**: 14 中 7 のみ engine boundary 通過。残り 7 は BPMN
  モデル側 cleanup (sequenceFlow 欠落 / ISO 8601 cycle) が必要。Smoke は
  `lawfirm_intake_funnel` (通る側) で実施
- **Spec cache invalidation**: BPMN の redeploy 後、engine pod に
  `POST /v1/process/{id}/reload` を叩く必要。RW change-data subscribe は
  Phase 2
- **`gleif.collect` handler**: 分単位の HTTP fetch を実行。lease を 120s に
  設定済 (deployment-spiff-worker.yaml)。それを超える GLEIF API 詰まり時は
  worker pool が同 job を再 claim する可能性あり (engine の idempotent
  `complete_job` で保護)
