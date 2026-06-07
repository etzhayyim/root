# bpmn-engine-host smoke

ADR 2605081200 PoC Phase 1 acceptance harness.

## What it covers

| Acceptance criterion | Coverage in `smoke.py` |
|---|---|
| 100 instance 並行 p95 < 30s | ✅ direct; `p95_s` uses DB-clock `instance_started` → `completed_at` |
| RW で `UPDATE` / `ON CONFLICT` 0 件 | ◐ indirect (history monotonic seq + orphan job invariant). For absolute proof, enable `log_statement=all` on RW frontend and `grep -E 'UPDATE\|ON CONFLICT' rw-frontend.log` after the smoke run |
| Engine pod restart replay | ✗ operational — see "restart drill" below |
| pyzeebe watchdog issue 非再発 | ✗ operational — `kubectl logs` of any pyzeebe-using worker (intel/lei) for >24h |

## Prereqs

1. Schema migration applied (`r_20260509110000_vertex_spiff_runtime`)
2. `bpmn-engine-host` Deployment running (or local dev: `granian
   --interface asgi main:app`)
3. At least one BPMN seeded into `vertex_bpmn_process_def` (default
   uses `lawfirm_intake_funnel` from
   `migrations/20260509080000_vertex_lawfirm_matter_intake.ts`)
4. The chosen BPMN's service tasks must have a worker subscribed
   (e.g. `open-lei-spiff-worker` for `gleif.collect`); otherwise
   instances park at the first service task and the smoke times out.
   For pure-flow smoke without external workers, pick a BPMN whose
   tokens reach end events via gateways alone.

## Run

```bash
# port-forward locally
kubectl -n mitama-udf port-forward svc/bpmn-engine-host 8080:80 &

export BPMN_ENGINE_URL=http://localhost:8080
export KOTOBA_URL="$(security find-generic-password -s etzhayyim.kotoba -a KOTOBA_URL -w)"

cd 50-infra/k8s/bpmn-engine-host/tests
python smoke.py --process-id lawfirm_intake_funnel \
                --concurrency 100 \
                --timeout-s 60 \
                --p95-budget-s 30
```

Exit code 0 = pass. Output is JSON for CI ingestion.

2026-05-09 verified baseline:

- `bpmn-engine-host`: `ghcr.io/etzhayyim/bpmn-engine-host:20260509-1705no-inline-cache`
- `lawfirm-spiff-worker`: `ghcr.io/etzhayyim/lawfirm-spiff-worker:20260509-0250inline-default4`
- c100 smoke: `completed=100`, `p95_s=10.888`,
  `history_violations=[]`, `orphan_violations=[]`
- restart drill c100: `completed=100`, `p95_s=12.861`,
  `history_violations=[]`, `orphan_violations=[]`

## Restart drill (manual)

```bash
# Terminal 1: start smoke with a generous timeout
python smoke.py --concurrency 100 --timeout-s 180 &
SMOKE_PID=$!

# Terminal 2: kill the engine pod ~10s in
sleep 10
kubectl -n mitama-udf delete pod \
  -l app.kubernetes.io/name=bpmn-engine-host

# Wait for smoke to finish; it should still pass thanks to instance
# state replay from vertex_spiff_instance.state_json on engine restart.
wait $SMOKE_PID
```

## Known limits

- `p95_s` is measured on the DB clock from
  `vertex_spiff_history.event_type='instance_started'` to
  `vertex_spiff_instance.completed_at`. `observed_p95_s` is also emitted
  and includes runner-side RW polling/read visibility latency; use it for
  diagnostics, not the ADR acceptance budget.
- The script holds psycopg connections from one host (the runner). For
  in-cluster execution as a `kubectl run` Job, no change is needed.
- BPMN error event paths are not exercised; that is gated on the
  `POST /v1/job/{id}/throwBpmnError` follow-up.
