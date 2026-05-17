//! RisingWave INSERT writer.
//!
//! RisingWave 2.8.x does not support COPY FROM STDIN via the Postgres wire
//! protocol. We use multi-row INSERT VALUES instead, writing directly to the
//! primary tables.  RisingWave's implicit PK upsert (same PK → overwrite)
//! makes re-runs naturally idempotent without staging tables.
//!
//! Batch size: 10 000 rows per INSERT (~1.8 MB SQL). In-cluster benchmarks
//! show ~4 000 rows/sec per connection; with 3 parallel writers the total
//! effective throughput is ~12 000 rows/sec.
//!
//! FLUSH is intentionally omitted: RW_ALLOW_FLUSH=0 in production and FLUSH
//! is a DDL-level operation that interferes with the rate-limit contract.
//! Rows become visible within the next checkpoint interval (~5s default).

use crate::run_tracker::RunTracker;
use crate::transform::{EdgeRelationMemberRow, EdgeWayNodeRow, RelationBatch, VertexOsmElementRow, WayBatch};
use crate::Args;
use anyhow::{Context, Result};
use std::sync::Arc;
use tokio::sync::mpsc;
use tokio_postgres::{Client, NoTls};
use tracing::{debug, info, warn};

/// v0.5.0: optional NATS client for parallel publish (ADR-2605091700 Phase 4).
/// When `args.nats_url` is set, every inserted row is also published to
/// `ingest.osm.element.{n|w|r}` subject as JSON.  Fire-and-forget — NATS
/// publish failure does NOT block the SQL INSERT path.
pub(crate) async fn connect_nats(url: Option<&str>) -> Option<async_nats::Client> {
    let url = url?.trim();
    if url.is_empty() {
        return None;
    }
    match async_nats::ConnectOptions::new()
        .max_reconnects(None)
        .reconnect_delay_callback(|_| std::time::Duration::from_secs(2))
        .connect(url)
        .await
    {
        Ok(nc) => {
            info!(nats_url = url, "NATS publish connected");
            Some(nc)
        }
        Err(e) => {
            warn!(error = ?e, nats_url = url, "NATS connect failed; continuing without NATS publish");
            None
        }
    }
}

/// Best-effort batch publish.  Iterates rows, JSON-encodes each, publishes to
/// `subject`.  Single-row publish failure is logged at debug (does not block).
async fn publish_batch_nats<T: serde::Serialize>(
    nats: &Option<async_nats::Client>,
    subject: &str,
    rows: &[T],
) {
    let Some(nc) = nats else { return };
    for row in rows {
        let payload = match serde_json::to_vec(row) {
            Ok(b) => b,
            Err(e) => {
                debug!(error = ?e, subject, "nats publish: serialize failed");
                continue;
            }
        };
        if let Err(e) = nc.publish(subject.to_owned(), payload.into()).await {
            debug!(error = ?e, subject, "nats publish failed (non-fatal)");
        }
    }
}

async fn connect(db: &str, dml_rate_limit: Option<u64>) -> Result<Client> {
    // v0.4.0: TCP keepalive + session-local distributed_dml.
    // Long-running ingests (3h+) hit "connection closed" on default tokio_postgres
    // because the OS / RW frontend may drop idle TCP after ~1h.  Set
    // keepalive 30s with 3 probes so dead peers are detected fast.
    let mut config: tokio_postgres::Config = db
        .parse()
        .context("parse postgres connection string")?;
    config
        .keepalives(true)
        .keepalives_idle(std::time::Duration::from_secs(30))
        .keepalives_interval(std::time::Duration::from_secs(10))
        .keepalives_retries(3);
    let (client, connection) = config
        .connect(NoTls)
        .await
        .context("connect RisingWave")?;
    tokio::spawn(async move {
        if let Err(e) = connection.await {
            warn!(error = ?e, "postgres connection closed");
        }
    });
    if let Some(rate) = dml_rate_limit {
        client
            .execute(&format!("SET dml_rate_limit = {rate}"), &[])
            .await
            .context("SET dml_rate_limit")?;
        info!(dml_rate_limit = rate, "rate limit applied");
    }
    // v0.4.0: session-local distributed_dml so we don't depend on global
    // ALTER SYSTEM.  See ADR-2605081430 D3 / D9.
    client
        .execute("SET batch_enable_distributed_dml = true", &[])
        .await
        .context("SET batch_enable_distributed_dml")?;
    Ok(client)
}

// SQL single-quote escape.
fn sq(s: &str) -> String {
    let mut buf = String::with_capacity(s.len() + 2);
    buf.push('\'');
    for c in s.chars() {
        if c == '\'' {
            buf.push('\'');
            buf.push('\'');
        } else {
            buf.push(c);
        }
    }
    buf.push('\'');
    buf
}

fn sql_opt_i64(v: Option<i64>) -> String {
    v.map(|x| x.to_string()).unwrap_or_else(|| "NULL".into())
}
fn sql_opt_u64(v: Option<u64>) -> String {
    // Bit-reinterpret u64 → i64 to fit RW BIGINT.  S2 cell IDs on faces 4-5
    // (mid-Pacific / mid-Atlantic / parts of Asia) exceed i64 max as raw u64
    // (e.g. 12284187311763095552 > 2^63).  We store the same bit pattern as
    // signed i64; range queries must apply the same `as i64` cast on bounds
    // to preserve ordering.  See `90-docs/adr/2605081430-...` D8.
    v.map(|x| (x as i64).to_string()).unwrap_or_else(|| "NULL".into())
}
fn sql_opt_f64(v: Option<f64>) -> String {
    match v {
        Some(x) if x.is_finite() => format!("{x}"),
        _ => "NULL".into(),
    }
}
fn sql_opt_str(v: Option<&str>) -> String {
    v.map(|s| sq(s)).unwrap_or_else(|| "NULL".into())
}
/// Epoch seconds → to_timestamp(x) for timestamptz columns.
fn sql_opt_ts(v: Option<i64>) -> String {
    v.map(|x| format!("to_timestamp({x})")).unwrap_or_else(|| "NULL".into())
}

const NODE_COLS: &str = "vertex_id,_seq,owner_did,source_did,sensitivity_ord,created_date,\
osm_type,osm_id,version,changeset_id,user_name,uid,timestamp,valid_from,valid_to,\
lat,lon,s2_cell_id,geohash,tags,bbox_min_lng,bbox_min_lat,bbox_max_lng,bbox_max_lat";

fn vertex_row_sql(r: &VertexOsmElementRow, seq: u64) -> String {
    let tags_str = serde_json::to_string(&r.tags).unwrap_or_else(|_| "{}".into());
    format!(
        "({vid},{seq},{owner},{source},{sens},{cdate},{otype},{oid},{ver},{cs},{user},{uid},{ts},{vf},{vt},{lat},{lon},{s2},{gh},{tags},{bmnl},{bmnla},{bmxl},{bmxla})",
        vid   = sq(&r.vertex_id),
        seq   = seq,
        owner = sq(&r.owner_did),
        source = sq(&r.source_did),
        sens  = r.sensitivity_ord,
        cdate = sq(&r.created_date),
        otype = sq(r.osm_type),
        oid   = r.osm_id,
        ver   = r.version,
        cs    = sql_opt_i64(r.changeset_id),
        user  = sql_opt_str(r.user_name.as_deref()),
        uid   = sql_opt_i64(r.uid),
        ts    = sql_opt_ts(r.timestamp),
        vf    = sql_opt_ts(r.valid_from),
        vt    = sql_opt_ts(r.valid_to),
        lat   = sql_opt_f64(r.lat),
        lon   = sql_opt_f64(r.lon),
        s2    = sql_opt_u64(r.s2_cell_id),
        gh    = sql_opt_str(r.geohash.as_deref()),
        tags  = sq(&tags_str),
        bmnl  = sql_opt_f64(r.bbox_min_lng),
        bmnla = sql_opt_f64(r.bbox_min_lat),
        bmxl  = sql_opt_f64(r.bbox_max_lng),
        bmxla = sql_opt_f64(r.bbox_max_lat),
    )
}

const WAYNODE_COLS: &str =
    "edge_id,_seq,owner_did,source_did,created_date,way_vertex_id,node_vertex_id,seq,valid_from,valid_to";

fn waynode_row_sql(r: &EdgeWayNodeRow, _seq: u64) -> String {
    format!(
        "({eid},{sq},{owner},{source},{cdate},{wv},{nv},{s},{vf},{vt})",
        eid    = sq(&r.edge_id),
        sq     = _seq,
        owner  = sq(&r.owner_did),
        source = sq(&r.source_did),
        cdate  = sq(&r.created_date),
        wv     = sq(&r.way_vertex_id),
        nv     = sq(&r.node_vertex_id),
        s      = r.seq,
        vf     = sql_opt_ts(r.valid_from),
        vt     = sql_opt_ts(r.valid_to),
    )
}

const RELMEMBER_COLS: &str =
    "edge_id,_seq,owner_did,source_did,created_date,relation_vertex_id,member_vertex_id,member_type,role,seq,valid_from,valid_to";

fn relmember_row_sql(r: &EdgeRelationMemberRow, _seq: u64) -> String {
    format!(
        "({eid},{sq},{owner},{source},{cdate},{rv},{mv},{mt},{role},{s},{vf},{vt})",
        eid    = sq(&r.edge_id),
        sq     = _seq,
        owner  = sq(&r.owner_did),
        source = sq(&r.source_did),
        cdate  = sq(&r.created_date),
        rv     = sq(&r.relation_vertex_id),
        mv     = sq(&r.member_vertex_id),
        mt     = sq(r.member_type),
        role   = sq(&r.role),
        s      = r.seq,
        vf     = sql_opt_ts(r.valid_from),
        vt     = sql_opt_ts(r.valid_to),
    )
}

// Use batch_execute (Simple Query protocol) so RisingWave receives the SQL
// as a plain text message, not as a prepared statement via the Extended Query
// (Parse/Bind/Execute) protocol. The Extended Query Parse phase hangs on large
// INSERT ... VALUES statements in RisingWave 2.8.x.
async fn insert_vertex_batch(
    client: &Client,
    table: &str,
    rows: &[VertexOsmElementRow],
    seq_base: u64,
) -> Result<()> {
    if rows.is_empty() {
        return Ok(());
    }
    let mut sql = format!("INSERT INTO {table} ({NODE_COLS}) VALUES ");
    for (i, r) in rows.iter().enumerate() {
        if i > 0 { sql.push(','); }
        sql.push_str(&vertex_row_sql(r, seq_base + i as u64));
    }
    client.batch_execute(&sql).await.context("insert vertex batch")?;
    Ok(())
}

async fn insert_waynode_batch(
    client: &Client,
    table: &str,
    rows: &[EdgeWayNodeRow],
    seq_base: u64,
) -> Result<()> {
    if rows.is_empty() {
        return Ok(());
    }
    let mut sql = format!("INSERT INTO {table} ({WAYNODE_COLS}) VALUES ");
    for (i, r) in rows.iter().enumerate() {
        if i > 0 { sql.push(','); }
        sql.push_str(&waynode_row_sql(r, seq_base + i as u64));
    }
    client.batch_execute(&sql).await.context("insert waynode batch")?;
    Ok(())
}

async fn insert_relmember_batch(
    client: &Client,
    table: &str,
    rows: &[EdgeRelationMemberRow],
    seq_base: u64,
) -> Result<()> {
    if rows.is_empty() {
        return Ok(());
    }
    let mut sql = format!("INSERT INTO {table} ({RELMEMBER_COLS}) VALUES ");
    for (i, r) in rows.iter().enumerate() {
        if i > 0 { sql.push(','); }
        sql.push_str(&relmember_row_sql(r, seq_base + i as u64));
    }
    client.batch_execute(&sql).await.context("insert relmember batch")?;
    Ok(())
}

pub async fn run_node_writer(
    args: &Args,
    _owner_did: &str,
    mut rx: mpsc::Receiver<Vec<VertexOsmElementRow>>,
    tracker: Option<Arc<RunTracker>>,
) -> Result<u64> {
    let client = connect(&args.db, args.dml_rate_limit).await?;
    let nats = connect_nats(args.nats_url.as_deref()).await;
    let mut seq: u64 = 0;
    let mut total: u64 = 0;
    let cursor_interval = args.batch_size as u64 * 100;
    while let Some(batch) = rx.recv().await {
        if batch.is_empty() {
            continue;
        }
        insert_vertex_batch(&client, "vertex_osm_element", &batch, seq).await?;
        publish_batch_nats(&nats, "ingest.osm.element.n", &batch).await;
        seq += batch.len() as u64;
        total += batch.len() as u64;
        if total % (args.batch_size as u64 * 10) == 0 {
            debug!(rows = total, "node write progress");
        }
        if total % cursor_interval == 0 {
            if let Some(ref t) = tracker {
                t.update_cursor("node", total, None).await.ok();
            }
        }
    }
    // FLUSH deliberately omitted (RW_ALLOW_FLUSH=0; rows visible at next checkpoint ~5s).
    info!(rows = total, "node writer complete");
    Ok(total)
}

pub async fn run_way_writer(
    args: &Args,
    _owner_did: &str,
    mut rx: mpsc::Receiver<WayBatch>,
    tracker: Option<Arc<RunTracker>>,
) -> Result<u64> {
    let client = connect(&args.db, args.dml_rate_limit).await?;
    let nats = connect_nats(args.nats_url.as_deref()).await;
    let mut vseq: u64 = 0;
    let mut eseq: u64 = 0;
    let mut vt: u64 = 0;
    let mut et: u64 = 0;
    let cursor_interval = args.batch_size as u64 * 100;
    while let Some(WayBatch { vertices, edges }) = rx.recv().await {
        if !vertices.is_empty() {
            insert_vertex_batch(&client, "vertex_osm_element", &vertices, vseq).await?;
            publish_batch_nats(&nats, "ingest.osm.element.w", &vertices).await;
            vseq += vertices.len() as u64;
            vt += vertices.len() as u64;
        }
        if !edges.is_empty() {
            insert_waynode_batch(&client, "edge_osm_way_node", &edges, eseq).await?;
            publish_batch_nats(&nats, "ingest.osm.edge.way_node", &edges).await;
            eseq += edges.len() as u64;
            et += edges.len() as u64;
        }
        if (vt + et) % (args.batch_size as u64 * 10) == 0 {
            debug!(vertices = vt, edges = et, "way write progress");
        }
        if vt % cursor_interval == 0 && vt > 0 {
            if let Some(ref t) = tracker {
                t.update_cursor("way", vt, None).await.ok();
            }
        }
    }
    // FLUSH deliberately omitted.
    info!(vertices = vt, edges = et, "way writer complete");
    Ok(vt)
}

pub async fn run_relation_writer(
    args: &Args,
    _owner_did: &str,
    mut rx: mpsc::Receiver<RelationBatch>,
    tracker: Option<Arc<RunTracker>>,
) -> Result<u64> {
    let client = connect(&args.db, args.dml_rate_limit).await?;
    let nats = connect_nats(args.nats_url.as_deref()).await;
    let mut vseq: u64 = 0;
    let mut eseq: u64 = 0;
    let mut vt: u64 = 0;
    let mut et: u64 = 0;
    let cursor_interval = args.batch_size as u64 * 100;
    while let Some(RelationBatch { vertices, edges }) = rx.recv().await {
        if !vertices.is_empty() {
            insert_vertex_batch(&client, "vertex_osm_element", &vertices, vseq).await?;
            publish_batch_nats(&nats, "ingest.osm.element.r", &vertices).await;
            vseq += vertices.len() as u64;
            vt += vertices.len() as u64;
        }
        if !edges.is_empty() {
            insert_relmember_batch(&client, "edge_osm_relation_member", &edges, eseq).await?;
            publish_batch_nats(&nats, "ingest.osm.edge.relation_member", &edges).await;
            eseq += edges.len() as u64;
            et += edges.len() as u64;
        }
        if (vt + et) % (args.batch_size as u64 * 10) == 0 {
            debug!(vertices = vt, edges = et, "relation write progress");
        }
        if vt % cursor_interval == 0 && vt > 0 {
            if let Some(ref t) = tracker {
                t.update_cursor("rel", vt, None).await.ok();
            }
        }
    }
    // FLUSH deliberately omitted.
    info!(vertices = vt, edges = et, "relation writer complete");
    Ok(vt)
}
