# RUNBOOK — cut atproto.etzhayyim.com over to the independent clj PDS

Goal: make `atproto.etzhayyim.com` serve the **independent etzhayyim PDS**
(`did:web:atproto.etzhayyim.com`, kotoba Datom-log backend) instead of the
gftd.ai worker it currently aliases.

These steps require credentials/connectivity NOT available from a laptop dev
shell: a reachable k8s cluster (`atproto` ns), GHCR push, and Cloudflare API for
the **etzhayyim.com** zone. Run from an authenticated operator box.

## 0. Preconditions
- `kubectl get ns atproto` succeeds (cluster reachable — needs the fleet VPN/WireGuard).
- `docker` daemon up; logged in to `ghcr.io` with push scope for `etzhayyim`.
- `wrangler whoami` (or a Cloudflare API token) authorized on the **etzhayyim.com** zone.
- A cloudflared **named tunnel** owned by the etzhayyim.com Cloudflare account.

## 1. Build + push the image
```bash
cd 50-infra/etzhayyim-atproto-pds-clj
docker build -t ghcr.io/etzhayyim/etzhayyim-atproto-pds:clj-canary .
docker push ghcr.io/etzhayyim/etzhayyim-atproto-pds:clj-canary
```

## 2. Secrets (do NOT commit real values)
```bash
kubectl -n atproto create secret generic etzhayyim-atproto-pds-secrets \
  --from-literal=KOTOBA_URL='http://kotoba.kotoba.svc.cluster.local:4566'
kubectl -n atproto create secret generic etzhayyim-atproto-pds-tunnel-token \
  --from-literal=token='<CLOUDFLARED_TUNNEL_TOKEN>'
```
> Leave `KOTOBA_URL` unset only for a no-DB smoke test (in-process datom log — not durable).

## 3. Deploy the pod
```bash
kubectl apply -f deploy/deployment.yaml
kubectl apply -f deploy/service.yaml     # the Service only; fill secrets via step 2
kubectl -n atproto rollout status deploy/etzhayyim-atproto-pds
# in-cluster smoke test:
kubectl -n atproto run curl --rm -it --image=curlimages/curl --restart=Never -- \
  curl -s http://etzhayyim-atproto-pds:8787/xrpc/com.atproto.server.describeServer
# expect: "did":"did:web:atproto.etzhayyim.com","availableUserDomains":["etzhayyim.com"]
```

## 4. Point the tunnel ingress at the PDS
In the cloudflared tunnel config (etzhayyim.com account), add the ingress rule
ABOVE the catch-all:
```yaml
ingress:
  - hostname: atproto.etzhayyim.com
    service: http://etzhayyim-atproto-pds.atproto.svc.cluster.local:8787
  - service: http_status:404
```

## 5. THE CUTOVER — repoint atproto.etzhayyim.com (etzhayyim.com zone)
The host currently routes to the gftd worker. Replace that on the **etzhayyim.com**
zone with a CNAME to the tunnel:
```bash
# via Cloudflare API (etzhayyim.com zone id = $ZONE):
#  - DELETE any existing Worker route 'atproto.etzhayyim.com/*' on this zone
#  - UPSERT proxied CNAME  atproto.etzhayyim.com -> <TUNNEL_ID>.cfargotunnel.com
```
Do NOT touch the gftd.ai zone — atproto.gftd.ai keeps working for gftd.

## 6. Verify the live cutover
```bash
curl -s https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer | jq .
# MUST now show did:web:atproto.etzhayyim.com + availableUserDomains ["etzhayyim.com"]
curl -s https://atproto.etzhayyim.com/.well-known/did.json | jq '.service[].serviceEndpoint'
# MUST be all *.etzhayyim.com, zero *.gftd.ai
diff <(curl -s https://atproto.etzhayyim.com/.well-known/did.json) \
     <(curl -s https://atproto.gftd.ai/.well-known/did.json)
# MUST now differ (previously byte-identical)
```

## 7. Rollback
Re-point the atproto.etzhayyim.com CNAME / Worker route on the etzhayyim.com zone
back to its previous target (snapshot it in step 5 before changing). Pod can stay
up; rollback is purely the zone record.

## Migration impact
The live PDS hosts no real user repos today (`resolveAtprotoAccount` returns null
for everything but the PDS DID itself), so there are no account repos to migrate.
New accounts created after cutover live on the kotoba Datom log under
`did:web:atproto.etzhayyim.com`.
