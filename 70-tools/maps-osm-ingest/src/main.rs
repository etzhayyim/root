//! maps-osm-ingest — OSM planet PBF ingest → RisingWave (vertex_osm_element + edges).
//!
//! Streams OSM PBF nodes/ways/relations via `osmpbf::ElementReader::par_map_reduce`,
//! converts to typed rows, and COPY-streams them into RisingWave over the Postgres
//! wire protocol. Three parallel writer streams (node / way / relation) saturate
//! the DB side; a bounded mpsc (depth 16) backpressures the decoder.
//!
//! B2 PBF cache: if B2 credentials are supplied, the tool checks B2 for a
//! previously cached PBF before downloading from Geofabrik.  The B2 key is:
//!   `{b2_pbf_prefix}/{source_did}/{today_date}/planet.osm.pbf`
//!
//! Run tracking: every execution records a `vertex_osm_ingest_run` row + periodic
//! `vertex_osm_ingest_cursor` rows so ops can monitor mid-run progress.

mod b2;
mod checkpoint;
mod reader;
mod run_tracker;
mod transform;
mod writer;

use anyhow::{Context, Result};
use b2::B2Client;
use clap::Parser;
use futures::stream::StreamExt;
use run_tracker::RunTracker;
use signal_hook::consts::signal::{SIGINT, SIGTERM};
use signal_hook_tokio::Signals;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::{mpsc, Notify};
use tracing::info;
use tracing_subscriber::EnvFilter;

#[derive(Parser, Debug, Clone)]
#[command(name = "maps-osm-ingest", version, about)]
pub struct Args {
    /// HTTPS URL for the OSM PBF (mutually exclusive with --pbf-path).
    #[arg(long, env = "PBF_URL")]
    pub pbf_url: Option<String>,

    /// Local filesystem path to a PBF (mutually exclusive with --pbf-url).
    #[arg(long, env = "PBF_PATH")]
    pub pbf_path: Option<PathBuf>,

    /// Postgres URL for RisingWave (e.g. postgres://root@host:4566/dev).
    #[arg(long, env = "KOTOBA_URL")]
    pub db: String,

    /// Source DID recorded on every row.
    #[arg(long, env = "SOURCE_DID", default_value = "did:web:maps.etzhayyim.com:planet")]
    pub source_did: String,

    /// Owner DID (defaults to source DID if omitted).
    #[arg(long, env = "OWNER_DID")]
    pub owner_did: Option<String>,

    /// Rows per COPY batch per writer stream.
    #[arg(long, env = "BATCH_SIZE", default_value_t = 100_000)]
    pub batch_size: usize,

    /// PBF decode parallelism (rayon threads inside osmpbf).
    #[arg(long, env = "PARALLELISM", default_value_t = 4)]
    pub parallelism: usize,

    /// Optional R2 object key for checkpoint persistence.
    #[arg(long, env = "CHECKPOINT_KEY")]
    pub checkpoint_key: Option<String>,

    /// R2 endpoint base URL (e.g. https://<acct>.r2.cloudflarestorage.com/<bucket>).
    #[arg(long, env = "R2_ENDPOINT")]
    pub r2_endpoint: Option<String>,

    /// S2 cell level (default 16 ≈ 80m).
    #[arg(long, env = "S2_LEVEL", default_value_t = 16)]
    pub s2_level: u64,

    /// Geohash length (default 8 ≈ 38m).
    #[arg(long, env = "GEOHASH_LEN", default_value_t = 8)]
    pub geohash_len: usize,

    /// Scratch dir for downloaded PBF when --pbf-url is used.
    #[arg(long, env = "SCRATCH_DIR", default_value = "/scratch")]
    pub scratch_dir: PathBuf,

    /// RisingWave dml_rate_limit (rows/sec per parallelism). Prevents B2 SlowDown
    /// during bulk ingest. Recommended: 200000 for continent runs, 100000 for planet.
    #[arg(long, env = "DML_RATE_LIMIT")]
    pub dml_rate_limit: Option<u64>,

    // ── B2 PBF cache ──────────────────────────────────────────────────────────

    /// B2 application key ID for PBF cache (optional).
    /// When set together with --b2-app-key and --b2-bucket-name, the tool
    /// checks B2 for a cached PBF before downloading from --pbf-url.
    #[arg(long, env = "B2_KEY_ID")]
    pub b2_key_id: Option<String>,

    /// B2 application key for PBF cache (optional).
    #[arg(long, env = "B2_APP_KEY")]
    pub b2_app_key: Option<String>,

    /// B2 bucket name for PBF cache (optional).
    /// Required when b2_key_id is an account-master key (not bucket-scoped).
    #[arg(long, env = "B2_BUCKET_NAME", default_value = "")]
    pub b2_bucket_name: String,

    /// B2 key prefix for cached PBFs.
    #[arg(long, env = "B2_PBF_PREFIX", default_value = "maps/osm-pbf")]
    pub b2_pbf_prefix: String,

    /// v0.5.0: NATS JetStream URL.  When set, every inserted row is also
    /// published to `ingest.osm.element.{n|w|r}` / `ingest.osm.edge.*`
    /// subjects (additive — does not replace SQL INSERT).  Failure to
    /// publish does not block the SQL path.  See ADR-2605091700 Phase 4.
    #[arg(long, env = "NATS_URL", default_value = "")]
    pub nats_url: Option<String>,
}

#[tokio::main(flavor = "multi_thread")]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .json()
        .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")))
        .with_target(true)
        .init();

    let args = Args::parse();
    info!(?args.source_did, batch_size = args.batch_size, "maps-osm-ingest starting");

    // Signal handling: set Notify when SIGTERM/SIGINT arrives.
    let shutdown = Arc::new(Notify::new());
    let shutdown_signal = shutdown.clone();
    let signals = Signals::new([SIGTERM, SIGINT]).context("signal handler install")?;
    tokio::spawn(async move {
        let mut s = signals.fuse();
        if let Some(sig) = s.next().await {
            info!(signal = sig, "shutdown requested");
            shutdown_signal.notify_waiters();
        }
    });

    // ── today's date for B2 cache key ─────────────────────────────────────────
    let today_date = chrono::Utc::now().format("%Y-%m-%d").to_string();

    // ── B2 cache key ──────────────────────────────────────────────────────────
    let b2_cache_key = format!(
        "{}/{}/{}/planet.osm.pbf",
        args.b2_pbf_prefix, args.source_did, today_date
    );

    // ── start run tracker (best-effort; errors skip tracking, not abort) ──────
    let tracker: Option<Arc<RunTracker>> = {
        let pbf_url_for_tracker = args.pbf_url.as_deref();
        let b2_key_for_tracker = if args.b2_key_id.is_some() {
            Some(b2_cache_key.as_str())
        } else {
            None
        };
        match RunTracker::start(&args.db, &args.source_did, pbf_url_for_tracker, b2_key_for_tracker).await {
            Ok(t) => {
                info!(run_id = %t.run_id, "run tracking active");
                Some(Arc::new(t))
            }
            Err(e) => {
                tracing::warn!(error = ?e, "run tracker unavailable (tables may not be migrated yet) — continuing without tracking");
                None
            }
        }
    };

    // ── resolve PBF source → local path ───────────────────────────────────────
    let result = run_ingest(&args, &today_date, &b2_cache_key, tracker.clone(), shutdown).await;

    // ── propagate tracker result ───────────────────────────────────────────────
    if let Err(ref e) = result {
        if let Some(ref t) = tracker {
            t.fail(&format!("{e:#}")).await.ok();
        }
    }

    result
}

async fn run_ingest(
    args: &Args,
    today_date: &str,
    b2_cache_key: &str,
    tracker: Option<Arc<RunTracker>>,
    shutdown: Arc<Notify>,
) -> Result<()> {
    tokio::fs::create_dir_all(&args.scratch_dir).await.ok();
    let dest = args.scratch_dir.join("planet.osm.pbf");

    let pbf_path = match (&args.pbf_url, &args.pbf_path) {
        (Some(url), None) => {
            // B2 cache check — only when all three B2 args are supplied
            let b2_client = if let (Some(key_id), Some(app_key)) =
                (&args.b2_key_id, &args.b2_app_key)
            {
                match B2Client::authorize(key_id, app_key, &args.b2_bucket_name).await {
                    Ok(c) => Some(c),
                    Err(e) => {
                        tracing::warn!(error = ?e, "B2 authorize failed — skipping cache");
                        None
                    }
                }
            } else {
                None
            };

            let mut b2_hit = false;
            if let Some(ref b2) = b2_client {
                info!(key = %b2_cache_key, "checking B2 PBF cache");
                match b2.exists(b2_cache_key).await {
                    Ok(true) => {
                        info!(key = %b2_cache_key, "B2 cache HIT — downloading from B2");
                        match b2.download(b2_cache_key).await {
                            Ok(Some(bytes)) => {
                                let size = bytes.len() as u64;
                                let sha256 = b2::sha256_hex(&bytes);
                                tokio::fs::write(&dest, &bytes).await.context("write B2 bytes to scratch")?;
                                info!(bytes = size, dest = %dest.display(), "B2 download written to scratch");
                                if let Some(ref t) = tracker {
                                    t.set_download_complete(&sha256, size).await.ok();
                                    t.touch_pbf_cache(today_date).await;
                                }
                                b2_hit = true;
                            }
                            Ok(None) => {
                                tracing::warn!(key = %b2_cache_key, "B2 said exists but download returned 404 — falling back to URL");
                            }
                            Err(e) => {
                                tracing::warn!(error = ?e, "B2 download error — falling back to URL");
                            }
                        }
                    }
                    Ok(false) => {
                        info!(key = %b2_cache_key, "B2 cache MISS — downloading from origin URL");
                    }
                    Err(e) => {
                        tracing::warn!(error = ?e, "B2 exists check failed — falling back to URL");
                    }
                }
            }

            if !b2_hit {
                // Download from origin URL
                reader::download_pbf(url, &dest).await.context("PBF download")?;

                // Compute sha256 and size for tracker
                // Note: for multi-GB files we avoid reading the whole file back into RAM
                // by using incremental hashing in a background task.
                let size = tokio::fs::metadata(&dest)
                    .await
                    .map(|m| m.len())
                    .unwrap_or(0);
                let sha256 = compute_file_sha256(&dest).await.unwrap_or_default();
                info!(bytes = size, sha256 = %sha256, "PBF download verified");

                if let Some(ref t) = tracker {
                    t.set_download_complete(&sha256, size).await.ok();
                    // Record in pbf_cache so future runs can skip the download
                    // (operator must manually upload to B2; this is just the manifest row)
                    if b2_client.is_some() {
                        t.record_pbf_cache(url, b2_cache_key, size, &sha256, today_date).await;
                    }
                }
            }

            dest
        }
        (None, Some(p)) => p.clone(),
        _ => anyhow::bail!("exactly one of --pbf-url or --pbf-path required"),
    };

    if let Some(ref t) = tracker {
        t.set_phase("node").await.ok();
    }

    // Bounded mpsc: depth 16 per type → decoder blocks if writer stalls (never OOM).
    let (node_tx, node_rx) = mpsc::channel::<Vec<transform::VertexOsmElementRow>>(16);
    let (way_tx, way_rx) = mpsc::channel::<transform::WayBatch>(16);
    let (rel_tx, rel_rx) = mpsc::channel::<transform::RelationBatch>(16);

    let owner_did = args.owner_did.clone().unwrap_or_else(|| args.source_did.clone());

    // Spawn 3 writer tasks (parallel COPY to RisingWave).
    let w_args = args.clone();
    let w_owner = owner_did.clone();
    let node_tracker = tracker.clone();
    let node_writer = tokio::spawn(async move {
        writer::run_node_writer(&w_args, &w_owner, node_rx, node_tracker).await
    });
    let w_args = args.clone();
    let w_owner = owner_did.clone();
    let way_tracker = tracker.clone();
    let way_writer = tokio::spawn(async move {
        writer::run_way_writer(&w_args, &w_owner, way_rx, way_tracker).await
    });
    let w_args = args.clone();
    let w_owner = owner_did.clone();
    let rel_tracker = tracker.clone();
    let rel_writer = tokio::spawn(async move {
        writer::run_relation_writer(&w_args, &w_owner, rel_rx, rel_tracker).await
    });

    // Decoder runs on a blocking thread (osmpbf is synchronous / rayon internally).
    let d_args = args.clone();
    let d_owner = owner_did.clone();
    let d_shutdown = shutdown.clone();
    let decoder = tokio::task::spawn_blocking(move || {
        reader::decode_pbf(
            &pbf_path,
            &d_args,
            &d_owner,
            node_tx,
            way_tx,
            rel_tx,
            d_shutdown,
        )
    });

    let (dec, nw, ww, rw) = tokio::join!(decoder, node_writer, way_writer, rel_writer);
    dec.context("decoder join")??;
    let nodes_written = nw.context("node writer join")??;
    let ways_written = ww.context("way writer join")??;
    let rels_written = rw.context("relation writer join")??;

    if let Some(ref t) = tracker {
        t.complete(nodes_written, ways_written, rels_written).await.ok();
    }

    if let Some(key) = args.checkpoint_key.as_deref() {
        checkpoint::mark_complete(args, key).await.ok();
    }

    info!(
        nodes = nodes_written,
        ways = ways_written,
        rels = rels_written,
        "maps-osm-ingest done"
    );
    Ok(())
}

/// Compute SHA-256 hex digest of a file using streaming reads (avoids loading
/// multi-GB PBFs into RAM).
async fn compute_file_sha256(path: &std::path::Path) -> Result<String> {
    use sha2::Digest as _;
    use tokio::io::AsyncReadExt as _;

    let mut file = tokio::fs::File::open(path).await.context("open file for sha256")?;
    let mut hasher = sha2::Sha256::new();
    let mut buf = vec![0u8; 1024 * 1024]; // 1 MiB chunks
    loop {
        let n = file.read(&mut buf).await.context("read chunk for sha256")?;
        if n == 0 { break; }
        hasher.update(&buf[..n]);
    }
    Ok(hex::encode(hasher.finalize()))
}
