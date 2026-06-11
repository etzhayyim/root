//! Phase 2 helper for ADR-2606036400 — long-lived WebRTC-direct listener.
//!
//! Runs a single libp2p node listening on WebRTC-direct and prints its full
//! dial multiaddr as a parseable line `DIAL_ADDR=<multiaddr>`. A js-libp2p
//! **browser** then dials that exact address (no CF Worker, no signaling).
//!
//! Port via `KOTOBA_POC_PORT` (default 0 = OS-assigned). The certhash is
//! regenerated each run, so the browser must read the printed DIAL_ADDR.
//!
//! Run: `KOTOBA_POC_PORT=49999 cargo run -p kotoba-webrtc-poc --bin listener`

use anyhow::Result;
use futures::StreamExt;
use libp2p::{
    ping,
    swarm::{Swarm, SwarmEvent},
    SwarmBuilder,
};
use libp2p_webrtc as webrtc;
use std::time::Duration;

/// Rewrite a `0.0.0.0` bind multiaddr into a loopback variant a same-host
/// browser can dial. Pure + testable (the listener prints both).
fn loopback_variant(addr: &str) -> String {
    addr.replacen("/ip4/0.0.0.0/", "/ip4/127.0.0.1/", 1)
}

fn build_webrtc_swarm() -> Result<Swarm<ping::Behaviour>> {
    Ok(SwarmBuilder::with_new_identity()
        .with_tokio()
        .with_other_transport(|key| {
            let cert = webrtc::tokio::Certificate::generate(&mut rand::thread_rng())
                .expect("generate self-signed webrtc cert");
            webrtc::tokio::Transport::new(key.clone(), cert)
        })?
        .with_behaviour(|_| ping::Behaviour::new(ping::Config::new()))?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(120)))
        .build())
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,libp2p_webrtc=warn,webrtc=warn,webrtc_sctp=error".into()),
        )
        .init();

    let port: u16 = std::env::var("KOTOBA_POC_PORT")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(0);

    let mut swarm = build_webrtc_swarm()?;
    let peer = *swarm.local_peer_id();
    swarm.listen_on(format!("/ip4/0.0.0.0/udp/{port}/webrtc-direct").parse()?)?;

    loop {
        match swarm.select_next_some().await {
            SwarmEvent::NewListenAddr { address, .. } => {
                // Print BOTH the bind addr and a 127.0.0.1 variant the browser can reach.
                let with_peer = address.clone().with(libp2p::multiaddr::Protocol::P2p(peer));
                println!("DIAL_ADDR={with_peer}");
                println!("DIAL_ADDR_LOOPBACK={}", loopback_variant(&with_peer.to_string()));
            }
            SwarmEvent::ConnectionEstablished { peer_id, .. } => {
                println!("CONNECTED_FROM={peer_id}");
            }
            SwarmEvent::ConnectionClosed { peer_id, .. } => {
                println!("DISCONNECTED={peer_id}");
            }
            _ => {}
        }
    }
}

#[cfg(test)]
mod tests {
    use super::loopback_variant;

    #[test]
    fn rewrites_unspecified_to_loopback_once() {
        let a = "/ip4/0.0.0.0/udp/49999/webrtc-direct/certhash/uEiAAAA/p2p/12D3KooWtest";
        assert_eq!(
            loopback_variant(a),
            "/ip4/127.0.0.1/udp/49999/webrtc-direct/certhash/uEiAAAA/p2p/12D3KooWtest"
        );
    }

    #[test]
    fn leaves_concrete_ip_untouched() {
        let a = "/ip4/192.168.1.15/udp/49999/webrtc-direct/certhash/x/p2p/p";
        assert_eq!(loopback_variant(a), a);
    }

    #[test]
    fn only_rewrites_leading_host_segment() {
        // A literal "0.0.0.0" elsewhere must not be touched (replacen count = 1
        // and the prefix is anchored to the /ip4/ host segment).
        let a = "/ip4/0.0.0.0/udp/1/webrtc-direct/certhash/0.0.0.0";
        assert_eq!(
            loopback_variant(a),
            "/ip4/127.0.0.1/udp/1/webrtc-direct/certhash/0.0.0.0"
        );
    }
}
