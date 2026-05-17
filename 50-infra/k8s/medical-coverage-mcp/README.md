# Medical Coverage MCP

Cluster-local MCP control plane for the medical coverage ingester.

The MCP server does not ingest PubMed or facility rows directly. It exposes
short control-plane tools that read RisingWave coverage and operate the existing
`medical-coverage-ingester` Kubernetes CronJob/Jobs.

The runtime shape is:

- ingest: Kubernetes CronJob running a Python batch container
- MCP: Kubernetes Deployment running a Python HTTP JSON-RPC control plane
- data plane: RisingWave tables/materialized views
- not currently used: Zeebe workers or RisingWave Python external UDFs

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

Namespace: `risingwave`

Required Secret:

```bash
kubectl -n risingwave create secret generic medical-coverage-mcp-secrets \
  --from-literal=RW_DSN='host=risingwave.risingwave.svc.cluster.local port=4566 dbname=dev user=root'
```

Optional Secret keys:

- `MCP_AUTH_TOKEN`: bearer token for mutation/read access when exposed outside
  the cluster.

The server uses the pod ServiceAccount for Kubernetes API access.

For external MCP access, route `actor.gftd.ai/iryo/mcp` to this service through
a Cloudflare Tunnel or Ingress URL and set `MEDICAL_COVERAGE_MCP_URL` on the
`actor-resolver` Worker.

For GitOps, copy `secrets-template.yaml` to a SOPS/SealedSecret/ExternalSecret
managed file outside the plain-text path, then sync this directory with
Argo CD or Flux.
