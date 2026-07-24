# @etzhayyim/e7m-cli

`e7m` — short binary alias for `etzhayyim`. Unified developer CLI for the
`etzhayyim/root` monorepo, owned by **etzhayyim** (operating entity, per repo-root
[`CLAUDE.md`](../../CLAUDE.md) and [ADR-2605192100 Mission Charter](../../90-docs/adr/2605192100-etzhayyim-mission-charter.md)).

Sibling CLI: [`70-tools/etzhayyim-cli/`](../etzhayyim-cli/) — Go-based, smaller
domain tool for Cloudflare Containers (build/deploy). Coexistence is intended;
eventual merge ADR may consolidate. The earlier `70-tools/etzhayyim/` Go CLI was
removed 2026-05-20 — its monorepo-internal surface is now covered by `e7m`.

## Install (in-monorepo dev)

```bash
cd 70-tools/e7m-cli
npm install
npm run build
node bin/e7m.js --help
# or, link globally:
npm link
e7m --help
```

## Commands

### `e7m doctor`

Diagnose local toolchain (node / pnpm / tinygo / wasm-tools / wrangler / docker /
forge / anvil / cast / go). Exits non-zero if any expected tool is missing.

### `e7m did verify [--uniresolver]`

Fetch `https://etzhayyim.com/.well-known/did.json`, validate
`id == did:web:etzhayyim.com`, `@context`, `verificationMethod`, `service`.
Optionally cross-check against `dev.uniresolver.io`.

### `e7m council status`

Parse [`COUNCIL.md`](../../COUNCIL.md) roster table and RFP deadline; show seat
status (per ADR-2605192300 Bootstrap Council).

### `e7m charter check` / `e7m charter apply`

Thin wrappers over
[`70-tools/charter-rider-applicator/verify.sh` and `apply.sh`](../charter-rider-applicator/)
(per ADR-2605192200 Charter Compliance Rider v2.0).

### `e7m agent <dev|build|up> [project]`

LangGraph CLI wrappers for apps under `60-apps/`. Accepts either the bare app
name (`yoro`) or the legacy `etzhayyim-project-*` form.

### `e7m actor build <dir> [--extension]`

Build a Kotodama / W Protocol WASM component (tinygo + wasm-tools). The WIT
directory auto-resolves to `40-engine/kotoba/crates/kotoba-kotodama/wit` (or `10-protocol/wproto/wit`
with `--extension`), or the value of `$KOTODAMA_WIT_DIR` if set.

### `e7m actor deploy <dir>`

Run `wrangler deploy` in the given component directory.

### `e7m contract gen lexicons`

Generate TypeScript bindings from `00-contracts/lexicons/**/*.json` via
`@atproto/lex-cli` into `orgs/etzhayyim/com-etzhayyim-sdk/src/generated/` (override
with `--out`).

### `e7m contract validate [target]`

Recursively JSON-parse-check every `*.json` under `00-contracts/lexicons/` +
`00-contracts/schemas/` (or a custom target).

### `e7m graph schema migrate` / `e7m graph cypher compile`

Placeholder hooks for the Kagami graph stack — not yet implemented.

### `e7m dev infra [lancedb|yata|all] [--down]` / `e7m dev app <name>`

Bring up the small set of local `docker-compose` services that currently exist
under `50-infra/`, or run `pnpm dev` (falls back to `npm run dev`) inside
`60-apps/<name>/`.

## Substrate boundary

This CLI MUST NOT introduce direct imports of `@atproto/api`, `viem`,
`@noble/ciphers`, IPFS clients, or `@signalapp/libsignal-client` into app code
(per repo-root `CLAUDE.md` Substrate boundary table). It only orchestrates
external tooling (tinygo, wasm-tools, wrangler, langgraph-cli, docker, bash
scripts) and fetches public HTTPS endpoints (`did.json`).

## Versioning

`0.2.0` — added `doctor` / `did` / `council` / `charter`; wired monorepo root
detection via `deps.toml`; replaced placeholder bodies with working
implementations or honest "not implemented" exits.
