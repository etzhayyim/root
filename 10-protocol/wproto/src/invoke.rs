//! W Protocol wRPC Invoke helpers for federation.
//!
//! wRPC Invoke trait:
//! ```ignore
//! trait Invoke: Send + Sync {
//!     type Context: Send + Sync;
//!     type Outgoing: AsyncWrite + Index<Self::Outgoing> + ...;
//!     type Incoming: AsyncRead + Index<Self::Incoming> + ...;
//!
//!     fn invoke(&self, cx, instance: &str, func: &str, params: Bytes, paths: ...)
//!         -> impl Future<Output = Result<(Outgoing, Incoming)>>;
//! }
//! ```
//!
//! W Protocol federation uses Invoke to call remote instances:
//! - w-federation.request-diff(peer_did, channel_id, local_root_cid)
//! - w-federation.pull-blocks(peer_did, cids)
//! - w-federation.push-blocks(peer_did, blocks)

// No type imports needed — federation structs are self-contained.

/// Federation sync request.
#[derive(Debug, Clone)]
pub struct SyncRequest {
    pub peer_did: String,
    pub channel_id: String,
    pub local_root_cid: String,
}

/// Federation sync result.
#[derive(Debug, Clone)]
pub struct SyncResult {
    pub channel_id: String,
    pub new_root_cid: String,
    pub blocks_received: usize,
    pub envelopes_added: usize,
    pub members_changed: usize,
}

/// Federation block transfer.
#[derive(Debug, Clone)]
pub struct BlockTransfer {
    /// Blake3 CID hex.
    pub cid: String,
    /// CBOR-encoded block bytes.
    pub data: Vec<u8>,
}

/// Helper to build wRPC invoke parameters for federation calls.
pub struct FederationInvoke;

impl FederationInvoke {
    pub const INSTANCE: &'static str = "gftd:w/w-federation";

    pub const FUNC_ANNOUNCE: &'static str = "announce";
    pub const FUNC_REQUEST_DIFF: &'static str = "request-diff";
    pub const FUNC_PULL_BLOCKS: &'static str = "pull-blocks";
    pub const FUNC_PUSH_BLOCKS: &'static str = "push-blocks";
    pub const FUNC_SYNC_CHANNEL: &'static str = "sync-channel";
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_federation_constants() {
        assert_eq!(FederationInvoke::INSTANCE, "gftd:w/w-federation");
        assert_eq!(FederationInvoke::FUNC_SYNC_CHANNEL, "sync-channel");
    }

    #[test]
    fn test_sync_request() {
        let req = SyncRequest {
            peer_did: "did:plc:remote".into(),
            channel_id: "ch_123".into(),
            local_root_cid: "abc123".into(),
        };
        assert_eq!(req.peer_did, "did:plc:remote");
    }
}
