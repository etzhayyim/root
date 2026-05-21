# ai-gftd-project-society6 App

## Components

- `society6-ui-s6c9m2q1`
  - `70-tools/gftd-static-site` で static 配信
  - host: `society6.gftd.ai`
  - content:
    - COFOG wasm components access portal
    - Society6 policy proposals and design principles

## Build

```bash
cd society6-ui-s6c9m2q1 && gftd build
```

## Deploy (example)

```bash
cd society6-ui-s6c9m2q1 && kubectl apply -f <repo-deploy-config>
kubectl apply -f k8s/http-routes.yaml
```
