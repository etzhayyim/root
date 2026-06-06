# bpmn-dispatcher (etzhayyim)

F4 — generic XRPC dispatcher for BPMN-as-actor. HTTP server that owns the
T1/T2 actor surface: turns `POST /xrpc/{nsid}` into a LangServer.
`run_process_with_result` call, routed via `vertex_bpmn_lexicon_binding`
lookup.

## History

Extracted from `etzhayyim-apps-etzhayyimcojp` 2026-05-22 per ADR-2605181400 §D2
amendment. D2's original "leave dispatcher in etzhayyim" decision was based on
pymagatama package living in etzhayyim; pymagatama was subsequently migrated
to `etzhayyim/20-actors/magatama/py/`, making the dispatcher infrastructure
the last remaining bpmn artifact in etzhayyim. This directory closes that loop.

## Layout

| File | Purpose |
|---|---|
| `deployment-dispatcher.yaml` | Python aiohttp Deployment + ClusterIP Service for the bpmn-dispatcher pod (image runs `python -m pymagatama.dispatcher_main`) |
| `tunnel.yaml` | Cloudflare Tunnel — Secret + ConfigMap + Deployment (2 replicas). Hostnames: `dispatcher.etzhayyim.com`, `mcp.etzhayyim.com`, `ses-api.etzhayyim.com` |
| `ingress-dispatcher.yaml` | nginx Ingress fallback for `dispatcher.etzhayyim.com` (used when the tunnel is unhealthy; see etzhayyim ADR-2605111400 nginx-ingress-yatabase backstory) |
| `configmap-pymagatama-cache-fix.yaml` | Hot-patch ConfigMap mounting an alternative `dispatcher_main.py` (cache fix variant) over the image's baked source |
| `configmap-pymagatama-sse-fix.yaml` | Hot-patch ConfigMap mounting an alternative `dispatcher_main.py` (SSE fix variant) |
| `configmap-mailer-direct-patch.yaml` | Hot-patch ConfigMap for the mailer-direct flow (~80KB embedded Python) |

The three patch ConfigMaps are historical hot-patches that should be
reconciled with the canonical `pymagatama.dispatcher_main` source in
`etzhayyim/20-actors/magatama/py/src/pymagatama/dispatcher_main.py`
(merge fixes, drop ConfigMaps, rebuild image).

## Operator pending

1. **Cloudflare**: on the etzhayyim CF account run
   `cloudflared tunnel create bpmn-dispatcher` → replace
   `REPLACE_ME_TUNNEL_ID` + `REPLACE_ME_CREDENTIALS_JSON` in `tunnel.yaml`.
2. **DNS**: CNAME `dispatcher.etzhayyim.com` and `mcp.etzhayyim.com`
   (and `ses-api.etzhayyim.com` if SES API is to be exposed) to
   `<TUNNEL_ID>.cfargotunnel.com` (proxied=True).
3. **Image**: replace `REPLACE_ME_IMAGE_REF` in `deployment-dispatcher.yaml`
   with the pymagatama image built from `etzhayyim/20-actors/magatama/py/`.
4. **Secrets**: provision in namespace `mitama-udf` —
   `bpmn-dispatcher-auth` (`INTERNAL_SECRET`),
   `bpmn-dispatcher-rw` (`RW_URL`, see Substrate boundary below),
   `lawfirm-stripe` + `public-malak-r2-creds` + `lg-pregel-secrets`
   (optional refs).
5. **Apply**: `kubectl apply -f .` from this directory.
6. **etzhayyim-side teardown** (after etzhayyim tunnel verified HEALTHY):
   - `cloudflared tunnel delete bpmn-dispatcher` on etzhayyim CF account
     (current tunnel ID `be2cc0b0-ddee-4ca7-baf1-2bffbef18f31`)
   - `kubectl delete deployment cloudflared-bpmn-dispatcher bpmn-dispatcher -n mitama-udf` on etzhayyim VKE
   - Update etzhayyim `00-contracts` references (`dispatcher.etzhayyim.com` → `dispatcher.etzhayyim.com`) — separate iter (ADR-2605181400 §D3 follow-up).

## Substrate boundary

This Deployment carries **inherited substrate violations** from
pymagatama's vendor-tier handlers. Per etzhayyim ADR-2605172100 hard
rule "MUST NOT integrate fiat payment processors":

| Env var (inherited) | Why preserved | Cleanup path |
|---|---|---|
| `STRIPE_US_API_KEY` / `STRIPE_JP_API_KEY` / `STRIPE_IN_API_KEY` / `STRIPE_PUBLIC_KEY` / `STRIPE_WEBHOOK_SECRET` | `pymagatama.primitives.lawfirm_checkout` / `lawfirm_billing` / `ingest.stripe` still reference them | pymagatama Stripe extraction (track in `deps.toml [[migrations]]`); after extraction drop the entire STRIPE_* block |
| `RW_URL` | `pymagatama.db_sync` uses Kotoba/Datomic for `vertex_bpmn_lexicon_binding` lookup | Migrate binding registry to AT MST records or IPFS; after migration drop `RW_URL` + `RW_*_GUARD` block |

These were already present in pymagatama at the time of its etzhayyim
migration; this iter does not introduce new violations. Substrate purity
cleanup is a separate workstream tracked against pymagatama, not this
Deployment.

## Topology

```
Client
  ↓ HTTPS
CF edge (any *.etzhayyim.com)
  ↓
CF edge (mcp.etzhayyim.com / dispatcher.etzhayyim.com CNAME)
  ↓ WireGuard/QUIC tunnel
cloudflared pod (mitama-udf ns, 2 replicas)
  ↓ cluster-internal HTTP
bpmn-dispatcher Service (ClusterIP :8080)
  ↓
bpmn-dispatcher pod (aiohttp + F5 watcher → LangServer)
  ↓ AgentGateway MCP
LangServer pods (lg-shinshi, lg-animeka, lg-recap, lg-media-gamers,
                 lg-ses, lg-pregel, lg-yatabase, etc.)
```

## References

- `90-docs/adr/2605181400-bpmn-extract-to-etzhayyim-root.md` §D2 amendment 2026-05-22
- `90-docs/adr/2605172100-etzhayyim-onchain-payment-substrate.md` (substrate boundary)
- `90-docs/adr/2605111200-cf-worker-edge-only-no-rw-connection.md` (RW access topology)
- etzhayyim source predecessor:
  - `etzhayyim-apps-etzhayyimcojp/50-infra/vultr/mitama-udf-pool/templates/dispatcher.yaml` (Helm)
  - `etzhayyim-apps-etzhayyimcojp/50-infra/vultr/mitama-udf-app-raw/templates/` (Helm wrappers + rendered manifests)
  - `etzhayyim-apps-etzhayyimcojp/50-infra/vultr/cloudflared/bpmn-dispatcher-tunnel.yaml`
