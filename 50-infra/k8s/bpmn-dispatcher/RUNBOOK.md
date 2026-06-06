# bpmn-dispatcher — Deploy Runbook

## Prerequisites

- etzhayyim CF account access (`cloudflared` CLI authenticated)
- `kubectl` context = etzhayyim VKE
- pymagatama image built and pushed to `ghcr.io/etzhayyim/pymagatama:<tag>`
- Namespace `mitama-udf` exists (created by `bpmn-engine-host` Deployment)

## Bring-up

```bash
# 1. Create the CF tunnel on the etzhayyim account
cloudflared tunnel create bpmn-dispatcher
# → outputs Tunnel ID + writes ~/.cloudflared/<UUID>.json credentials

# 2. Patch tunnel.yaml
TUNNEL_ID="<from step 1>"
CREDS_JSON=$(cat ~/.cloudflared/${TUNNEL_ID}.json)
sed -i.bak "s/REPLACE_ME_TUNNEL_ID/${TUNNEL_ID}/g" tunnel.yaml
# Manually paste CREDS_JSON into the credentials.json block (indent 4 spaces)

# 3. DNS — point dispatcher.etzhayyim.com + mcp.etzhayyim.com at the tunnel
cloudflared tunnel route dns bpmn-dispatcher dispatcher.etzhayyim.com
cloudflared tunnel route dns bpmn-dispatcher mcp.etzhayyim.com
# (ses-api.etzhayyim.com if SES API is to be exposed via this tunnel)

# 4. Patch dispatcher deployment image
IMAGE_REF="ghcr.io/etzhayyim/pymagatama:<tag>"
sed -i.bak "s|REPLACE_ME_IMAGE_REF|${IMAGE_REF}|g" deployment-dispatcher.yaml

# 5. Provision secrets in mitama-udf
kubectl -n mitama-udf create secret generic bpmn-dispatcher-auth \
    --from-literal=INTERNAL_SECRET="$(openssl rand -hex 32)"
kubectl -n mitama-udf create secret generic bpmn-dispatcher-rw \
    --from-literal=KOTOBA_URL="<postgres://... — substrate-violation, see README>"
# Optional (Stripe / R2 / OpenRouter) — see README "Substrate boundary".

# 6. Apply manifests
kubectl apply -f .

# 7. Verify
kubectl -n mitama-udf rollout status deployment/cloudflared-bpmn-dispatcher
kubectl -n mitama-udf rollout status deployment/bpmn-dispatcher
curl -sS https://dispatcher.etzhayyim.com/health
# → {"status":"ok"}
```

## Cutover from etzhayyim

After etzhayyim tunnel + dispatcher pods report HEALTHY and `/health`
end-to-end works:

```bash
# 1. Delete etzhayyim tunnel (etzhayyim CF account)
cloudflared tunnel delete bpmn-dispatcher   # ID: be2cc0b0-ddee-4ca7-baf1-2bffbef18f31

# 2. Drain etzhayyim VKE workload
kubectl --context etzhayyim-lax -n mitama-udf delete deployment cloudflared-bpmn-dispatcher
kubectl --context etzhayyim-lax -n mitama-udf delete deployment bpmn-dispatcher

# 3. Remove etzhayyim DNS records
# dispatcher.etzhayyim.com / mcp.etzhayyim.com — manual delete via CF dashboard or
# terraform plan/apply if etzhayyim-side DNS is in `50-infra/prod/`.
```

## Rollback

If etzhayyim deploy is broken and etzhayyim hasn't been torn down yet:

```bash
# Revert DNS — both *.etzhayyim.com and *.etzhayyim.com records can point at
# the same backend during the cutover window. Operators may keep etzhayyim
# tunnel HEALTHY until etzhayyim is verified.
```

If etzhayyim has already been torn down: restore from the etzhayyim commit that
removed the dispatcher manifests, or re-apply this directory and re-run
bring-up step 1-6 with corrected values.

## Hot-patch reconciliation (follow-up)

The three `configmap-pymagatama-*-fix.yaml` ConfigMaps are legacy
hot-patches. To retire them:

1. Diff `data.dispatcher_main.py` against
   `etzhayyim/20-actors/magatama/py/src/pymagatama/dispatcher_main.py`.
2. Merge any unique fixes into the canonical source.
3. Rebuild pymagatama image with merged fixes baked in.
4. Remove the ConfigMaps from this dir + corresponding volume mounts
   from `deployment-dispatcher.yaml` (currently the Deployment in this
   directory does NOT mount these ConfigMaps — they were applied via
   `mitama-udf-app-raw` Helm chart in etzhayyim as separate hot-patch overlay,
   not via this Deployment template. They're preserved here for archival
   reconciliation only).
