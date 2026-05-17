//! W Protocol Firehose utilities.
//!
//! Provides W Protocol collection classification for AT Firehose events.
//! The actual bridge (`AtFirehoseBridge`) lives in `yata-at` and is used
//! through `wproto::at::AtFirehoseBridge`. This module adds W Protocol awareness.

use std::collections::HashSet;

/// W Protocol AT collections that should be processed by the W Protocol pipeline.
pub const W_COLLECTIONS: &[&str] = &[
    "ai.gftd.w.message",
    "ai.gftd.w.channel",
    "ai.gftd.w.member",
    "ai.gftd.w.reaction",
    "ai.gftd.w.readReceipt",
    "ai.gftd.w.presence",
    "ai.gftd.a2a.task",
    "ai.gftd.a2a.result",
    "ai.gftd.a2a.message",
    "ai.gftd.a2a.session",
];

/// Classifier for W Protocol vs regular AT Firehose events.
pub struct WFirehoseClassifier {
    w_collections: HashSet<String>,
}

impl WFirehoseClassifier {
    pub fn new() -> Self {
        Self {
            w_collections: W_COLLECTIONS.iter().map(|s| s.to_string()).collect(),
        }
    }

    /// Check if a collection is a W Protocol collection.
    pub fn is_w_collection(&self, collection: &str) -> bool {
        self.w_collections.contains(collection)
    }

    /// Return all W Protocol collections (for firehose subscription config).
    pub fn w_collection_list(&self) -> Vec<String> {
        self.w_collections.iter().cloned().collect()
    }

    /// Merge W Protocol collections with additional app-specific collections.
    pub fn merged_collections(&self, extra: &[String]) -> Vec<String> {
        let mut all: Vec<String> = self.w_collection_list();
        for c in extra {
            if !self.w_collections.contains(c) {
                all.push(c.clone());
            }
        }
        all
    }
}

impl Default for WFirehoseClassifier {
    fn default() -> Self {
        Self::new()
    }
}
