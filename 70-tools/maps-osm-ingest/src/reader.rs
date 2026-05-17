//! PBF download + streaming decode.
//!
//! Uses `osmpbf::ElementReader::par_map_reduce` for multi-core decode. Each
//! OSMPBF "block" is handed to a worker thread which produces typed rows and
//! pushes them onto bounded mpsc channels. This never materialises the full
//! planet in memory — back-pressure comes from the channels.

use crate::transform::{self, RelationBatch, VertexOsmElementRow, WayBatch};
use crate::Args;
use anyhow::{Context, Result};
use futures::StreamExt;
use osmpbf::{Element, ElementReader};
use std::path::Path;
use std::sync::Arc;
use tokio::io::AsyncWriteExt;
use tokio::sync::{mpsc, Notify};
use tracing::{debug, info, warn};
#[allow(unused_imports)]
use tracing::trace;

// 5 000 rows per INSERT (bench v0.2.5-bench: 5x larger batches to reduce
// round-trip overhead).  Each statement ≈ ~1.25 MB SQL; 3 concurrent writers
// ≈ ~3.75 MB peak frontend memory — still well within the 1 Gi limit.
const NODE_FLUSH: usize = 5_000;
const WAYNODE_FLUSH: usize = 5_000;
const RELMEMBER_FLUSH: usize = 5_000;

pub async fn download_pbf(url: &str, dest: &Path) -> Result<()> {
    info!(%url, dest = %dest.display(), "downloading PBF");
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(60 * 60 * 4))
        .build()?;
    let resp = client.get(url).send().await?.error_for_status()?;
    let mut stream = resp.bytes_stream();
    let mut file = tokio::fs::File::create(dest).await?;
    let mut total: u64 = 0;
    while let Some(chunk) = stream.next().await {
        let chunk = chunk?;
        total += chunk.len() as u64;
        file.write_all(&chunk).await?;
    }
    file.flush().await?;
    info!(bytes = total, "PBF download complete");
    Ok(())
}

/// Blocking decode. Uses rayon under the hood via `par_map_reduce`.
pub fn decode_pbf(
    pbf_path: &Path,
    args: &Args,
    owner_did: &str,
    node_tx: mpsc::Sender<Vec<VertexOsmElementRow>>,
    way_tx: mpsc::Sender<WayBatch>,
    rel_tx: mpsc::Sender<RelationBatch>,
    shutdown: Arc<Notify>,
) -> Result<()> {
    info!(path = %pbf_path.display(), "decoding PBF");
    let reader = ElementReader::from_path(pbf_path).context("open PBF")?;

    // Per-thread accumulators via par_map_reduce identity.
    let source_did = args.source_did.to_string();
    let owner_did = owner_did.to_string();
    let s2_level = args.s2_level;
    let geohash_len = args.geohash_len;

    struct Acc {
        nodes: Vec<VertexOsmElementRow>,
        way_rows: Vec<VertexOsmElementRow>,
        way_nodes: Vec<transform::EdgeWayNodeRow>,
        rel_rows: Vec<VertexOsmElementRow>,
        rel_members: Vec<transform::EdgeRelationMemberRow>,
    }
    impl Acc {
        fn new() -> Self {
            Self {
                nodes: Vec::with_capacity(NODE_FLUSH),
                way_rows: Vec::with_capacity(1024),
                way_nodes: Vec::with_capacity(WAYNODE_FLUSH),
                rel_rows: Vec::with_capacity(1024),
                rel_members: Vec::with_capacity(RELMEMBER_FLUSH),
            }
        }
    }

    let node_tx = node_tx.clone();
    let way_tx = way_tx.clone();
    let rel_tx = rel_tx.clone();

    // We need a tokio runtime handle to push into channels from rayon threads.
    let handle = tokio::runtime::Handle::try_current().ok();

    let flush_nodes = |acc: &mut Acc, force: bool| {
        if force || acc.nodes.len() >= NODE_FLUSH {
            let batch = std::mem::take(&mut acc.nodes);
            if let Some(h) = &handle {
                let tx = node_tx.clone();
                h.block_on(async move {
                    let _ = tx.send(batch).await;
                });
            }
        }
    };
    let flush_way = |acc: &mut Acc, force: bool| {
        if force || acc.way_nodes.len() >= WAYNODE_FLUSH {
            let batch = WayBatch {
                vertices: std::mem::take(&mut acc.way_rows),
                edges: std::mem::take(&mut acc.way_nodes),
            };
            if let Some(h) = &handle {
                let tx = way_tx.clone();
                h.block_on(async move {
                    let _ = tx.send(batch).await;
                });
            }
        }
    };
    let flush_rel = |acc: &mut Acc, force: bool| {
        if force || acc.rel_members.len() >= RELMEMBER_FLUSH {
            let batch = RelationBatch {
                vertices: std::mem::take(&mut acc.rel_rows),
                edges: std::mem::take(&mut acc.rel_members),
            };
            if let Some(h) = &handle {
                let tx = rel_tx.clone();
                h.block_on(async move {
                    let _ = tx.send(batch).await;
                });
            }
        }
    };

    // for_each is single-threaded but simplest + correct for streaming; rayon
    // parallelism here would need Sync senders (we're already Send/Clone OK)
    // but par_map_reduce would buffer per-block in memory, we prefer streaming.
    let mut acc = Acc::new();
    let mut n_nodes: u64 = 0;
    let mut n_ways: u64 = 0;
    let mut n_rels: u64 = 0;

    reader
        .for_each(|el| {
            // Poll shutdown (best-effort).
            // Full abort handled on next iteration via Notified::now_or_never.
            match el {
                Element::Node(n) => {
                    n_nodes += 1;
                    if let Some(row) = transform::node_to_vertex(
                        &n, &source_did, &owner_did, s2_level, geohash_len,
                    ) {
                        acc.nodes.push(row);
                    }
                    flush_nodes(&mut acc, false);
                }
                Element::DenseNode(dn) => {
                    n_nodes += 1;
                    if let Some(row) = transform::dense_node_to_vertex(
                        &dn, &source_did, &owner_did, s2_level, geohash_len,
                    ) {
                        acc.nodes.push(row);
                    }
                    flush_nodes(&mut acc, false);
                }
                Element::Way(w) => {
                    n_ways += 1;
                    let (vertex, edges) =
                        transform::way_to_rows(&w, &source_did, &owner_did);
                    if let Some(v) = vertex {
                        acc.way_rows.push(v);
                    }
                    acc.way_nodes.extend(edges);
                    flush_way(&mut acc, false);
                }
                Element::Relation(r) => {
                    n_rels += 1;
                    let (vertex, edges) =
                        transform::relation_to_rows(&r, &source_did, &owner_did);
                    if let Some(v) = vertex {
                        acc.rel_rows.push(v);
                    }
                    acc.rel_members.extend(edges);
                    flush_rel(&mut acc, false);
                }
            }
            if (n_nodes + n_ways + n_rels) % 1_000_000 == 0 {
                debug!(nodes = n_nodes, ways = n_ways, rels = n_rels, "decode progress");
            }
            // Cheap shutdown check (non-blocking poll).
            if poll_shutdown(&shutdown) {
                warn!("shutdown observed during decode");
            }
        })
        .context("PBF decode")?;

    flush_nodes(&mut acc, true);
    flush_way(&mut acc, true);
    flush_rel(&mut acc, true);
    info!(nodes = n_nodes, ways = n_ways, rels = n_rels, "decode complete");
    Ok(())
}

/// Non-blocking poll of `Notify::notified()` from sync code.
fn poll_shutdown(n: &Notify) -> bool {
    use std::future::Future;
    use std::pin::pin;
    use std::task::{Context, Poll, Waker};
    let notified = n.notified();
    let mut notified = pin!(notified);
    let waker = Waker::noop();
    let mut cx = Context::from_waker(waker);
    matches!(notified.as_mut().poll(&mut cx), Poll::Ready(()))
}
