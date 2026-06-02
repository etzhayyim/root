//! kg-appview entry point.

use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::Arc;

use anyhow::{Context, Result};
use tracing_subscriber::EnvFilter;

use kg_appview::{
    firehose::spawn_subscriber,
    load::{load_projection, LoadStats},
    replay::replay_snapshot_file,
    server::serve,
    store::AppStore,
};

struct Args {
    kg_out: Option<PathBuf>,
    snapshot_file: Option<PathBuf>,
    firehose_url: Option<String>,
    listen: SocketAddr,
}

fn parse_args() -> Result<Args> {
    let mut kg_out: Option<PathBuf> = None;
    let mut snapshot_file: Option<PathBuf> = None;
    let mut firehose_url: Option<String> = None;
    let mut listen: Option<SocketAddr> = None;
    let mut explicit_kg_out_disabled = false;
    let mut it = std::env::args().skip(1);
    while let Some(a) = it.next() {
        match a.as_str() {
            "--kg-out" => {
                let v = it.next().context("--kg-out requires a value")?;
                if v == "none" || v == "-" {
                    explicit_kg_out_disabled = true;
                } else {
                    kg_out = Some(PathBuf::from(v));
                }
            }
            "--snapshot-file" => {
                snapshot_file = Some(PathBuf::from(
                    it.next().context("--snapshot-file requires a value")?,
                ));
            }
            "--firehose-url" => {
                firehose_url = Some(it.next().context("--firehose-url requires a value")?);
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

    // Default --kg-out only kicks in when no other source is configured.
    if kg_out.is_none()
        && snapshot_file.is_none()
        && firehose_url.is_none()
        && !explicit_kg_out_disabled
    {
        kg_out = Some(PathBuf::from("../kg-projector/out"));
    }

    Ok(Args {
        kg_out,
        snapshot_file,
        firehose_url,
        listen: listen.unwrap_or_else(|| "127.0.0.1:8080".parse().expect("static addr")),
    })
}

fn print_help() {
    println!("kg-appview — ADR-2605190900 stages K2.a / K2.b / K2.c / K3.a");
    println!();
    println!("Usage: kg-appview [--kg-out <dir>] [--snapshot-file <path>] [--firehose-url <wss://...>] [--listen <addr:port>]");
    println!();
    println!("Cold-start sources (any combination, applied in order; later wins on node key conflict):");
    println!("  --kg-out <dir>          Load nodes/*.json + edges/*.json from a kg-projector out/ tree.");
    println!("                          Pass `none` to disable the default.");
    println!("  --snapshot-file <path>  Load a kg-projector bundle.jsonl file (K3.a).");
    println!();
    println!("Live-update source (optional):");
    println!("  --firehose-url <wss>    Subscribe to a Jetstream-format firehose for live");
    println!("                          com.etzhayyim.kg.* commits (K2.c).");
    println!();
    println!("Server:");
    println!("  --listen <addr:port>    Bind address. Default 127.0.0.1:8080.");
    println!();
    println!("Defaults: --kg-out ../kg-projector/out (auto-applied only when no other source is configured).");
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
        kg_out = ?args.kg_out,
        snapshot_file = ?args.snapshot_file,
        firehose_url = ?args.firehose_url,
        listen = %args.listen,
        "starting kg-appview"
    );

    let store = AppStore::new()?;
    let mut total = LoadStats::default();

    if let Some(dir) = &args.kg_out {
        let s = load_projection(&store, dir)
            .with_context(|| format!("loading projection from {}", dir.display()))?;
        tracing::info!(nodes = s.node_count, edges = s.edge_count, triples = s.triple_count, "kg-out loaded");
        total.add(&s);
    }
    if let Some(path) = &args.snapshot_file {
        let s = replay_snapshot_file(&store, path)
            .with_context(|| format!("replaying snapshot {}", path.display()))?;
        tracing::info!(nodes = s.node_count, edges = s.edge_count, triples = s.triple_count, "snapshot replayed");
        total.add(&s);
    }
    tracing::info!(
        total_nodes = total.node_count,
        total_edges = total.edge_count,
        total_triples = total.triple_count,
        "cold-start ingestion complete"
    );

    let store = Arc::new(store);
    if let Some(url) = args.firehose_url.clone() {
        let _handle = spawn_subscriber(store.clone(), url);
        tracing::info!("firehose subscriber spawned");
    }

    serve(store, args.listen).await
}
