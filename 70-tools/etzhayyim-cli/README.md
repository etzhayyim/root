# etzhayyim-cli (`e7m`)

Multi-purpose Go CLI for the etzhayyim monorepo.

Binary is built and installed as `e7m` (legacy alias: `etzhayyim`). Build:

```bash
cd 70-tools/etzhayyim-cli
go build -o /opt/homebrew/bin/e7m .
```

## Commands

| Command | Purpose | Doc |
|---|---|---|
| `e7m build` | TinyGo WASM component → wasm-tools componentize (kotodama WIT) | `build.go` |
| `e7m build-server` | kotodama-server binary + Docker image (zigbuild cross-compile) | `build_server.go` |
| `e7m deploy` | Cloudflare Container deploy (kotodama.toml + etzhayyim.json → wrangler deploy + smoke) | `deploy.go` |
| `e7m plugin` | Manage build tools (wasm-tools, tinygo adapters) | `plugin.go` |
| `e7m bench` | Dispatch baien benches (micro / core4) | `bench.go` |
| `e7m version` | Print version | `main.go` |

Run `e7m <cmd> --help` for command-specific flags.

## `e7m bench` (baien benches)

Added 2026-05-23 per ADR-2605092350 (baien) and ADR-2605202345 (EVO-X2
fleet). Default host = `evo` (EVO-X2 GMKtec, gad/192.168.1.22),
default model = `microsoft/bitnet-b1.58-2B-4T-bf16`.

```bash
e7m bench list                                   # benches + frontier reference
e7m bench micro                                  # 15-prompt rule-based, ~5 min
e7m bench micro --limit 3                        # quick sanity check
e7m bench core4 --only ifeval                    # one Core 4 task
e7m bench core4                                  # all 4 sequential (~4h on EVO-X2 CPU bf16)
e7m bench micro --host judah                     # alternative fleet node
```

Results land in `90-docs/baien/<bench>-<YYMMDD>/`. The microbench Python
source is bundled into the Go binary via `//go:embed`; `lm-eval` is
expected to be pre-installed on the remote host (`python -m pip install
lm-eval[ifeval]`).

GPQA Diamond requires HuggingFace authentication for the gated
`Idavidrein/gpqa` dataset — set `HF_TOKEN` on the remote host before
running `e7m bench core4 --only gpqa_diamond_zeroshot`.

See `90-docs/baien/frontier-bench-snapshot-260523.md` §E for full
context.
