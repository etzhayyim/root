# ai-gftd-project-shigotoba wasm

このディレクトリは `ai-gftd-project-shigotoba` の App 実装です。

- `shigotoba-jobs-component`
  - UI (`/`)
  - REST API (`/api/v1/*`)
  - MCP (`/api/mcp`)

Build:

```bash
cd shigotoba-jobs-component
gftd build
```

Deploy:

```bash
cd shigotoba-jobs-component
kubectl apply -f <repo-deploy-config>
```
