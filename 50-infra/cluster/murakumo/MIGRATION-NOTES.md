# murakumo cluster runtime — Step 8 cutover targets

This directory's Rust runtime is **intentionally** vendor-flavoured (`gftd-*` identifiers) pending the 220-file Step 8 cutover. See repo-root `CLAUDE.md` §Status row 8 — blocked on legal registration.

**Do not rename these in isolation.** The targets are interdependent (env var name + config dir + control-plane URL + DNS suffix + launchd label + cargo package name). Partial rename breaks the runtime. The cutover must be one atomic PR.

Authoritative ADR: **ADR-2605214000** §3.

## Itemised targets

| File | Line | Current (vendor) | Target (etzhayyim) | Type |
|---|---|---|---|---|
| `src/config.rs` | 21 | `endpoint: "https://murakumo.gftd.ai"` | `endpoint: "https://murakumo.etzhayyim.com"` | default endpoint |
| `src/config.rs` | 37 | `.join(".gftd")` | `.join(".etzhayyim")` | config dir |
| `src/config.rs` | 56–58 | parser keys: `GFTD_NODE_ID` / `GFTD_WORKER_ID` / `GFTD_MURAKUMO` / `GFTD_GPU_TIER` / `GFTD_GPU_VRAM_MB` / `GFTD_PROVIDER_MODE` | rename prefix `GFTD_` → `ETZHAYYIM_` | env var name |
| `src/config.rs` | 69–77 | env var reads (same set as above + `GFTD_NODE_ROLE` / `GFTD_NATS_URL` / `GFTD_QUIC_GATEWAY_ADDR`) | rename prefix `GFTD_` → `ETZHAYYIM_` | env var read |
| `src/config.rs` | 87 | save-format `GFTD_*` keys | `ETZHAYYIM_*` | persisted config |
| `src/config.rs` | 119 | `"/usr/local/bin/gftd-murakumo"` | `"/usr/local/bin/etzhayyim-murakumo"` | binary install path |
| `src/api.rs` | 8 | `const DEFAULT_MURAKUMO_APP_ENDPOINT: &str = "https://murakumo.gftd.ai"` | `"https://murakumo.etzhayyim.com"` | default endpoint |
| `src/api.rs` | 20 | `env_or("GFTD_MURAKUMO_HTTP_TIMEOUT", "90s")` | `env_or("ETZHAYYIM_MURAKUMO_HTTP_TIMEOUT", "90s")` | env var read |
| `src/api.rs` | 131 | `env_or("GFTD_MURAKUMO_APP", ...)` | `env_or("ETZHAYYIM_MURAKUMO_APP", ...)` | env var read |
| `src/murakumo_mesh.rs` | 294 | `suffix: ".mesh.gftd.ai".to_string()` | `".mesh.etzhayyim.com"` | DNS suffix |
| `src/murakumo_mesh.rs` | 298 | doc comment `node-id.mesh.gftd.ai` | `node-id.mesh.etzhayyim.com` | doc comment |
| `src/murakumo_mesh.rs` | 305 | doc comment `mesh IP → node-id.mesh.gftd.ai` | `node-id.mesh.etzhayyim.com` | doc comment |
| `src/main.rs` | 112 | `Joins the Murakumo network (murakumo.gftd.ai CF Worker cluster)` | `(murakumo.etzhayyim.com)` | help text |
| `src/main.rs` | 143 | `GFTD_MURAKUMO Control plane (default: https://murakumo.gftd.ai)` | `ETZHAYYIM_MURAKUMO` + `murakumo.etzhayyim.com` | help text |
| `src/main.rs` | 151–152 | `curl -fsSL https://murakumo.gftd.ai/install.sh \| sh` (twice) | `murakumo.etzhayyim.com` | install URL examples |
| `src/main.rs` | 160 | `gftd-murakumo murakumo-mesh dns <node-id>.mesh.gftd.ai` | `etzhayyim-murakumo` + `.mesh.etzhayyim.com` | binary + DNS suffix |
| `src/main.rs` | 573, 576, 582 | usage / strip_suffix / format `.mesh.gftd.ai` | `.mesh.etzhayyim.com` | DNS literal |
| `src/main.rs` | 84 | `GFTD_MURAKUMO_VERBOSE` env var check | `ETZHAYYIM_MURAKUMO_VERBOSE` | env var read (found via dry-run) |
| `src/install.rs` | 12 | help text `HTTP/3 direct to murakumo.gftd.ai CF Worker` | `murakumo.etzhayyim.com` | help text |
| `src/install.rs` | 39 | log `Registering with murakumo.gftd.ai/join...` | `murakumo.etzhayyim.com/join` | log message |
| `src/install.rs` | 176 | `https://cdn.gftd.ai/bin/magatama-inference/latest/{}` | `https://cdn.etzhayyim.com/bin/magatama-inference/latest/{}` | binary download URL |
| `src/install.rs` | 222, 259, 263 | launchd label `ai.gftd.murakumo` + plist filename | `com.etzhayyim.murakumo` | launchd label (found via dry-run) |
| `src/install.rs` | 233–235 | `~/.gftd/daemon.log` paths in plist | `~/.etzhayyim/daemon.log` | log path (found via dry-run) |
| `src/install.rs` | 238–240 | `GFTD_MURAKUMO` + `GFTD_PROVIDER_MODE` plist env keys | `ETZHAYYIM_MURAKUMO` + `ETZHAYYIM_PROVIDER_MODE` | plist env vars (found via dry-run) |
| `src/install.rs` | 269, 278–280, 289–294 | systemd unit: `gftd-murakumo.service`, `GFTD_MURAKUMO`, `GFTD_PROVIDER_MODE` | `etzhayyim-murakumo.service`, `ETZHAYYIM_*` | systemd unit (found via dry-run) |
| `src/daemon.rs` | 23, 27 | `gftd-murakumo` in not-installed / usage messages | `etzhayyim-murakumo` | binary name (found via dry-run) |
| `src/daemon.rs` | 146, 188 | `update_field("GFTD_WORKER_ID", ...)` | `update_field("ETZHAYYIM_WORKER_ID", ...)` | config key (found via dry-run) |
| `src/daemon.rs` | 859, 874, 881, 888, 925 | `GFTD_NATIVE_WEBGPU_EXEC` / `GFTD_NATIVE_TRAIN_EXPERTS_EXEC` / `GFTD_TRAIN_EXPERTS_EXEC` | `ETZHAYYIM_NATIVE_*` | native exec env vars (found via dry-run) |
| `src/daemon.rs` | 1376, 1424 | `.join(".gftd")` + `.gftd/daemon.log` paths | `.etzhayyim` + `.etzhayyim/daemon.log` | config dir (found via dry-run) |
| `src/worker.rs` | 186 | `"gftd-murakumo-native/..."` user agent | `"etzhayyim-murakumo-native/..."` | user agent (found via dry-run) |
| `src/worker.rs` | 76–125 | `GFTD_NATIVE_WEBGPU_*` / `GFTD_NATIVE_WORKER_*` / `GFTD_NATIVE_MEM_CLASS` etc. | `ETZHAYYIM_NATIVE_*` | native worker capability env vars (found via dry-run) |
| `src/worker.rs` | 397 | `GFTD_DEFAULT_MODEL` | `ETZHAYYIM_DEFAULT_MODEL` | model env var (found via dry-run) |
| `deploy-mesh.sh` | 17 | `CONTROL_PLANE="https://murakumo.gftd.ai"` | `CONTROL_PLANE="https://murakumo.etzhayyim.com"` | shell default |
| `deploy-mesh.sh` | 16 | `MESH_IDENTITY_DIR="$HOME/.gftd/mesh"` | `"$HOME/.etzhayyim/mesh"` | mesh identity dir |
| `deploy-mesh.sh` | 104, 109, 112, 117, 152, 153, 167, 176, 178, 210 | various `~/.gftd/` paths + `gftd-murakumo` binary refs | `~/.etzhayyim/` + `etzhayyim-murakumo` | path + binary refs |
| `deploy-mesh.sh` | 164, 182 | launchd label `ai.gftd.murakumo-mesh` + plist path | `com.etzhayyim.murakumo-mesh` + plist path | launchd label |
| `deploy-mesh.sh` | 142–146 | run script body using `gftd-murakumo` | `etzhayyim-murakumo` | run script |
| `Cargo.toml` | (package.name) | `gftd-murakumo` | `etzhayyim-murakumo` | cargo crate name |

## Known intentional remainders (NOT renamed)

| File | Line | Value | Reason |
|---|---|---|---|
| `src/murakumo_mesh.rs` | 13 | `b"gftd-murakumo-mesh-v1"` | Cryptographic key-derivation context tag — renaming breaks DH shared-secret compatibility with all existing nodes. Requires coordinated fleet protocol bump, separate PR. |
| `src/api.rs` | 60, 133 | `gftd.murakumo.v1.` XRPC namespace | AT Protocol NSID is a server-side schema identifier, not client cluster identity. Renaming requires separate CF Worker + Lexicon update. |
| `src/models.rs` | 364 | `gftd/gftd-moe-moe-kyun` | HuggingFace model org/repo path — third-party model registry, not cluster identity. |
| `src/config.rs` | 143–144 | `gftd/swe-260316` alias | HuggingFace model alias — third-party model registry. |
| `src/daemon.rs` | 543 | `gftd/hayate-v4` | HuggingFace model path — third-party model registry. |

## Cutover procedure (when Step 8 fires)

1. Branch from main: `git checkout -b step8-murakumo-cluster-rename`.
2. Apply all renames above in **one commit**.
3. `cargo build --release` on macOS arm64 — must build clean.
4. Deploy to one Mac mini (`dan`) via `deploy-mesh.sh dan`. Verify `etzhayyim-murakumo murakumo-mesh status` returns from the new binary.
5. Run smoke test:
   - `etzhayyim-murakumo health` → control plane reachable
   - `etzhayyim-murakumo murakumo-mesh dns dan.mesh.etzhayyim.com` → resolves
   - Cell-runner picks up new env vars (verify with `launchctl print user/$(id -u)/com.etzhayyim.magatama-cell-runner`)
6. Deploy to remaining 9 nodes.
7. Decommission old `gftd-murakumo` binary + `~/.gftd/` config dirs across the fleet (one-time `rm -rf` per node after smoke test passes).
8. Merge PR.

## Do not

- Do not rename a subset of these (e.g. just the URL but not env vars). The runtime won't boot mid-rename.
- Do not introduce backward-compat shims (e.g. accepting both `GFTD_MURAKUMO` and `ETZHAYYIM_MURAKUMO`). Step 8 cutover is a clean break per repo-root `CLAUDE.md` Hard rules.
- Do not run the rename before legal registration completes (etzhayyim CLAUDE.md §Status row 8 master gate).
- Do not rename `MESH_KEY_CTX` without a separate fleet-coordinated protocol bump (see intentional remainders table above).

## Verification commands (post-cutover)

```bash
# No leftover gftd identifiers in this dir (other than this file and intentional remainders)
grep -rn "gftd" --include="*.rs" --include="*.sh" --include="*.toml" \
  | grep -v MIGRATION-NOTES.md \
  | grep -v "gftd-murakumo-mesh-v1" \
  | grep -v "gftd\.murakumo\.v1\." \
  | grep -v "gftd/swe-260316" \
  | grep -v "gftd/hayate-v4" \
  | grep -v "gftd/gftd-moe-moe-kyun"
# expected: zero matches

# Binary built
file target/release/etzhayyim-murakumo

# Config dir
ls -la ~/.etzhayyim/

# Launchd label
launchctl list | grep com.etzhayyim.murakumo-mesh
```
