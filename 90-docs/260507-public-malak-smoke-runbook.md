# Public Malak smoke runbook

This runbook covers the Public Malak hourly smoke test in
`mitama-udf/public-malak-smoke-cron`.

The smoke writes one synthetic Telegram observation, waits for Kotoba/Datomic
snapshot visibility, checks `listSnapshots` through the in-cluster dispatcher,
and verifies public HTML/HAR artifact routes through `public-malak.etzhayyim.com`.

## Manual Gate

```bash
helm -n mitama-udf test mitama-udf-pool --timeout 1200s
kubectl -n mitama-udf logs job/public-malak-smoke --tail=80
```

Expected final log shape:

```json
{"ok": true, "listSnapshots": {"status": 200}, "html": {"status": 200, "store": "s3"}, "har": {"status": 200, "store": "s3"}}
```

## Cron Status

```bash
kubectl -n mitama-udf get cronjob public-malak-smoke-cron -o wide
kubectl -n mitama-udf get jobs -l app.kubernetes.io/name=public-malak-smoke-cron --sort-by=.metadata.creationTimestamp
```

Create an ad-hoc CronJob-derived run:

```bash
kubectl -n mitama-udf create job public-malak-smoke-cron-manual-$(date +%s) \
  --from=cronjob/public-malak-smoke-cron
```

Then wait and inspect:

```bash
kubectl -n mitama-udf wait --for=condition=complete job/<job-name> --timeout=1200s
kubectl -n mitama-udf logs job/<job-name> --tail=80
```

## Failure Triage

If the smoke fails before `phase=written`, check the worker image and B2 env:

```bash
kubectl -n mitama-udf describe job/<job-name>
kubectl -n mitama-udf logs job/<job-name> --tail=200
kubectl -n mitama-udf get secret public-malak-r2-creds
```

If it fails waiting for `vertex_ads_snapshot`, check Kotoba/Datomic visibility and
KOTOBA_URL injection:

```bash
kubectl -n mitama-udf exec deploy/bpmn-dispatcher -- env | rg '^KOTOBA_URL='
kubectl -n mitama-udf exec deploy/bpmn-dispatcher -- python -c 'import os, psycopg; print(psycopg.connect(os.environ["KOTOBA_URL"]).execute("select 1").fetchone())'
```

If `listSnapshots` fails, check dispatcher auth and direct XRPC:

```bash
kubectl -n mitama-udf get secret bpmn-dispatcher-auth
kubectl -n mitama-udf logs deploy/bpmn-dispatcher --tail=200
```

If public artifacts return 403 from in-cluster Python but work from curl, verify
the smoke is using the explicit `public-malak-smoke/1` User-Agent. Cloudflare can
block Python's default urllib User-Agent.

## Alerting

The chart includes an optional `PrometheusRule` at:

```text
50-infra/vultr/mitama-udf-pool/templates/public-malak-smoke-prometheusrule.yaml
```

It is disabled by default because the current cluster may not have the
`monitoring.coreos.com/PrometheusRule` CRD installed.

Enable it only after the CRD and kube-state-metrics CronJob/Job metrics are
available:

```bash
helm -n mitama-udf upgrade mitama-udf-pool 50-infra/vultr/mitama-udf-pool \
  --reuse-values \
  --set publicMalakSmoke.prometheusRule.enabled=true \
  --wait
```
