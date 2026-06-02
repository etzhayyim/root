//! R0 SMTP-in listener (feature `daemon`).
//!
//! Wires [`crate::smtp_in::SmtpSession`] to a TCP socket and relays each accepted
//! message to kotoba-server `email.ingest` per resolved recipient. This is the
//! deliberately-thin, untested edge of the gateway (the protocol/render/routing
//! logic it calls is fully tested in the pure modules).
//!
//! R0 caveats (documented, not yet implemented — see README):
//!   • No STARTTLS — terminate TLS in front (Cloudflare / stunnel) for now.
//!   • No DKIM/SPF/DMARC verification — accepts on envelope only.
//!   • Authenticates to kotoba-server as the operator DID via a Bearer token from
//!     `OPENMAIL_OPERATOR_TOKEN` (inbound delivery into any member inbox).

use std::sync::Arc;

use anyhow::{Context, Result};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::{TcpListener, TcpStream};

use crate::ingest::{ingest_request_body, ingest_url};
use crate::routing::{resolve_recipient, Recipient};
use crate::smtp_in::{Event, SmtpSession};

/// Runtime configuration, sourced from env in [`run`].
#[derive(Clone)]
pub struct Config {
    pub bind_addr: String,
    pub hostname: String,
    pub kotoba_base: String,
    pub operator_token: String,
}

impl Config {
    pub fn from_env() -> Result<Self> {
        Ok(Self {
            bind_addr: std::env::var("OPENMAIL_BIND").unwrap_or_else(|_| "0.0.0.0:2525".into()),
            hostname: std::env::var("OPENMAIL_HOSTNAME")
                .unwrap_or_else(|_| "mx.openmail.etzhayyim.com".into()),
            kotoba_base: std::env::var("OPENMAIL_KOTOBA_BASE")
                .unwrap_or_else(|_| "http://127.0.0.1:8077".into()),
            operator_token: std::env::var("OPENMAIL_OPERATOR_TOKEN")
                .context("OPENMAIL_OPERATOR_TOKEN required (Bearer for email.ingest)")?,
        })
    }
}

pub async fn run() -> Result<()> {
    let cfg = Arc::new(Config::from_env()?);
    let listener = TcpListener::bind(&cfg.bind_addr)
        .await
        .with_context(|| format!("bind {}", cfg.bind_addr))?;
    tracing::info!(addr = %cfg.bind_addr, hostname = %cfg.hostname, "openmail SMTP-in listening");

    let http = reqwest::Client::new();
    loop {
        let (stream, peer) = listener.accept().await?;
        let cfg = Arc::clone(&cfg);
        let http = http.clone();
        tokio::spawn(async move {
            if let Err(e) = handle_conn(stream, &cfg, &http).await {
                tracing::warn!(?peer, error = %e, "connection error");
            }
        });
    }
}

async fn handle_conn(stream: TcpStream, cfg: &Config, http: &reqwest::Client) -> Result<()> {
    let (read_half, mut write_half) = stream.into_split();
    let mut reader = BufReader::new(read_half);
    let mut session = SmtpSession::new(cfg.hostname.clone());

    write_half
        .write_all(session.greeting().wire().as_bytes())
        .await?;

    let mut line = String::new();
    loop {
        line.clear();
        let n = reader.read_line(&mut line).await?;
        if n == 0 {
            break; // peer closed
        }
        let trimmed = line.trim_end_matches(['\r', '\n']);
        match session.feed_line(trimmed) {
            // code 0 = body line in DATA mode, no reply on the wire.
            Event::Reply(r) if r.code == 0 => {}
            Event::Reply(r) => write_half.write_all(r.wire().as_bytes()).await?,
            Event::Quit(r) => {
                write_half.write_all(r.wire().as_bytes()).await?;
                break;
            }
            Event::Complete { message, reply } => {
                deliver(&message, cfg, http).await;
                write_half.write_all(reply.wire().as_bytes()).await?;
            }
        }
    }
    Ok(())
}

/// Relay one accepted message to each in-domain recipient via `email.ingest`.
/// Best-effort R0: failures are logged; a future revision should map per-recipient
/// delivery failures back to SMTP status codes before the final reply.
async fn deliver(message: &crate::smtp_in::InboundMessage, cfg: &Config, http: &reqwest::Client) {
    let url = ingest_url(&cfg.kotoba_base);
    for rcpt in &message.rcpts {
        match resolve_recipient(rcpt) {
            Recipient::Did(did) => {
                let body = ingest_request_body(&message.data, &did, None);
                let res = http
                    .post(&url)
                    .bearer_auth(&cfg.operator_token)
                    .json(&body)
                    .send()
                    .await;
                match res {
                    Ok(r) if r.status().is_success() => {
                        tracing::info!(%did, "delivered inbound mail to kotoba inbox")
                    }
                    Ok(r) => tracing::warn!(%did, status = %r.status(), "email.ingest rejected"),
                    Err(e) => tracing::warn!(%did, error = %e, "email.ingest call failed"),
                }
            }
            Recipient::NoSuchUser(a) => tracing::warn!(addr = %a, "550 no such user"),
            Recipient::NotOurDomain(a) => tracing::warn!(addr = %a, "relay denied"),
        }
    }
}
