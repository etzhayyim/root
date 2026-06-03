# yata — Rust client for [yatabase](https://yatabase.etzhayyim.com)

> Real-time graph database with integrated Supabase-style object storage.
> PG-compatible reads, SPARQL, S3-compatible upload, vector search, OWL
> reasoning, AT Protocol federation — and one bill, BWA-free egress.

[![crates.io](https://img.shields.io/crates/v/yata.svg)](https://crates.io/crates/yata)
[![docs.rs](https://docs.rs/yata/badge.svg)](https://docs.rs/yata)
[![License](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)
[![MSRV](https://img.shields.io/badge/MSRV-1.78-orange.svg)](#msrv)

```toml
[dependencies]
yata = { version = "0.1", features = ["derive"] }
tokio = { version = "1", features = ["full"] }
```

## Quickstart

```rust
use yata::prelude::*;

#[derive(Vertex, Debug, Clone)]
#[yata(label = "person")]
struct Person {
    #[yata(pk)]
    id: String,
    name: String,
    age: i32,
    #[yata(vector(dim = 768))]
    embedding: Vec<f32>,
}

#[derive(Edge, Debug, Clone)]
#[yata(type = "knows", from = Person, to = Person)]
struct Knows {
    #[yata(pk)]
    id: String,
    since: chrono::DateTime<chrono::Utc>,
    weight: f32,
}

#[tokio::main]
async fn main() -> yata::Result<()> {
    // Connect — DSN works with `sk_live_yata_*` Bearer or `psql://` URL.
    let y = Yata::connect("yatabase://sk_live_yata_xxx@yatabase.etzhayyim.com/my-db").await?;

    // Type-safe schema migration. Idempotent.
    y.migrate::<(Person, Knows)>().await?;

    // Insert.
    y.insert(Person {
        id: "alice".into(),
        name: "Alice".into(),
        age: 30,
        embedding: vec![0.1; 768],
    }).await?;

    // Type-safe traversal.
    let friends: Vec<Person> = y
        .from::<Person>().eq("id", "alice")
        .out::<Knows>()
        .to::<Person>()
        .limit(10)
        .fetch().await?;

    // Hybrid graph + vector search.
    let query_vec = vec![0.1; 768];
    let similar: Vec<Person> = y
        .from::<Person>()
        .knn(&query_vec, 10)
        .out::<Knows>()
        .fetch().await?;

    // SPARQL escape hatch (Phase 2 will add full Cypher).
    let _rows = y.sparql(r#"
        SELECT ?friend WHERE { :alice :knows ?friend . }
    "#).await?;

    Ok(())
}
```

## Features

| feature        | default | description                                  |
|----------------|---------|----------------------------------------------|
| `query`        | ✓       | type-safe SQL/PGQ builder                    |
| `derive`       | ✓       | `#[derive(Vertex)]` + `#[derive(Edge)]`      |
| `sparql`       | —       | SPARQL 1.1 HTTP client                       |
| `stream`       | —       | streaming MV subscription (WebSocket)        |
| `mcp`          | —       | embed an MCP server exposing your graph as tools |
| `cypher`       | —       | Cypher → SQL/PGQ translator (P3.x)           |
| `bolt`         | —       | Neo4j-compat Bolt protocol (P3.x)            |
| `cli`          | —       | bring `yata` CLI binary into scope           |
| `tokio-rt`     | ✓       | tokio runtime                                |
| `async-std-rt` | —       | async-std runtime alternative                |

## CLI

The `yata` binary is a thin frontend over the same client API.

```bash
cargo install yata-cli

yata init                            # ~/.yata/config.toml
yata connect                         # interactive shell (psql-like)
yata schema show
yata mv list
yata mv tail alice_friends
yata reason owl rl
yata shacl validate shapes.ttl
yata import people.csv --label person
yata export sparql 'SELECT * WHERE { ?s ?p ?o } LIMIT 10' --format jsonld
yata mcp serve --port 8765           # expose all queries as MCP tools
yata bench                           # built-in latency / throughput
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ yata (facade)                                                   │
│   re-exports + prelude                                          │
├─────────────────────────────────────────────────────────────────┤
│ yata-core  ─┬─ tokio-postgres (PG protocol)                     │
│             ├─ rustls (TLS)                                     │
│             └─ async connection pool                            │
│ yata-schema ── VertexSpec / EdgeSpec / Column                   │
│ yata-derive ── #[derive(Vertex)] / #[derive(Edge)]              │
│ yata-query  ── type-safe builder → SQL/PGQ AST                  │
│ yata-sparql ── reqwest HTTP /sparql                             │
│ yata-stream ── tokio-tungstenite /mv?subscribe                  │
│ yata-mcp    ── rmcp server (your graph as MCP tools)            │
│ yata-cli    ── clap-derive frontend over yata + yata-mcp        │
└─────────────────────────────────────────────────────────────────┘
```

## Status

**v0.1 (skeleton)** — public API surface from
[ADR-2605080000 §D5](https://github.com/etzhayyim/etzhayyim-root/blob/main/90-docs/adr/2605080000-yatabase-yata-retail-cloud.md).
Many functions are `todo!()` while the
[yatabase.etzhayyim.com server](https://yatabase.etzhayyim.com) ships P3.2+
surfaces. Track the roadmap at
[`60-apps/etzhayyim-project-yatabase/CLAUDE.md`](https://github.com/etzhayyim/etzhayyim-root/blob/main/60-apps/etzhayyim-project-yatabase/CLAUDE.md).

## MSRV

Rust **1.78** (stable, 2024 edition).

## License

Dual-licensed under either of:

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE))
- MIT License ([LICENSE-MIT](LICENSE-MIT))

at your option. Contributions are dual-licensed under the same terms.
