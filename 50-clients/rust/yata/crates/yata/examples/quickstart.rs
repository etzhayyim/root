//! 01-quickstart.rs — minimal `yata` client example.
//!
//! Run with:
//!
//! ```bash
//! cd 50-clients/rust/yata
//! YATA_DSN="yatabase://sk_live_yata_xxx@yatabase.etzhayyim.com/yata_xxx" \
//!     cargo run --example 01-quickstart
//! ```
//!
//! v0.1 skeleton — `Yata::connect` succeeds even without a live
//! yatabase host; downstream calls (migrate / insert / fetch) return
//! `YataError::NotImplemented`. Use this example to sanity-check that
//! the public API surface compiles and that `cargo run --example`
//! resolves through the workspace.

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
    weight: f32,
}

#[tokio::main]
async fn main() -> Result<()> {
    let dsn = std::env::var("YATA_DSN")
        .unwrap_or_else(|_| "yatabase://sk_live_yata_xxx@yatabase.etzhayyim.com/yata_xxx".into());

    let y = Yata::connect(&dsn).await?;
    println!("connected: host={} db={}", y.dsn().host, y.dsn().database);

    // The next four calls all return YataError::NotImplemented in v0.1.
    // Wrapped in `match` so the example completes without an early exit.
    match y.migrate::<(Person, Knows)>().await {
        Ok(())  => println!("migrate: ok"),
        Err(e)  => println!("migrate: {e}"),
    }

    match y.insert(Person {
        id: "alice".into(),
        name: "Alice".into(),
        age: 30,
        embedding: vec![0.1; 768],
    }).await {
        Ok(())  => println!("insert: ok"),
        Err(e)  => println!("insert: {e}"),
    }

    let q = y
        .from::<Person>().eq("id", "alice")
        .out::<Knows>()
        .to::<Person>()
        .limit(10);
    println!("query plan (debug SQL): {}", q.to_sql());

    match q.fetch().await {
        Ok(rows) => println!("fetch: {} rows", rows.len()),
        Err(e)   => println!("fetch: {e}"),
    }

    Ok(())
}
