# editor-configs — remote-LSP attach for nvim / Helix / Zed / VSCode

Each subdirectory contains a config snippet that wires the editor's
LSP client to the fleet-hosted langservers via `scripts/attach-langserver.sh`
(socat stdio ↔ TCP bridge).

## Design

Single source of truth: `scripts/lsp-fleet.json` (generated from
`hosts.toml` + `transports.toml` + `mesh.toml`).

Each editor config calls `attach-langserver.sh <lang>` as a custom LSP
binary. The shim resolves mesh-IP and port at invocation time, so editor
configs DON'T encode IPs — when fleet topology changes, only the registry
needs regen (`./scripts/generate-fleet-registry.sh`), no editor config edits.

```
editor (stdio) ──► attach-langserver.sh ──► socat ──► tcp://<mesh-ip>:<port> ──► fleet LSP
```

## Per-editor support

| Editor | Mechanism | File |
|---|---|---|
| Neovim | Lua plugin using `vim.lsp.rpc.connect()` (TCP-native, no socat) | `nvim/etzhayyim-langserver.lua` |
| Helix  | `languages.toml` `command = attach-langserver.sh` | `helix/languages.toml.partial` |
| Zed    | `lsp.<server>.binary` override | `zed/settings.partial.json` |
| VSCode | per-extension binary path override (varies) | `vscode/settings.partial.json` |

Neovim is special-cased: it has a built-in TCP transport (`vim.lsp.rpc.connect`),
so it skips socat and connects directly. The other three editors rely on
`attach-langserver.sh` as a socat shim because they only accept stdio LSP.

## Install

1. Refresh the fleet registry:
   ```bash
   cd 50-infra/etzhayyim-langserver
   ./scripts/generate-fleet-registry.sh
   ```

2. **Neovim**: add the plugin path to your runtimepath, then:
   ```lua
   require("etzhayyim-langserver").setup({})
   ```

3. **Helix**: copy `helix/languages.toml.partial` into
   `~/.config/helix/languages.toml` and replace `/path/to/etzhayyim/root`
   with your checkout path.

4. **Zed**: merge `zed/settings.partial.json` into `~/.config/zed/settings.json`.

5. **VSCode**: merge `vscode/settings.partial.json` into your workspace's
   `.vscode/settings.json`. See caveats in that file — VSCode LSP extensions
   vary in how they accept a custom binary path.

## Caveats

- `attach-langserver.sh` requires `socat` (L3 prereq, `brew install socat`).
- Editors that hold a long-lived LSP connection are fine. socat `fork` on
  the fleet side spawns one LSP per connection — no client-side change
  needed.
- Cold-start: each new connection re-indexes the workspace. Workspace cache
  on the fleet side (rust-analyzer `~/.cache/rust-analyzer`, etc.) survives
  between connections but indexing time is paid per new client session.
- Workspace files: the fleet LSP indexes the workspace on the MAC MINI it
  runs on (`@@WORKSPACE@@` from the plist). It does NOT index your local
  editor's file tree. For now, sync via existing flows (git pull on the mini)
  or use the fleet LSP only for substrate code that lives on the mini.

## Future (L9)

L9 will add a `LangserverQueryCell` so Pregel cells can perform
symbol-aware refactors across all fleet workspaces. Editor configs in this
directory remain the user-facing surface for human editors.
