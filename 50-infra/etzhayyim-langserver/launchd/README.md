# launchd templates — `com.etzhayyim.langserver.*`

One plist per (host, language). Naming convention:

```
com.etzhayyim.langserver.<lang>
  → e.g. com.etzhayyim.langserver.rust, .python, .typescript, .go, .lua, .ruby
```

This sits as a sibling of `com.etzhayyim.kotodama-cell-runner` and uses the same
`@@PLACEHOLDER@@` substitution style.

## Files

| File | Role |
|---|---|
| `com.etzhayyim.langserver.template.plist` | launchd job definition (per-language) |
| `run-langserver.sh` | wrapper script invoked by the plist; execs the LSP binary |
| `README.md` | this file |

## Substitution scheme

`install.sh` (lands in L6) will sed these placeholders per host/language:

| Placeholder | Source | Resolved at |
|---|---|---|
| `@@LANG@@` | `--lang <id>` arg to install.sh | L2 (here) |
| `@@USERNAME@@` | `whoami` on the target host | L1 (probe) |
| `@@REPO_PATH@@` | repo checkout path on the host | L1 |
| `@@WORKSPACE@@` | indexed workspace (defaults to repo) | L2 |
| `@@LOG_DIR@@` | `/Users/<user>/.etzhayyim/log` | L2 |
| `@@LISTEN_ADDR@@` | transport endpoint (`both:<sock>\|<bind>:<port>` default) | **L4** (socket) then **L5** (mesh) |
| `@@LSP_BIN_PATH@@` | path to LSP binary on the host | **L3** (binary pins) |
| `@@LSP_ARGS@@` | LSP CLI args (e.g. `--stdio`) | **L3** |

Placeholders marked **L3+** are intentionally unresolved at L2 — the plist is
a **dry-run template only** per CLAUDE.md "ハードウェア未確認段階では plist
は dry-run のみ" constraint. Loading these into launchd is gated on:

1. L1 hardware probe committed (`hw.*` blocks in `hosts.toml`)
2. L3 binary pins committed (`@@LSP_BIN_PATH@@` resolvable per host)
3. User explicit confirmation per CLAUDE.md

## Transport modes (L4)

`run-langserver.sh` dispatches on the `ETZHAYYIM_LISTEN_ADDR` env var:

| Form | Effect |
|---|---|
| `stdio` | Raw stdio. Debugging only — no remote clients. |
| `unix:<path>` | Single Unix domain socket via `socat UNIX-LISTEN:...,fork`. |
| `tcp:<bind>:<port>` | Single TCP listener via `socat TCP-LISTEN:...,fork`. |
| `both:<sock>\|<bind>:<port>` | Two parallel listeners (the default). |

If `ETZHAYYIM_LISTEN_ADDR` is unset, the wrapper auto-resolves it to `both:` mode
using `transports.toml` (per-language port + socket basename allocation).

Concurrency: socat `fork` mode spawns one LSP per client connection. This trades
cold-start cost for client isolation. A future multiplexer (lsp-proxy /
lsp-multiplexer) can replace fork mode without touching the plist template.

`pty` is **intentionally OFF** — LSP framing is raw JSON-RPC; a pty would inject
terminal control sequences and break the protocol.

## Lifecycle settings (mirrors kotodama-cell-runner conventions)

- **RunAtLoad** = `true` — start at LaunchAgent load / user login
- **KeepAlive.SuccessfulExit** = `false` — restart on crash (non-zero exit)
- **KeepAlive.NetworkState** = `true` — restart when network returns (mesh-aware)
- **ThrottleInterval** = `15` — anti-flap minimum 15s between restarts
- **ProcessType** = `Background` — macOS background QoS, no App Nap
- **Nice** = `5` — yield to interactive workloads
- **WorkingDirectory** = `@@WORKSPACE@@` — relevant for LSPs that infer project root

## Logs

```
/Users/<tribe>/.etzhayyim/log/langserver.<lang>.stdout.log
/Users/<tribe>/.etzhayyim/log/langserver.<lang>.stderr.log
```

L7 will optionally tee these into NATS JetStream subject
`etzhayyim.langserver.<host>.<lang>.log` for fleet-wide tail.

## Why this layer is leaf-side (L2)

The launchd contract — *what process to run, with what env, under what restart
policy* — depends on **nothing upstream** in this stack. Transport (L4),
mesh exposure (L5), health checks (L6), observability (L7), editor configs (L8),
and Pregel integration (L9) all build on top of this contract. Reverse-topo
positions L2 right after L1 (the host inventory it parameterizes).

## Do not (per CLAUDE.md)

- Do **not** `launchctl load` any generated plist until L1 hardware probe is
  committed and user has explicitly confirmed.
- Do **not** introduce a `etzhayyim-` / `com.etzhayyim.` Label. `com.etzhayyim.*` only.
- Do **not** add proprietary log shipping; L7 stays on Apache 2.0 OSS (NATS).
