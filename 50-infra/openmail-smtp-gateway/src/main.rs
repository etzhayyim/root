//! openmail SMTP gateway binary.
//!
//! The listener is gated behind the `daemon` feature so the pure core (and its
//! tests) build without tokio/reqwest. Run with:
//!   cargo run -p openmail-smtp-gateway --features daemon

#[cfg(feature = "daemon")]
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing::subscriber::set_global_default(
        tracing_subscriber_fallback::fmt_or_noop(),
    )
    .ok();
    openmail_smtp_gateway::daemon::run().await
}

#[cfg(not(feature = "daemon"))]
fn main() {
    eprintln!(
        "openmail-smtp-gateway: built without the `daemon` feature.\n\
         Rebuild with `--features daemon` to run the SMTP-in listener.\n\
         (The pure SMTP/render/routing core is exercised by `cargo test`.)"
    );
}

/// Minimal tracing init that doesn't add a hard dependency on tracing-subscriber:
/// if the crate is present it formats; otherwise logging is a no-op. Kept tiny so
/// the binary has no extra required dep — the daemon's value is the relay, not logs.
#[cfg(feature = "daemon")]
mod tracing_subscriber_fallback {
    /// Returns a no-op subscriber; `tracing::info!` calls simply do nothing unless
    /// an operator wires their own subscriber. This avoids pulling tracing-subscriber
    /// into the dependency graph for R0.
    pub fn fmt_or_noop() -> tracing::subscriber::NoSubscriber {
        tracing::subscriber::NoSubscriber::default()
    }
}
