# Zeebe Decommission Runbook

ADR-2605081200 の SpiffWorkflow cutover 後に、Camunda Zeebe broker と
legacy pyzeebe worker path を停止するための手順。RW が安定し、Spiff smoke /
restart drill が green であることを前提にする。

## Do Not Start

以下のいずれかが真なら decommission しない。

- `bpmn-engine-host` `/readyz` が 200 ではない
- `lawfirm-spiff-worker` の ready replica が desired 未満
- `mv_spiff_ready_jobs` に古い ready/claimed job が残っている
- legacy pyzeebe worker Deployment / CronJob が active traffic を処理している
- Murakumo 側 `yoro-actor-zeebe-worker` がまだ VKE Zeebe LB に依存している
- rollback window 内に operator がいない

## Precheck

```bash
50-infra/vultr/zeebe/preflight-decommission.sh
```

Check Spiff queue drain:

```sql
SELECT status, count(*)
FROM graphar.vertex_spiff_job
GROUP BY status
ORDER BY status;
```

Expected: no unexpected `ready`, `claimed`, or long-lived `running` rows.

Check legacy Zeebe consumers:

```bash
kubectl get deploy,sts,cronjob -A -o wide | grep -Ei 'zeebe|pyzeebe|ZEEBE' || true
kubectl get svc -A | grep -Ei 'zeebe' || true
```

Everything found must be either intentionally retained out of scope or listed in
the stop plan below.

Latest preflight (2026-05-09 JST): Spiff rollouts, `/healthz`, `/readyz`, and
RW health gate passed, but legacy Zeebe workloads/services were still active
across `intel`, `mitama-udf`, `shinka-actors`, and `yoro-actors`, including
`mitama-udf/statefulset.apps/zeebe` and the public
`zeebe-murakumo-gateway` LoadBalancer. Broker deletion is blocked until those
consumers are migrated, disabled, or explicitly accepted as out of scope.

## Step 1: Stop Legacy pyzeebe Workers

Scale workers before broker deletion so no new broker work is activated.

```bash
helm upgrade mitama-udf-pool 50-infra/vultr/mitama-udf-pool \
  -n mitama-udf \
  --reuse-values \
  --set zeebeWorker.enabled=false
```

For manifest-only workers, scale explicitly:

```bash
kubectl -n mitama-udf scale deploy/zeebe-worker --replicas=0 --timeout=120s || true
kubectl -n mitama-chat scale deploy/chat-zeebe-worker --replicas=0 --timeout=120s || true
```

Murakumo/yoro workers are cross-cluster dependencies. Do not scale them until
their runtime registration no longer advertises `bpmn-zeebe` or their endpoint
has been moved to Spiff.

## Step 2: Observe Drain Window

Keep the broker running while old activations finish or expire.

```bash
kubectl -n mitama-udf logs statefulset/zeebe --tail=200
kubectl -n mitama-udf port-forward svc/zeebe-gateway 26500:26500 &
ZB_PF_PID=$!
zbctl status --address localhost:26500 --insecure
kill "$ZB_PF_PID"
```

Minimum drain window: one legacy worker timeout plus 10 minutes. If any
business-critical Zeebe process is still running, pause and migrate/replay that
flow through Spiff before continuing.

## Step 3: Remove External Zeebe Entry Points

Remove the Murakumo-reachable LoadBalancer first so new remote workers cannot
attach while local broker teardown proceeds.

```bash
kubectl delete -f 50-infra/vultr/zeebe/zeebe-murakumo-gateway-lb.yaml
```

Confirm no external service remains:

```bash
kubectl -n mitama-udf get svc | grep -Ei 'zeebe|26500' || true
```

`zeebe-gateway` ClusterIP may still exist until Step 4.

## Step 4: Stop Broker

```bash
kubectl delete -f 50-infra/vultr/zeebe/zeebe-simple-monitor.yaml --ignore-not-found=true
kubectl delete -f 50-infra/vultr/zeebe/zeebe.yaml
```

Confirm:

```bash
kubectl -n mitama-udf get sts,pod,svc,pvc | grep -Ei 'zeebe' || true
```

Do not delete the PVC in the first maintenance window. Keep it as rollback
state until Spiff has run through the next scheduled production cycle.

## Step 5: Postcheck

Run the Spiff acceptance smoke again:

```bash
kubectl -n mitama-udf port-forward svc/bpmn-engine-host 8080:80 &
PF_PID=$!
KOTOBA_URL="$KOTOBA_URL_VALUE" BPMN_ENGINE_URL=http://localhost:8080 \
  python3 50-infra/k8s/bpmn-engine-host/tests/smoke.py \
  --process-id lawfirm_intake_funnel \
  --concurrency 100 \
  --timeout-s 60 \
  --p95-budget-s 30
kill "$PF_PID"
```

Then verify no legacy clients are trying to reconnect:

```bash
kubectl logs -A --since=30m | grep -Ei 'zeebe|pyzeebe|26500' || true
```

Expected: no new connection loops or task activation failures.

## Rollback

Rollback is valid while the PVC is retained.

```bash
kubectl apply -f 50-infra/vultr/zeebe/zeebe.yaml
kubectl -n mitama-udf rollout status sts/zeebe --timeout=180s
kubectl apply -f 50-infra/vultr/zeebe/zeebe-murakumo-gateway-lb.yaml

helm upgrade mitama-udf-pool 50-infra/vultr/mitama-udf-pool \
  -n mitama-udf \
  --reuse-values \
  --set zeebeWorker.enabled=true
```

If rollback is needed because Spiff failed after broker deletion, keep
`BPMN_ENGINE_URL` unset for fallback-capable workers and restore their
`ZEEBE_GATEWAY` value to `zeebe-gateway.mitama-udf.svc.cluster.local:26500`.

## Final Cleanup

After one full production cycle with no rollback:

```bash
kubectl -n mitama-udf delete pvc -l app.kubernetes.io/name=zeebe
```

Only after PVC deletion should follow-up PRs remove stale Zeebe manifests,
`bpmn-zeebe` runtime registrations, and legacy `vertex_zeebe_*` / Zeebe-shaped
runtime tables. Keep `vertex_bpmn_process_def` and
`vertex_bpmn_lexicon_binding`; they are engine-agnostic spec tables.
