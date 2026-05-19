//! kg-appview entry point.

use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::Arc;

use anyhow::{Context, Result};
use tracing_subscriber::EnvFilter;

use kg_appview::{
    load::load_projection,
    server::serve,
    store::AppStore,
};

struct Args {
    kg_out: PathBuf,
    listen: SocketAddr,
}

fn parse_args() -> Result<Args> {
    let mut kg_out: Option<PathBuf> = None;
    let mut listen: Option<SocketAddr> = None;
    let mut it = std::env::args().skip(1);
    while let Some(a) = it.next() {
        match a.as_str() {
            "--kg-out" => {
                kg_out = Some(PathBuf::from(
                    it.next().context("--kg-out requires a value")?,
                ));
            }
            "--listen" => {
                let raw = it.next().context("--listen requires a value")?;
                listen = Some(raw.parse().context("invalid --listen address")?);
            }
            "--help" | "-h" => {
                print_help();
                std::process::exit(0);
            }
            other => anyhow::bail!("unknown flag: {other} (try --help)"),
        }
    }
    Ok(Args {
        kg_out: kg_out.unwrap_or_else(|| PathBuf::from("../kg-projector/out")),
        listen: listen.unwrap_or_else(|| "127.0.0.1:8080".parse().expect("static addr")),
    })
}

fn print_help() {
    println!("kg-appview — Stage K2.a of ADR-2605190900");
    println!();
    println!("Usage: kg-appview [--kg-out <dir>] [--listen <addr:port>]");
    println!();
    println!("Defaults:");
    println!("  --kg-out  ../kg-projector/out");
    println!("  --listen  127.0.0.1:8080");
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("kg_appview=info")),
        )
        .init();

    let args = parse_args()?;
    tracing::info!(
        kg_out = %args.kg_out.display(),
        listen = %args.listen,
        "starting kg-appview"
    );

    let store = AppStore::new()?;
    let stats = load_projection(&store, &args.kg_out)
        .with_context(|| format!("loading projection from {}", args.kg_out.display()))?;
    tracing::info!(
        nodes = stats.node_count,
        edges = stats.edge_count,
        triples = stats.triple_count,
        "projection loaded"
    );

    serve(Arc::new(store), args.listen).await
}
