# Medical Coverage MCP

Cluster-local MCP control plane for the medical coverage ingester.

The MCP server does not ingest PubMed or facility rows directly. It exposes
short control-plane tools that read Kotoba/Datomic coverage and operate the existing
`medical-coverage-ingester` Kubernetes CronJob/Jobs.

The runtime shape is:

- ingest: Kubernetes CronJob running a Python batch container
- MCP: Kubernetes Deployment running a Python HTTP JSON-RPC control plane
- data plane: Kotoba/Datomic tables/materialized views
- not currently used: Zeebe workers or Kotoba/Datomic Python external UDFs

## Tools

- `medical.coverage.get`
- `medical.targets.list`
- `medical.ingest.trigger`
- `medical.ingest.status`
- `medical.ingest.logs`
- `medical.ingest.pause`
- `medical.ingest.resume`
- `medical.ingest.reconcile`
- `medical.ingest.configure`

## Runtime

Namespace: `kotoba`

Required Secret:

```bash
kubectl -n kotoba create secret generic medical-coverage-mcp-secrets \
  --from-literal=KOTOBA_URL='http://127.0.0.1:8077'
```

Optional Secret keys:

- `MCP_AUTH_TOKEN`: bearer token for mutation/read access when exposed outside
  the cluster.

The server uses the pod ServiceAccount for Kubernetes API access.

For external MCP access, route `actor.etzhayyim.com/iryo/mcp` to this service through
a Cloudflare Tunnel or Ingress URL and set `MEDICAL_COVERAGE_MCP_URL` on the
`actor-resolver` Worker.

For GitOps, copy `secrets-template.yaml` to a SOPS/SealedSecret/ExternalSecret
managed file outside the plain-text path, then sync this directory with
Argo CD or Flux.
