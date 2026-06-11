//! K2.c Jetstream-format WebSocket subscriber.
//!
//! Connects to a Jetstream-shape firehose (e.g. `wss://jetstream.atproto.tools/subscribe`),
//! filters for `com.etzhayyim.kg.{node,edge}` commits, and applies them to
//! the live store. Reconnects with exponential backoff on disconnect. The
//! subscriber runs as a background tokio task; the main task keeps serving
//! SPARQL.
//!
//! Event shape consumed (Jetstream firehose):
//! ```jsonc
//! {
//!   "did": "did:plc:...",
//!   "time_us": 1700000000000000,
//!   "kind": "commit",
//!   "commit": {
//!     "rev": "...",
//!     "operation": "create" | "update" | "delete",
//!     "collection": "com.etzhayyim.kg.node" | "com.etzhayyim.kg.edge",
//!     "rkey": "...",
//!     "record": { "$type": "...", ... },     // create / update only
//!     "cid": "..."
//!   }
//! }
//! ```
//!
//! Live PDS publishing of these collections is not yet wired in this
//! monorepo (see `50-infra/mst-projector/` Stage 3 scaffold), so this
//! module is fully exercised only against synthetic events. The smoke
//! tests below feed the apply path with the exact JSON the subscriber
//! decodes off the wire.

use std::sync::Arc;
use std::time::Duration;

use anyhow::{Context, Result};
use futures_util::StreamExt;
use serde::Deserialize;
use serde_json::Value;
use tokio_tungstenite::tungstenite::Message;

use crate::iri::node_iri;
use crate::load::{apply_record_value, remove_node};
use crate::store::AppStore;

const RELEVANT_COLLECTIONS: &[&str] = &["com.etzhayyim.kg.node", "com.etzhayyim.kg.edge"];

const BACKOFF_INITIAL: Duration = Duration::from_secs(1);
const BACKOFF_MAX: Duration = Duration::from_secs(60);

#[derive(Debug, Deserialize)]
struct JetstreamEvent {
    kind: Option<String>,
    commit: Option<JetstreamCommit>,
}

#[derive(Debug, Deserialize)]
struct JetstreamCommit {
    operation: Option<String>,
    collection: Option<String>,
    rkey: Option<String>,
    record: Option<Value>,
}

/// Spawn the subscriber as a background tokio task. Returns immediately.
pub fn spawn_subscriber(app: Arc<AppStore>, firehose_url: String) -> tokio::task::JoinHandle<()> {
    tokio::spawn(async move {
        if let Err(err) = run_subscriber(app, firehose_url).await {
            tracing::error!(error = %err, "firehose subscriber exited with error");
        }
    })
}

async fn run_subscriber(app: Arc<AppStore>, firehose_url: String) -> Result<()> {
    let mut backoff = BACKOFF_INITIAL;
    loop {
        match connect_once(app.clone(), &firehose_url).await {
            Ok(()) => {
                tracing::warn!("firehose stream ended cleanly; reconnecting after {:?}", backoff);
            }
            Err(err) => {
                tracing::warn!(error = %err, "firehose connection failed; reconnecting after {:?}", backoff);
            }
        }
        tokio::time::sleep(backoff).await;
        backoff = std::cmp::min(backoff.saturating_mul(2), BACKOFF_MAX);
    }
}

async fn connect_once(app: Arc<AppStore>, firehose_url: &str) -> Result<()> {
    tracing::info!(url = %firehose_url, "firehose connecting");
    let (ws, _resp) = tokio_tungstenite::connect_async(firehose_url)
        .await
        .with_context(|| format!("ws connect {firehose_url}"))?;
    tracing::info!("firehose connected");
    let (_sink, mut stream) = ws.split();

    while let Some(msg) = stream.next().await {
        let msg = msg.with_context(|| "ws read")?;
        match msg {
            Message::Text(text) => {
                if let Err(err) = handle_event(&app, &text) {
                    tracing::warn!(error = %err, "skipping malformed event");
                }
            }
            Message::Binary(_) => {
                // Jetstream emits JSON over text frames. Native firehose
                // CAR-encoded events land here; not handled in K2.c.
            }
            Message::Close(_) => break,
            Message::Ping(_) | Message::Pong(_) | Message::Frame(_) => {}
        }
    }
    Ok(())
}

/// Pure: parse a Jetstream event JSON and apply it to the store. Returns
/// `Ok(true)` when the event was an com.etzhayyim.kg.* commit (whether
/// applied or removed), `Ok(false)` when the event was ignored as
/// irrelevant. Errors only on store I/O.
pub fn handle_event(app: &AppStore, text: &str) -> Result<bool> {
    let event: JetstreamEvent = match serde_json::from_str(text) {
        Ok(e) => e,
        Err(_) => return Ok(false),
    };

    if event.kind.as_deref() != Some("commit") {
        return Ok(false);
    }
    let Some(commit) = event.commit else {
        return Ok(false);
    };
    let Some(collection) = commit.collection.as_deref() else {
        return Ok(false);
    };
    if !RELEVANT_COLLECTIONS.iter().any(|c| *c == collection) {
        return Ok(false);
    }

    match commit.operation.as_deref() {
        Some("create") | Some("update") => {
            let Some(record) = commit.record else { return Ok(false) };
            apply_record_value(app, &record)
                .with_context(|| format!("applying {collection} create/update"))?;
            Ok(true)
        }
        Some("delete") => {
            // For node deletions we know the canonical nodeId because the
            // projector emits one rkey per (nodeType, nodeId). The
            // firehose event doesn't carry the nodeId — only the rkey —
            // so we can't directly map rkey → nodeId on the consumer side.
            // K2.c leaves deletes as a no-op except when the rkey itself
            // happens to be a nodeId (rare). K2.c.x will cache rkey →
            // nodeId at apply time and consult that cache here.
            let _ = commit.rkey;
            let _ = remove_node; // keep symbol live for K2.c.x
            tracing::debug!(collection, "delete: noop in K2.c (rkey→nodeId mapping deferred)");
            Ok(true)
        }
        _ => Ok(false),
    }
}

// `node_iri` is currently only used by the (future) rkey→nodeId resolver
// in K2.c.x; keep the import live so the module compiles cleanly.
#[allow(dead_code)]
fn _node_iri_keepalive(s: &str) -> String {
    node_iri(s).as_str().to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn event_for_relevant_collection_creates_node() {
        let app = AppStore::new().unwrap();
        let event = serde_json::json!({
            "did": "did:web:etzhayyim.com",
            "time_us": 1700000000000000_u64,
            "kind": "commit",
            "commit": {
                "rev": "abc",
                "operation": "create",
                "collection": "com.etzhayyim.kg.node",
                "rkey": "rdummy",
                "cid": "bafkreidummy",
                "record": {
                    "$type": "com.etzhayyim.kg.node",
                    "nodeId": "urn:test:firehose-1",
                    "nodeType": "adr",
                    "source": "manual",
                    "createdAt": "2026-05-19T00:00:00.000Z"
                }
            }
        })
        .to_string();
        let handled = handle_event(&app, &event).unwrap();
        assert!(handled, "event should be handled");

        let results = app
            .store
            .query(
                "PREFIX etzv: <https://etzhayyim.com/kg/v#>
                 ASK { <https://etzhayyim.com/kg/n/urn:test:firehose-1> etzv:nodeType \"adr\" }",
            )
            .unwrap();
        match results {
            oxigraph::sparql::QueryResults::Boolean(b) => assert!(b),
            _ => panic!("expected ASK result"),
        }
    }

    #[test]
    fn event_for_other_collection_is_ignored() {
        let app = AppStore::new().unwrap();
        let event = serde_json::json!({
            "kind": "commit",
            "commit": {
                "operation": "create",
                "collection": "app.bsky.feed.post",
                "rkey": "x",
                "record": { "$type": "app.bsky.feed.post", "text": "hi" }
            }
        })
        .to_string();
        let handled = handle_event(&app, &event).unwrap();
        assert!(!handled, "irrelevant collection should be ignored");
    }

    #[test]
    fn malformed_event_does_not_panic() {
        let app = AppStore::new().unwrap();
        assert_eq!(handle_event(&app, "not json").unwrap(), false);
        assert_eq!(handle_event(&app, "{}").unwrap(), false);
        assert_eq!(
            handle_event(&app, r#"{"kind":"identity"}"#).unwrap(),
            false
        );
    }
}
