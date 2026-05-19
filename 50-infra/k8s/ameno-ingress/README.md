# ameno-ingress

Cloudflare Tunnel + bearer-token auth for `ameno-daemon.etzhayyim.com`.

ADR-2605191407 (viewer mode) + ADR-2605191346 (Vultr-free).

## Topology

```
Browser (anywhere on the open internet)
  └─ HTTPS to https://ameno-daemon.etzhayyim.com
       ↓ CF edge (TLS terminated)
       ↓ CF Tunnel
  └─ cloudflared Deployment (in etzhayyim-langserver namespace)
       ↓ HTTP to ollama-fleet OR
       ↓ HTTP to lg-ameno ClusterIP:8080
       ↓ checks `Authorization: Bearer <AMENO_AUTH_TOKEN>`
       ↓ then runs the graph
```

## Apply

```sh
# 1. Create the CF tunnel via `cloudflared tunnel create ameno-daemon`,
#    grab the token from the dashboard, then:
kubectl -n etzhayyim-langserver create secret generic ameno-daemon-tunnel-token \
  --from-literal=token="<paste-token>"

# 2. Generate the bearer token shared with browser clients:
kubectl -n etzhayyim-langserver create secret generic ameno-daemon-auth \
  --from-literal=token="$(openssl rand -hex 32)"

# 3. Patch lg-ameno to read the bearer token:
kubectl -n etzhayyim-langserver patch deploy lg-ameno --patch '
spec:
  template:
    spec:
      containers:
        - name: server
          env:
            - name: AMENO_AUTH_TOKEN
              valueFrom: { secretKeyRef: { name: ameno-daemon-auth, key: token } }
'

# 4. Apply the tunnel deployment:
kubectl apply -f cloudflared-deploy.yaml

# 5. Configure the tunnel's ingress rules (Cloudflare dashboard or YAML):
#      hostname: ameno-daemon.etzhayyim.com
#      service:  http://lg-ameno.etzhayyim-langserver.svc.cluster.local:8080
```

Once the tunnel is connected (`kubectl logs deploy/ameno-tunnel`),
`curl https://ameno-daemon.etzhayyim.com/healthz` returns 401 without
auth and 200 with the bearer token.

## Browser viewer mode against the tunnel

In the svelte appview's Compute selector, pick `custom` and:

- URL: `https://ameno-daemon.etzhayyim.com`
- Auth token: paste the same value you wrote to the
  `ameno-daemon-auth` secret

viewer-mode.ts attaches `Authorization: Bearer …` to both `/healthz`,
`/workerInfo`, and `/threads/:tid/stream` calls.

## Limitations of bearer auth

- One token per cluster. Rotating means restarting every browser
  session.
- Token leaks via address bar / shoulder-surf / browser dev tools.
- No per-actor identity — the daemon sees only "anyone with the
  token". `did:web` challenge-response is the proper next step
  (separate ADR follow-up: `etzhayyim-daemon-did-auth`).

For v0.1 (single-operator deployments and dev) this is acceptable.
Production multi-user requires the DID auth upgrade.

## License

Apache-2.0.
