# intel-dependency-worker

Kubernetes worker for `intel.etzhayyim.com` dependency inference.

The first slice continuously infers:

- `Building -> owned_by -> LegalEntity`
- LEI-backed owner confidence upgrades
- review queue split at `confidence < 0.85`
- global `vertex_*` / `actor_registry` dependency topology by scanning
  `edge_* (src_vid, dst_vid)` tables, classifying dependency direction, and
  writing reverse-topology order snapshots

It writes to:

- `vertex_intel_inference_run`
- `edge_intel_dependency`
- `vertex_dependency_topology_order`

The namespace is explicitly `intel`; do not deploy into `default`.

The worker supports two execution modes:

- `Deployment/intel-langserver-worker`: exposes LangServer tools used by
  `intel.inferDependencies` / `intel.resolveEntity`, and runs the global
  topology daemon every 15 minutes.
- `CronJob/intel-dependency-worker`: runs the same chain every 15 minutes as a
  safety-net graph delta scan and topology refresh.

Deploy:

```sh
kubectl apply -f deployment.yaml
```

Required secret:

```sh
kubectl -n intel create secret generic intel-dependency-worker-secrets \
  --from-literal=KOTOBA_URL='http://127.0.0.1:8077'
```

RunPod/OpenAI-compatible LLM assist for ambiguous dependency/entity resolution
uses `https://llm.etzhayyim.com/v1/chat/completions` by default:

```sh
kubectl -n intel create secret generic intel-dependency-worker-secrets \
  --from-literal=KOTOBA_URL='http://127.0.0.1:8077' \
  --from-literal=INTEL_LLM_API_KEY='<optional-gateway-key>' \
  --dry-run=client -o yaml | kubectl apply -f -
```

The Deployment sets `INTEL_LLM_MAGATAMA_VERIFIED=true` for the internal
`llm.etzhayyim.com` gateway path. Override `INTEL_LLM_URL` / `INTEL_LLM_MODEL` only
when pointing the worker at a different OpenAI-compatible endpoint.

Topology controls:

```sh
INTEL_TOPOLOGY_DAEMON=true          # Deployment background loop
INTEL_TOPOLOGY_ANALYZE=true         # RUN_ONCE path runs topology pipeline
INTEL_TOPOLOGY_LLM_RESOLVE=true     # use llm.etzhayyim.com for ambiguous edges
INTEL_TOPOLOGY_MAX_NODES_PER_TABLE=1000
INTEL_TOPOLOGY_MAX_EDGES_PER_TABLE=5000
INTEL_LLM_TIMEOUT_SEC=90           # llm.etzhayyim.com can wait on RunPod queue
LANGSERVER_WORKER_RESTART_DELAY_SEC=15
```

LangServer task types:

- `intel.topology.analyze`
- `intel.topology.update`

Run once:

```sh
kubectl -n intel create job intel-dependency-worker-now \
  --from=cronjob/intel-dependency-worker
```

Smoke-test the Kubernetes manifests and CronJob-derived Job locally:

```sh
./job-test.sh
```

Run the worker integration tests without a live Kotoba/Datomic connection:

```sh
python3 -m unittest test_worker.py
```

The same image hosts pod-side LangServer handlers for `intel.inferDependencies`
and `intel.resolveEntity`.
