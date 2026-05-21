# yata — Rust client crate workspace

Authoritative: [ADR-2605080000 §D5 + Appendix A](../../../90-docs/adr/2605080000-yatabase-yata-retail-cloud.md).

## Layout

```
50-clients/rust/yata/
├── Cargo.toml                   workspace + workspace.dependencies
├── README.md                    crates.io front page
├── CLAUDE.md                    THIS FILE
├── examples/
│   └── 01-quickstart.rs         minimal connect → migrate → insert → query
└── crates/
    ├── yata/                    facade (re-exports + prelude)  → published as `yata`
    ├── yata-core/               connection / Yata struct / errors
    ├── yata-schema/             VertexSpec / EdgeSpec traits
    ├── yata-derive/             #[derive(Vertex)] / #[derive(Edge)] proc-macros
    ├── yata-query/              type-safe SQL/PGQ builder
    ├── yata-sparql/             SPARQL 1.1 HTTP client
    ├── yata-stream/             streaming MV subscription (WS)
    ├── yata-mcp/                MCP server export
    └── yata-cli/                `yata` CLI binary
```

## Versioning

- All sub-crates share `version = "0.1.0"` from `[workspace.package]`.
- crates.io publish order on first release: `yata-schema → yata-derive →
  yata-core → yata-query → yata-sparql → yata-stream → yata-mcp → yata-cli → yata`.
- `[workspace.dependencies]` uses `path = ...` while developing in-tree;
  crates.io publish drops `path` and ships only `version`.

## MSRV

Rust **1.78** stable, edition **2024**. Anything that needs nightly
features stays out of the public API.

## Forbidden in this workspace

- `std::sync::Mutex` for hot-path connection pool. Use `tokio::sync::Mutex`
  or lock-free primitives.
- `unsafe` outside of `yata-derive` proc-macro internals (where syn
  occasionally requires it). Mark every `unsafe` block with a `// SAFETY:` comment.
- `panic!` inside library code — only `Result<_, YataError>`. CLI may
  panic on user error after printing a clear message.
- Direct `tokio-postgres::Connection::execute()` exposure. Wrap every
  query through `yata-query` so the client always knows the typed shape.
- `unwrap()` / `expect()` outside tests / examples.

## Status

| Phase | Scope                                             | State          |
|-------|---------------------------------------------------|----------------|
| 0.1   | API surface skeleton from ADR Appendix A          | **MVP, this commit** |
| 0.2   | yata-query real AST → SQL/PGQ emitter             | next           |
| 0.3   | yata-sparql / yata-stream / yata-mcp wiring       | next           |
| 0.4   | yata-cypher (P6 ADR)                              | server P3.x    |
| 0.5   | yata-bolt (Neo4j compat)                          | server P3.x    |

## Local dev

```bash
cd 50-clients/rust/yata
cargo check --workspace            # compile-only smoke
cargo build --workspace            # build all sub-crates
cargo build -p yata-cli            # build just the CLI binary
cargo run --example 01-quickstart  # run the example (needs yatabase host)
cargo test --workspace             # unit tests
```

## Publishing (first release)

```bash
# Pre-flight
cargo publish --dry-run -p yata-schema
cargo publish --dry-run -p yata-derive
# … etc

# Real publish
cargo publish -p yata-schema
cargo publish -p yata-derive
cargo publish -p yata-core
cargo publish -p yata-query
cargo publish -p yata-sparql
cargo publish -p yata-stream
cargo publish -p yata-mcp
cargo publish -p yata-cli
cargo publish -p yata
```

## CRITICAL: `path = …` removal at publish

`[workspace.dependencies]` here uses `path = "crates/<name>"` so in-tree
edits propagate without bumping versions. **Before `cargo publish`**,
the publish script (CI) substitutes `path = …` for `version = "0.1.0"`
in each leaf `Cargo.toml`'s `[dependencies]` block, then runs publish,
then reverts the change. crates.io rejects `path = …` in published
manifests — the runtime package tree it builds must be self-contained.

## Public crate name reservation

| crate          | crates.io name |
|----------------|----------------|
| yata           | `yata`         |
| yata-core      | `yata-core`    |
| yata-schema    | `yata-schema`  |
| yata-derive    | `yata-derive`  |
| yata-query     | `yata-query`   |
| yata-sparql    | `yata-sparql`  |
| yata-stream    | `yata-stream`  |
| yata-mcp       | `yata-mcp`     |
| yata-cli       | `yata-cli`     |

All 9 names confirmed unoccupied as of 2026-05-08. Reserve at the same
time as the v0.1 publish to prevent squatting.
