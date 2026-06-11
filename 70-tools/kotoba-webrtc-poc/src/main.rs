//! Phase 0 PoC for ADR-2606036400.
//!
//! Two libp2p nodes, both using the **WebRTC-direct** transport (self-signed
//! DTLS cert + certhash in the multiaddr, no CA, no signaling server). The
//! listener prints its full dial address — note the `/webrtc-direct/certhash/...`
//! component: that exact multiaddr is what a js-libp2p **browser** dials in
//! Phase 2. The dialer connects to it and we assert `ConnectionEstablished`.
//!
//! Success here = a browser-dialable transport is feasible on the libp2p line
//! kotoba already pins (0.53.2 / core 0.41.3), without touching the submodule.
//!
//! Run: `cargo run -p kotoba-webrtc-poc`

use anyhow::{anyhow, Result};
use futures::StreamExt;
use libp2p::{
    multiaddr::Protocol,
    ping,
    swarm::{Swarm, SwarmEvent},
    Multiaddr, SwarmBuilder,
};
use libp2p_webrtc as webrtc;
use std::time::Duration;

/// Build a swarm whose ONLY transport is WebRTC-direct.
fn build_webrtc_swarm() -> Result<Swarm<ping::Behaviour>> {
    let swarm = SwarmBuilder::with_new_identity()
        .with_tokio()
        // `with_other_transport` because WebRTC-direct is not one of the
        // builder's first-class `.with_quic()/.with_tcp()` transports.
        // The WebRTC transport already yields `(PeerId, impl StreamMuxer)`
        // and carries its own auth+mux (no separate noise/yamux).
        .with_other_transport(|key| {
            let cert = webrtc::tokio::Certificate::generate(&mut rand::thread_rng())
                .expect("generate self-signed webrtc cert");
            webrtc::tokio::Transport::new(key.clone(), cert)
        })?
        .with_behaviour(|_| ping::Behaviour::new(ping::Config::new()))?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(30)))
        .build();
    Ok(swarm)
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,libp2p_webrtc=warn,webrtc=warn".into()),
        )
        .init();

    let mut listener = build_webrtc_swarm()?;
    let mut dialer = build_webrtc_swarm()?;
    let listener_peer = *listener.local_peer_id();
    println!("listener PeerId = {listener_peer}");
    println!("dialer   PeerId = {}", dialer.local_peer_id());

    // Both nodes listen on an OS-assigned UDP port, WebRTC-direct.
    // PHASE-0 FINDING: the libp2p-webrtc transport can only *dial* from a node
    // that itself has an *active* webrtc-direct listener (it needs a bound UDP
    // socket to source ICE from) — otherwise the dial fails with
    // "no active listeners, can not dial without a previous listen". So the
    // dialer must listen too, even though it never accepts inbound here.
    listener.listen_on("/ip4/127.0.0.1/udp/0/webrtc-direct".parse()?)?;
    dialer.listen_on("/ip4/127.0.0.1/udp/0/webrtc-direct".parse()?)?;

    async fn first_listen_addr(swarm: &mut Swarm<ping::Behaviour>) -> Multiaddr {
        loop {
            if let SwarmEvent::NewListenAddr { address, .. } = swarm.select_next_some().await {
                return address;
            }
        }
    }

    // 1) Wait for the listener's full dial multiaddr (with certhash) AND for the
    //    dialer to have its own active listener.
    let dial_addr: Multiaddr = tokio::time::timeout(Duration::from_secs(10), async {
        let addr = first_listen_addr(&mut listener).await;
        let _ = first_listen_addr(&mut dialer).await; // dialer now has an active listener
        addr
    })
    .await
    .map_err(|_| anyhow!("timed out waiting for listen addr"))?;

    println!("\n  ⇨ BROWSER-DIALABLE ADDR:\n    {dial_addr}/p2p/{listener_peer}\n");
    assert!(
        dial_addr.iter().any(|p| matches!(p, Protocol::WebRTCDirect)),
        "listen addr must contain /webrtc-direct"
    );
    assert!(
        dial_addr.iter().any(|p| matches!(p, Protocol::Certhash(_))),
        "listen addr must contain /certhash (self-signed, CA-free)"
    );

    // 2) Dial it from the second node.
    dialer.dial(dial_addr.with(Protocol::P2p(listener_peer)))?;

    // 3) Drive both swarms; assert a real connection is established.
    let connected = tokio::time::timeout(Duration::from_secs(20), async {
        loop {
            tokio::select! {
                ev = listener.select_next_some() => {
                    if let SwarmEvent::ConnectionEstablished { peer_id, .. } = ev {
                        println!("[listener] ConnectionEstablished with {peer_id}");
                        return true;
                    }
                }
                ev = dialer.select_next_some() => {
                    match ev {
                        SwarmEvent::ConnectionEstablished { peer_id, .. } => {
                            println!("[dialer]   ConnectionEstablished with {peer_id}");
                            return true;
                        }
                        SwarmEvent::OutgoingConnectionError { error, .. } => {
                            eprintln!("[dialer]   OutgoingConnectionError: {error}");
                        }
                        _ => {}
                    }
                }
            }
        }
    })
    .await
    .unwrap_or(false);

    if connected {
        println!("\n✅ PHASE 0 PASS — WebRTC-direct rust↔rust dial works on libp2p 0.53.2.");
        println!("   A js-libp2p browser can dial the same /webrtc-direct/certhash addr (Phase 2).");
        Ok(())
    } else {
        Err(anyhow!(
            "❌ PHASE 0 FAIL — no ConnectionEstablished (see OutgoingConnectionError above)"
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// CI-checkable regression for ADR-2606036400 Phase 0: two nodes connect
    /// over WebRTC-direct (self-signed cert + certhash), on kotoba's libp2p line.
    /// Mirrors `main` but as `cargo test` coverage instead of a manual run.
    #[tokio::test(flavor = "multi_thread", worker_threads = 2)]
    async fn webrtc_direct_rust_to_rust_dial_connects() {
        let mut listener = build_webrtc_swarm().expect("listener swarm");
        let mut dialer = build_webrtc_swarm().expect("dialer swarm");
        let listener_peer = *listener.local_peer_id();

        listener
            .listen_on("/ip4/127.0.0.1/udp/0/webrtc-direct".parse().unwrap())
            .unwrap();
        // Phase-0 finding: the dialer must also hold an active webrtc-direct
        // listener or the dial fails with "no active listeners".
        dialer
            .listen_on("/ip4/127.0.0.1/udp/0/webrtc-direct".parse().unwrap())
            .unwrap();

        async fn first_listen_addr(s: &mut Swarm<ping::Behaviour>) -> Multiaddr {
            loop {
                if let SwarmEvent::NewListenAddr { address, .. } = s.select_next_some().await {
                    return address;
                }
            }
        }

        let dial_addr = tokio::time::timeout(Duration::from_secs(10), async {
            let addr = first_listen_addr(&mut listener).await;
            let _ = first_listen_addr(&mut dialer).await;
            addr
        })
        .await
        .expect("listen addrs assigned");

        // The advertised addr must be browser-dialable: /webrtc-direct + /certhash.
        assert!(
            dial_addr.iter().any(|p| matches!(p, Protocol::WebRTCDirect)),
            "addr must carry /webrtc-direct: {dial_addr}"
        );
        assert!(
            dial_addr.iter().any(|p| matches!(p, Protocol::Certhash(_))),
            "addr must carry /certhash (CA-free): {dial_addr}"
        );

        dialer
            .dial(dial_addr.with(Protocol::P2p(listener_peer)))
            .unwrap();

        let connected = tokio::time::timeout(Duration::from_secs(20), async {
            loop {
                tokio::select! {
                    ev = listener.select_next_some() => {
                        if matches!(ev, SwarmEvent::ConnectionEstablished { .. }) { return true; }
                    }
                    ev = dialer.select_next_some() => {
                        match ev {
                            SwarmEvent::ConnectionEstablished { .. } => return true,
                            SwarmEvent::OutgoingConnectionError { error, .. } => {
                                eprintln!("dial error: {error}");
                            }
                            _ => {}
                        }
                    }
                }
            }
        })
        .await
        .unwrap_or(false);

        assert!(connected, "WebRTC-direct rust↔rust dial must establish a connection");
    }
}
