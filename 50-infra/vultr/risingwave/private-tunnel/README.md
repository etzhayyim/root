# 50-infra/vultr/risingwave/private-tunnel

Cloudflare Tunnel exposing RisingWave to Hyperdrive **without** a public IP.
Created 2026-05-17 to replace the previous public LoadBalancer
(`45.32.79.245:4566`) after the GitGuardian credential-leak incident.

## What this provides

```
Cloudflare Workers
        ↓ (binding)
Hyperdrive
        ↓ (over Cloudflare Tunnel, no public origin)
risingwave-private.etzhayyim.com (CNAME → a17cdf9d-….cfargotunnel.com)
        ↓ (cloudflared in cluster)
tcp://risingwave.risingwave.svc.cluster.local:4566  (ClusterIP, in-cluster only)
        ↓
RisingWave frontend (auth-required, root password in 1Password)
```

## Components

| Resource | Name | Purpose |
|---|---|---|
| CF Tunnel | `risingwave-private` (id `a17cdf9d-7b9d-4cf4-a482-66129bc2a43d`) | TCP ingress into the cluster |
| CF DNS | `risingwave-private.etzhayyim.com` (CNAME → tunnel) | Hostname for Hyperdrive |
| K8s Secret | `risingwave/cloudflared-risingwave-private-credentials` | Tunnel `credentials.json` |
| K8s ConfigMap | `risingwave/cloudflared-risingwave-private-config` | `config.yaml` with TCP ingress |
| K8s Deployment | `risingwave/cloudflared-risingwave-private` (replicas: 2) | cloudflared 2025.4.0 |
| K8s Service (target) | `risingwave/risingwave` (ClusterIP `10.100.13.171:4566`) | RisingWave frontend |
| RW credential | 1Password vault `etzhayyim`, item `RisingWave root (rotated 2026-05-17)` (ID `kudkk66526jk3ft4iasbezf6uy`) | 32-char root password (auth-enforced via `ALTER USER root WITH PASSWORD`) |

## Apply (idempotent)

```bash
# 1. Create tunnel + DNS (one-time)
cloudflared tunnel create risingwave-private
TUNNEL_ID=$(cloudflared tunnel list | awk '/risingwave-private/ {print $1}')
cloudflared tunnel route dns risingwave-private risingwave-private.etzhayyim.com

# 2. K8s Secret with tunnel credentials (one-time)
export KUBECONFIG=/tmp/rw-vke-a61d513b-f9b7-4121-abb9-b53732aa5ec4.yaml
kubectl -n risingwave create secret generic cloudflared-risingwave-private-credentials \
  --from-file=credentials.json=$HOME/.cloudflared/${TUNNEL_ID}.json \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. ConfigMap + Deployment (idempotent — edit config.yaml then re-apply)
kubectl apply -f 50-infra/vultr/risingwave/private-tunnel/configmap.yaml
kubectl apply -f 50-infra/vultr/risingwave/private-tunnel/deployment.yaml

# 4. Verify tunnel connected
kubectl -n risingwave logs deploy/cloudflared-risingwave-private --tail=20
# Expect: 'Registered tunnel connection' × 4
```

## Hyperdrive setup (REQUIRED — finishes the loop)

The K8s side of the tunnel is automated above; the Hyperdrive side
requires CF Dashboard or API access (the existing CF API token in
Keychain `etzhayyim.cloudflare:API_TOKEN` lacks Hyperdrive scope, so the
dashboard is the path).

### Steps in CF Dashboard

1. Go to https://dash.cloudflare.com/4da88288dc30d9ee257f319d3c33ecf0/workers/hyperdrive
2. Find existing `HYPERDRIVE_VULTR` config (used by CF Workers
   under `binding = "HYPERDRIVE_VULTR"`).
3. Edit it → "Connection method" → select **"Over Cloudflare Tunnel"**.
4. Select tunnel: `risingwave-private`
   (id `a17cdf9d-7b9d-4cf4-a482-66129bc2a43d`)
5. Origin host: `risingwave.risingwave.svc.cluster.local`
   (in-cluster DNS — cloudflared resolves this)
6. Origin port: `4566`
7. Database engine: `PostgreSQL`
8. Database name: `dev`
9. Database user: `root`
10. Password: paste from 1Password vault `etzhayyim` item
    `RisingWave root (rotated 2026-05-17)` (32 chars)
11. Save.

### Alternative — via CF API (requires Hyperdrive-scoped token)

If you mint a CF API token with `Account → Hyperdrive → Edit` permission:

```bash
CF_TOKEN_NEW=<new token>
ACCT=4da88288dc30d9ee257f319d3c33ecf0
HD_ID=$(curl -sS -H "Authorization: Bearer $CF_TOKEN_NEW" \
  "https://api.cloudflare.com/client/v4/accounts/$ACCT/hyperdrive/configs" | \
  jq -r '.result[] | select(.name=="HYPERDRIVE_VULTR") | .id')
NEW_PW=$(op item get kudkk66526jk3ft4iasbezf6uy --field=password --reveal)
curl -sS -X PATCH -H "Authorization: Bearer $CF_TOKEN_NEW" \
  "https://api.cloudflare.com/client/v4/accounts/$ACCT/hyperdrive/configs/$HD_ID" \
  -d "$(jq -nc \
    --arg pw "$NEW_PW" \
    --arg tunnel "a17cdf9d-7b9d-4cf4-a482-66129bc2a43d" \
    '{
       origin: {
         tunnel: {id: $tunnel},
         scheme: "postgres",
         host: "risingwave.risingwave.svc.cluster.local",
         port: 4566,
         database: "dev",
         user: "root",
         password: $pw
       }
     }')"
```

## Verification after Hyperdrive update

Deploy a small CF Worker that uses `env.HYPERDRIVE_VULTR.connect()`:

```ts
export default {
  async fetch(req: Request, env: Env) {
    const sql = postgres(env.HYPERDRIVE_VULTR.connectionString);
    const rows = await sql`SELECT NOW() AS rw_tunneled_ok, current_user`;
    return Response.json(rows[0]);
  }
}
```

Expect: 200 OK with a recent timestamp + `current_user: root`.

## What was decommissioned

- Vultr LoadBalancer for RW (was `45.32.79.245:4566`, wide-open). K8s
  Service `risingwave` patched type LoadBalancer → ClusterIP at
  2026-05-17T21:55Z. Vultr LB id `63490c84-0b1b-4cd1-a9f8-991cf54a8c68`
  released by VKE CCM.
- The LB external IP `45.32.79.245` was released to Vultr's pool;
  reusing it for any future binding is **not** safe (other Vultr tenants
  may receive it).

## References

- `50-infra/vultr/risingwave/rotate-password.sh` — password rotation runbook
- `50-infra/vultr/risingwave-firewall-restrict.sh` — Vultr instance firewall (not used in final design; superseded by ClusterIP + tunnel)
- ADR-2605172000 — etzhayyim/root RW-free substrate (note: this private tunnel keeps vendor RW reachable from CF Workers without breaking the open-substrate boundary; vendor business continues)
