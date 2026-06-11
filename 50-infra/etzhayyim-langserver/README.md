# etzhayyim-langserver — Murakumo-fleet LSP 常駐

LSP server を Murakumo Mac mini fleet 上に launchd で常駐させ、fleet 内任意の編集端末
(自分の Mac / nvim / VSCode / zed / helix) から remote attach できるようにする substrate。

## なぜこの層 (50-infra)

- ADR-2605191346: etzhayyim/* deployment target は **Murakumo Mac-mini fleet のみ**
- ADR-2605192415 §7.1: Tier 1 = launchd 常駐 (no commercial K8s)
- 既存 `com.etzhayyim.kotodama-cell-runner.plist` の convention を踏襲

## 逆トポロジー順 (leaf → root, in-progress)

| Layer | Concern | Status |
|---|---|---|
| L1 | fleet host inventory + HW probe | ✅ scaffold landed (HW probe pending user-run) |
| L2 | launchd plist template `com.etzhayyim.langserver.*` | ✅ template + wrapper + README (dry-run only, plutil OK) |
| L3 | LSP binary version pin | ✅ `langservers.toml` SSoT + installer (dry-run by default) + `deps.toml` `[platform.langserver]` block |
| L4 | socket / TCP listener config | ✅ `transports.toml` + socat fork-mode wrapper (Unix socket + TCP loopback, both:) |
| L5 | tailmesh fleet-wide LSP sharing | ✅ `mesh.toml` + wrapper `mesh-tcp:` / `mesh-both:` modes + `lsp-fleet.json` registry generator |
| L6 | health-check + auto-restart | ✅ healthz HTTP sidecar (stdlib only, /healthz JSON) + watchdog.sh + 200/503 paths smoke-tested |
| L7 | observability (log shipping) | ✅ `obs.toml` + newsyslog rotation + `/metrics` Prometheus on sidecar (smoke-tested) + opt-in NATS forwarder |
| L8 | editor bridge (nvim / VSCode / zed / helix) | ✅ `attach-langserver.sh` shim + 4 editor configs + nvim native plugin |
| L9 | cell-runner integration (Pregel symbol-aware) | ✅ `langserver_client` library + `LangserverHealthMonitoringCell` ref impl + cells.toml entry |

## Hard rules (per CLAUDE.md + ADR matrix)

- `etzhayyim-` prefix only (or no prefix). Legacy `etzhayyim-` / `com.etzhayyim.` 禁止。
- Apache 2.0 + Charter Compliance Rider v2.0 (`/CHARTER-RIDER.md`)
- 50-infra layout 準拠 (sibling of `etzhayyim-charters-compliance`, `etzhayyim-tithe-router` etc.)
- `deps.toml` SSoT 更新必須 (L3 で binary pin、L1 で fleet 追記)
- Substrate hard rules: AT Protocol MST / IPFS / Base L2 only. **LSP は computation only, 永続 state を持たない** ので substrate 制約は緩い (logs は MST に流さず stdout file)。

## Reference: existing convention

- plist template: `50-infra/cluster/murakumo/cell-runner/com.etzhayyim.kotodama-cell-runner.plist`
- fleet SSoT: `50-infra/murakumo/fleet.toml`
- mesh substrate: `50-infra/cluster/murakumo/` (tailmesh, X25519 + XChaCha20-Poly1305)
- launchd port allocation rule: cells `13000-14000`, phenotype `14000+`. **langserver 提案: `15500-15600`** (collision-free)
