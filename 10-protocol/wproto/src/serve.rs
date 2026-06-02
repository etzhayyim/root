//! W Protocol wRPC Serve implementation scaffold.
//!
//! Maps wRPC Serve trait to W Protocol engine (AutoCrypto + MDAG + AT Record).
//!
//! wRPC Serve trait:
//! ```ignore
//! trait Serve: Sync {
//!     type Context: Send + Sync + 'static;
//!     type Outgoing: AsyncWrite + Index<Self::Outgoing> + Send + Sync + Unpin + 'static;
//!     type Incoming: AsyncRead + Index<Self::Incoming> + Send + Sync + Unpin + 'static;
//!
//!     fn serve(&self, instance: &str, func: &str, paths: ...)
//!         -> impl Future<Output = Result<impl Stream<Item = Result<(Context, Outgoing, Incoming)>>>>;
//! }
//! ```
//!
//! The W Protocol Serve handler:
//! 1. Receives wRPC call (Component Model binary params)
//! 2. Decodes params → WEnvelope fields
//! 3. AutoCrypto: encrypt if channel requires Signal
//! 4. MDAG: CBOR commit → Blake3 CID → CAS
//! 5. AT Record: Lexicon JSON (derived)
//! 6. Graph: projection for query path
//! 7. Encodes response → Component Model binary

// Routing constants only — no crypto/record logic needed here.

/// W Protocol wRPC handler context.
///
/// Extracted from wRPC Serve::Context.
/// Contains authentication and tenant information.
#[derive(Debug, Clone)]
pub struct WrpcContext {
    /// Authenticated DID of the caller.
    pub sender_did: String,
    /// Clerk org_id (tenant isolation).
    pub org_id: String,
    /// Whether the caller is a bot (server-assisted Signal).
    pub is_bot: bool,
    /// Request correlation ID.
    pub request_id: String,
}

/// W Protocol wRPC instance/function routing.
///
/// Maps wRPC (instance, func) pairs to W Protocol operations.
pub struct WrpcRouter;

impl WrpcRouter {
    pub const INSTANCE_COMMAND: &'static str = "etzhayyim:w/w-command";
    pub const INSTANCE_QUERY: &'static str = "etzhayyim:w/w-query";
    pub const INSTANCE_STREAM: &'static str = "etzhayyim:w/w-stream";
    pub const INSTANCE_FEDERATION: &'static str = "etzhayyim:w/w-federation";

    /// All wRPC instances served by W Protocol.
    pub fn instances() -> &'static [&'static str] {
        &[
            Self::INSTANCE_COMMAND,
            Self::INSTANCE_QUERY,
            Self::INSTANCE_STREAM,
            Self::INSTANCE_FEDERATION,
        ]
    }

    /// Command methods (mutations → AT Record + MDAG).
    pub fn command_methods() -> &'static [&'static str] {
        &[
            "send", "edit", "redact", "react", "unreact", "mark-read",
            "create-channel", "update-channel", "archive-channel",
            "join-channel", "leave-channel", "invite-member", "update-member-role",
            "create-dm", "update-presence",
            "register-prekeys", "replenish-otpks", "rotate-group-key",
        ]
    }

    /// Query methods (reads → KV/MDAG/Cypher).
    pub fn query_methods() -> &'static [&'static str] {
        &[
            "list-channels", "get-channel",
            "list-envelopes", "get-thread", "search",
            "list-members", "get-unread",
            "get-prekey-bundle", "get-prekey-bundles",
            "list-presence",
            "get-sync-state", "diff", "fetch-blocks",
        ]
    }

    /// Federation methods (MDAG sync).
    pub fn federation_methods() -> &'static [&'static str] {
        &[
            "announce", "request-diff", "pull-blocks", "push-blocks", "sync-channel",
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_instances() {
        let instances = WrpcRouter::instances();
        assert!(instances.contains(&"etzhayyim:w/w-command"));
        assert!(instances.contains(&"etzhayyim:w/w-query"));
        assert!(instances.contains(&"etzhayyim:w/w-federation"));
        assert_eq!(instances.len(), 4);
    }

    #[test]
    fn test_command_methods() {
        let methods = WrpcRouter::command_methods();
        assert!(methods.contains(&"send"));
        assert!(methods.contains(&"create-channel"));
        assert!(methods.contains(&"create-dm"));
    }

    #[test]
    fn test_query_methods() {
        let methods = WrpcRouter::query_methods();
        assert!(methods.contains(&"list-envelopes"));
        assert!(methods.contains(&"get-sync-state"));
        assert!(methods.contains(&"diff"));
        assert!(methods.contains(&"fetch-blocks"));
    }

    #[test]
    fn test_federation_methods() {
        let methods = WrpcRouter::federation_methods();
        assert!(methods.contains(&"announce"));
        assert!(methods.contains(&"request-diff"));
        assert!(methods.contains(&"sync-channel"));
    }
}
