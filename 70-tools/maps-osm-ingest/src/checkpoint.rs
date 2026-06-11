//! Optional resume checkpoint persisted to Cloudflare R2 over S3-compatible HTTP.
//!
//! This is a thin best-effort helper. R2 takes AWS SigV4; we only write a
//! small JSON marker so we keep auth simple: presigned PUT or Worker-signed
//! URL pass-through. If `--r2-endpoint` and `--checkpoint-key` are both set,
//! we PUT the marker; otherwise we no-op.

use crate::Args;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use tracing::info;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Checkpoint {
    pub source_did: String,
    pub last_block_offset: u64,
    pub batch_seq: u64,
    pub completed_at: Option<i64>,
}

pub async fn mark_complete(args: &Args, key: &str) -> Result<()> {
    let Some(endpoint) = args.r2_endpoint.as_deref() else {
        return Ok(());
    };
    let payload = Checkpoint {
        source_did: args.source_did.clone(),
        last_block_offset: u64::MAX,
        batch_seq: 0,
        completed_at: Some(chrono_now()),
    };
    let url = format!("{}/{}", endpoint.trim_end_matches('/'), key);
    let body = serde_json::to_vec(&payload)?;
    // PUT — caller-configured endpoint should be pre-authenticated (Worker
    // proxy or presigned). If not, this returns 403; we swallow.
    let resp = reqwest::Client::new().put(&url).body(body).send().await?;
    info!(status = %resp.status(), %url, "checkpoint PUT");
    Ok(())
}

fn chrono_now() -> i64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0)
}
