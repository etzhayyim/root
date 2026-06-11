//! RisingWave run + cursor tracking for the OSM PBF ingest pipeline.
//!
//! Tables written (see migration 20260508990000_vertex_osm_ingest_run_cursor):
//!   - `vertex_osm_ingest_run`    — one row per ingest execution
//!   - `vertex_osm_ingest_cursor` — mid-run progress per (run_id, phase)
//!   - `vertex_osm_pbf_cache`     — B2 cache manifest entry
//!
//! All SQL uses `batch_execute` (Simple Query protocol) to avoid RisingWave's
//! Extended Query (Prepared Statement) parse restrictions on large statements.
//! Timestamps are passed as `to_timestamp({unix_secs})`.
//!
//! `vertex_osm_ingest_cursor` uses a delete-then-insert upsert pattern per
//! the root-rules §Record-log semantics (no ON CONFLICT in RisingWave).

use anyhow::{Context, Result};
use tokio_postgres::{Client, NoTls};
use tracing::{info, warn};

// ── helpers ───────────────────────────────────────────────────────────────────

fn now_secs() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

/// Single-quote escape for embedding in raw SQL strings.
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

fn sq_opt(v: Option<&str>) -> String {
    v.map(sq).unwrap_or_else(|| "NULL".into())
}

/// Open a plain postgres connection for tracker writes (no dml_rate_limit so
/// tracker updates don't compete with the rate-limited writer connections).
async fn connect_tracker(db: &str) -> Result<Client> {
    // v0.4.0: TCP keepalive so tracker connection survives multi-hour ingests.
    let mut config: tokio_postgres::Config = db
        .parse()
        .context("parse postgres connection string (tracker)")?;
    config
        .keepalives(true)
        .keepalives_idle(std::time::Duration::from_secs(30))
        .keepalives_interval(std::time::Duration::from_secs(10))
        .keepalives_retries(3);
    let (client, connection) = config
        .connect(NoTls)
        .await
        .context("connect RisingWave (tracker)")?;
    tokio::spawn(async move {
        if let Err(e) = connection.await {
            warn!(error = ?e, "tracker postgres connection closed");
        }
    });
    Ok(client)
}

// ── RunTracker ────────────────────────────────────────────────────────────────

pub struct RunTracker {
    client: Client,
    pub run_id: String,
    source_did: String,
    pub started_epoch: u64,
}

impl RunTracker {
    /// Insert a new `vertex_osm_ingest_run` row (phase='init', status='running').
    pub async fn start(
        db: &str,
        source_did: &str,
        pbf_url: Option<&str>,
        pbf_b2_key: Option<&str>,
    ) -> Result<Self> {
        let client = connect_tracker(db).await?;
        let run_id = uuid::Uuid::new_v4().to_string();
        let started = now_secs();

        let sql = format!(
            "INSERT INTO vertex_osm_ingest_run \
             (run_id, source_did, pbf_url, pbf_b2_key, started_at, phase, status, \
              nodes_written, ways_written, rel_rows_written) \
             VALUES ({run_id}, {source_did}, {pbf_url}, {pbf_b2_key}, \
                     to_timestamp({started}), 'init', 'running', 0, 0, 0)",
            run_id = sq(&run_id),
            source_did = sq(source_did),
            pbf_url = sq_opt(pbf_url),
            pbf_b2_key = sq_opt(pbf_b2_key),
            started = started,
        );

        client.batch_execute(&sql).await.context("insert osm_ingest_run")?;
        info!(%run_id, %source_did, "run tracker started");

        Ok(Self {
            client,
            run_id,
            source_did: source_did.to_string(),
            started_epoch: started,
        })
    }

    /// Update run with download provenance (phase='ingest', sha256, size).
    pub async fn set_download_complete(&self, sha256: &str, size_bytes: u64) -> Result<()> {
        let sql = format!(
            "UPDATE vertex_osm_ingest_run \
             SET phase='ingest', pbf_sha256={sha256}, pbf_size_bytes={size_bytes} \
             WHERE run_id={run_id}",
            sha256 = sq(sha256),
            size_bytes = size_bytes,
            run_id = sq(&self.run_id),
        );
        self.client.batch_execute(&sql).await.context("set_download_complete")?;
        Ok(())
    }

    /// Update the current phase (e.g. 'node', 'way', 'rel').
    pub async fn set_phase(&self, phase: &str) -> Result<()> {
        let sql = format!(
            "UPDATE vertex_osm_ingest_run SET phase={phase} WHERE run_id={run_id}",
            phase = sq(phase),
            run_id = sq(&self.run_id),
        );
        self.client.batch_execute(&sql).await.context("set_phase")?;
        Ok(())
    }

    /// Record element totals after decode (best-effort; 0 is acceptable).
    #[allow(dead_code)]
    pub async fn set_totals(&self, nodes: u64, ways: u64, rels: u64) -> Result<()> {
        let sql = format!(
            "UPDATE vertex_osm_ingest_run \
             SET nodes_total={nodes}, ways_total={ways}, rels_total={rels} \
             WHERE run_id={run_id}",
            nodes = nodes,
            ways = ways,
            rels = rels,
            run_id = sq(&self.run_id),
        );
        self.client.batch_execute(&sql).await.context("set_totals")?;
        Ok(())
    }

    /// Upsert a `vertex_osm_ingest_cursor` row for (run_id, phase).
    ///
    /// RisingWave has no ON CONFLICT; we use delete-then-insert.
    /// `last_osm_id` is the last OSM element ID processed in this phase (optional).
    pub async fn update_cursor(
        &self,
        phase: &str,
        rows_written: u64,
        last_osm_id: Option<i64>,
    ) -> Result<()> {
        let cursor_id = format!("{}:{}", self.run_id, phase);
        let now = now_secs();
        let last_id_sql = last_osm_id
            .map(|id| id.to_string())
            .unwrap_or_else(|| "NULL".into());

        // delete-then-insert upsert (RisingWave implicit PK overwrite)
        let del = format!(
            "DELETE FROM vertex_osm_ingest_cursor WHERE cursor_id={cursor_id}",
            cursor_id = sq(&cursor_id),
        );
        let ins = format!(
            "INSERT INTO vertex_osm_ingest_cursor \
             (cursor_id, run_id, source_did, phase, rows_written, last_osm_id, updated_at) \
             VALUES ({cursor_id}, {run_id}, {source_did}, {phase}, {rows_written}, \
                     {last_osm_id}, to_timestamp({now}))",
            cursor_id = sq(&cursor_id),
            run_id = sq(&self.run_id),
            source_did = sq(&self.source_did),
            phase = sq(phase),
            rows_written = rows_written,
            last_osm_id = last_id_sql,
            now = now,
        );

        // Execute both statements; batch_execute runs them in order.
        let combined = format!("{del}; {ins}");
        self.client
            .batch_execute(&combined)
            .await
            .context("update_cursor")?;
        Ok(())
    }

    /// Mark the run complete and record final write counts + throughput.
    pub async fn complete(&self, nodes: u64, ways: u64, rels: u64) -> Result<()> {
        let now = now_secs();
        let elapsed = now.saturating_sub(self.started_epoch).max(1);
        let total_rows = nodes + ways + rels;
        let rows_per_sec = total_rows as f64 / elapsed as f64;

        let sql = format!(
            "UPDATE vertex_osm_ingest_run \
             SET status='completed', completed_at=to_timestamp({now}), \
                 rows_per_sec={rows_per_sec}, phase='done', \
                 nodes_written={nodes}, ways_written={ways}, rel_rows_written={rels} \
             WHERE run_id={run_id}",
            now = now,
            rows_per_sec = rows_per_sec,
            nodes = nodes,
            ways = ways,
            rels = rels,
            run_id = sq(&self.run_id),
        );
        self.client.batch_execute(&sql).await.context("complete")?;
        info!(
            run_id = %self.run_id,
            nodes, ways, rels,
            rows_per_sec = format!("{rows_per_sec:.0}"),
            "run tracker completed"
        );
        Ok(())
    }

    /// Mark the run failed with an error message.
    pub async fn fail(&self, error: &str) -> Result<()> {
        // Truncate error message to avoid overflowing VARCHAR
        let short = if error.len() > 1024 { &error[..1024] } else { error };
        let sql = format!(
            "UPDATE vertex_osm_ingest_run SET status='failed', error_msg={error} \
             WHERE run_id={run_id}",
            error = sq(short),
            run_id = sq(&self.run_id),
        );
        self.client.batch_execute(&sql).await.context("fail")?;
        warn!(run_id = %self.run_id, "run tracker failed");
        Ok(())
    }

    /// Insert a `vertex_osm_pbf_cache` row (best-effort; errors are warned, not returned).
    pub async fn record_pbf_cache(
        &self,
        geofabrik_url: &str,
        b2_key: &str,
        size_bytes: u64,
        sha256: &str,
        valid_date: &str,
    ) {
        let cache_id = format!("{}:{}", self.source_did, valid_date);
        let now = now_secs();

        let del = format!(
            "DELETE FROM vertex_osm_pbf_cache WHERE cache_id={cache_id}",
            cache_id = sq(&cache_id),
        );
        let ins = format!(
            "INSERT INTO vertex_osm_pbf_cache \
             (cache_id, source_did, geofabrik_url, b2_key, size_bytes, sha256, \
              cached_at, last_used_at, valid_date) \
             VALUES ({cache_id}, {source_did}, {geofabrik_url}, {b2_key}, \
                     {size_bytes}, {sha256}, to_timestamp({now}), to_timestamp({now}), {valid_date})",
            cache_id = sq(&cache_id),
            source_did = sq(&self.source_did),
            geofabrik_url = sq(geofabrik_url),
            b2_key = sq(b2_key),
            size_bytes = size_bytes,
            sha256 = sq(sha256),
            now = now,
            valid_date = sq(valid_date),
        );

        let combined = format!("{del}; {ins}");
        if let Err(e) = self.client.batch_execute(&combined).await {
            warn!(error = ?e, "record_pbf_cache failed (non-fatal)");
        } else {
            info!(cache_id, b2_key, "PBF cache entry recorded");
        }
    }

    /// Update `last_used_at` on an existing cache entry (best-effort).
    pub async fn touch_pbf_cache(&self, valid_date: &str) {
        let cache_id = format!("{}:{}", self.source_did, valid_date);
        let now = now_secs();
        let sql = format!(
            "UPDATE vertex_osm_pbf_cache SET last_used_at=to_timestamp({now}) \
             WHERE cache_id={cache_id}",
            now = now,
            cache_id = sq(&cache_id),
        );
        if let Err(e) = self.client.batch_execute(&sql).await {
            warn!(error = ?e, "touch_pbf_cache failed (non-fatal)");
        }
    }
}
