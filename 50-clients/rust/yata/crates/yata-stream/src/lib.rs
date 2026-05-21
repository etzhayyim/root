//! `yata-stream` — streaming materialised-view subscription client.
//!
//! ```ignore
//! use yata::prelude::*;
//! use yata_stream::MvSubscriptionExt;
//!
//! let mut sub = y.subscribe_mv("alice_friends").await?;
//! while let Some(row) = sub.next().await? {
//!     println!("{:?}", row);
//! }
//! ```
//!
//! Wire format (planned for v0.2):
//!   GET wss://yatabase.gftd.ai/xrpc/ai.gftd.apps.yata.subscribeMv?name=...
//!   ↓
//!   one JSON event per WebSocket text frame.

#![cfg_attr(docsrs, feature(doc_cfg))]
#![deny(missing_debug_implementations)]
#![warn(missing_docs)]

use async_trait::async_trait;
use serde::Deserialize;
use yata_core::{Yata, YataError, Result};

/// One MV row delivered as a JSON object.
pub type MvRow = serde_json::Value;

/// Subscription handle returned by `Yata::subscribe_mv`.
#[derive(Debug)]
pub struct MvSubscription {
    /// Name of the MV being subscribed to.
    pub name: String,
}

impl MvSubscription {
    /// Pull the next event. Returns `Ok(None)` on graceful close.
    pub async fn next(&mut self) -> Result<Option<MvRow>> {
        Err(YataError::NotImplemented(
            "MvSubscription::next is a v0.1 skeleton; WS transport lives in 0.2",
        ))
    }

    /// Close the subscription and free the WebSocket.
    pub async fn close(self) -> Result<()> {
        Ok(())
    }
}

/// Optional row decoder for caller convenience.
#[derive(Debug, Clone, Deserialize)]
pub struct GenericMvEvent {
    /// `created` / `updated` / `deleted`.
    pub op: String,
    /// New row value (omitted on `deleted`).
    pub value: Option<serde_json::Value>,
}

/// Extension trait imported via `use yata::prelude::*`.
#[async_trait]
pub trait MvSubscriptionExt {
    /// Open a streaming subscription against a named MV.
    async fn subscribe_mv(&self, name: &str) -> Result<MvSubscription>;
}

#[async_trait]
impl MvSubscriptionExt for Yata {
    async fn subscribe_mv(&self, name: &str) -> Result<MvSubscription> {
        Ok(MvSubscription { name: name.to_string() })
    }
}
