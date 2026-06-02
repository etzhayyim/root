//! W Protocol transport multiplexer.
//!
//! Routes wRPC calls to the appropriate transport based on target:
//! - In-process: wasmtime Component Model (same Pod)
//! - NATS: wrpc-transport-nats (cross-Pod, same cluster)
//! - QUIC: wrpc-transport-quic (federation, P2P)
//!
//! The transport is transparent to the WIT interface — same w-command/w-query
//! works across all transports via wRPC Invoke/Serve traits.

/// Target for a wRPC call.
#[derive(Debug, Clone)]
pub enum Target {
    /// Same Pod — wasmtime in-process dispatch (existing path).
    Local { component_id: String },
    /// Same cluster — wRPC over NATS.
    Cluster { subject_prefix: String },
    /// Federation — wRPC over QUIC.
    Federation { peer_did: String, endpoint: String },
}

/// NATS subject mapping for W Protocol.
///
/// wRPC NATS subjects follow the pattern:
/// `etzhayyim.w.{interface}.{method}.{org_id}`
pub struct NatsSubjects;

impl NatsSubjects {
    /// Build NATS subject for a w-command call.
    pub fn command(method: &str, org_id: &str) -> String {
        format!("etzhayyim.w.command.{}.{}", method, org_id)
    }

    /// Build NATS subject for a w-query call.
    pub fn query(method: &str, org_id: &str) -> String {
        format!("etzhayyim.w.query.{}.{}", method, org_id)
    }

    /// Build NATS subject for real-time event stream.
    pub fn stream(channel_id: &str) -> String {
        format!("etzhayyim.w.stream.{}", channel_id)
    }

    /// Build NATS subject for federation announce.
    pub fn federation_announce() -> String {
        "etzhayyim.w.federation.announce".into()
    }

    /// Build NATS subject for federation diff request.
    pub fn federation_diff(peer_did: &str) -> String {
        format!("etzhayyim.w.federation.diff.{}", peer_did)
    }

    /// Build NATS subject for federation block pull.
    pub fn federation_pull(peer_did: &str) -> String {
        format!("etzhayyim.w.federation.pull.{}", peer_did)
    }

    /// Build NATS subject for federation block push.
    pub fn federation_push(peer_did: &str) -> String {
        format!("etzhayyim.w.federation.push.{}", peer_did)
    }

    /// Wildcard subscription for all w-command calls in an org.
    pub fn command_wildcard(org_id: &str) -> String {
        format!("etzhayyim.w.command.*.{}", org_id)
    }

    /// Wildcard subscription for all w-query calls in an org.
    pub fn query_wildcard(org_id: &str) -> String {
        format!("etzhayyim.w.query.*.{}", org_id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_command_subject() {
        assert_eq!(
            NatsSubjects::command("send", "org_123"),
            "etzhayyim.w.command.send.org_123"
        );
    }

    #[test]
    fn test_query_subject() {
        assert_eq!(
            NatsSubjects::query("list-envelopes", "org_123"),
            "etzhayyim.w.query.list-envelopes.org_123"
        );
    }

    #[test]
    fn test_stream_subject() {
        assert_eq!(
            NatsSubjects::stream("ch_abc"),
            "etzhayyim.w.stream.ch_abc"
        );
    }

    #[test]
    fn test_federation_subjects() {
        assert_eq!(
            NatsSubjects::federation_announce(),
            "etzhayyim.w.federation.announce"
        );
        assert_eq!(
            NatsSubjects::federation_diff("did:plc:peer1"),
            "etzhayyim.w.federation.diff.did:plc:peer1"
        );
    }

    #[test]
    fn test_wildcard_subjects() {
        assert_eq!(
            NatsSubjects::command_wildcard("org_123"),
            "etzhayyim.w.command.*.org_123"
        );
    }
}
