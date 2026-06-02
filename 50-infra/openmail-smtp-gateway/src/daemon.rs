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
            Event::Complete { message, reply: _ } => {
                // Drive the per-recipient delivery, then map outcomes → one final
                // SMTP reply (the smtp_in default 250 is overridden by the real result).
                let outcomes = deliver(&message, cfg, http).await;
                let (code, text) = crate::status::final_reply(&outcomes);
                let final_reply = crate::smtp_in::SmtpReply::new(code, text);
                write_half.write_all(final_reply.wire().as_bytes()).await?;
            }
            Event::StartTls(_) => {
                // The protocol supports STARTTLS (advertised + handled by the state
                // machine); the inbound TLS handshake needs a server certificate,
                // which this R0 daemon is not provisioned with. Refuse with 454 so
                // the client continues in plaintext rather than expecting TLS.
                // Wiring: load OPENMAIL_TLS_CERT/KEY, accept with 220, then
                // tokio-rustls Acceptor + session.reset_after_starttls().
                let r = crate::smtp_in::SmtpReply::new(454, "4.7.0 STARTTLS not available (no cert)");
                write_half.write_all(r.wire().as_bytes()).await?;
            }
        }
    }
    Ok(())
}

/// Relay one accepted message to each in-domain recipient via `email.ingest`,
/// returning the per-recipient outcome for [`crate::status::final_reply`].
async fn deliver(
    message: &crate::smtp_in::InboundMessage,
    cfg: &Config,
    http: &reqwest::Client,
) -> Vec<crate::status::Delivery> {
    use crate::status::Delivery;
    let url = ingest_url(&cfg.kotoba_base);
    let mut outcomes = Vec::with_capacity(message.rcpts.len());
    for rcpt in &message.rcpts {
        let outcome = match resolve_recipient(rcpt) {
            Recipient::Did(did) => {
                let body = ingest_request_body(&message.data, &did, None);
                match http
                    .post(&url)
                    .bearer_auth(&cfg.operator_token)
                    .json(&body)
                    .send()
                    .await
                {
                    Ok(r) if r.status().is_success() => {
                        tracing::info!(%did, "delivered inbound mail to kotoba inbox");
                        Delivery::Delivered
                    }
                    Ok(r) if r.status().is_server_error() => {
                        tracing::warn!(%did, status = %r.status(), "email.ingest 5xx (transient)");
                        Delivery::Transient
                    }
                    Ok(r) => {
                        tracing::warn!(%did, status = %r.status(), "email.ingest rejected");
                        Delivery::PermanentReject
                    }
                    Err(e) => {
                        tracing::warn!(%did, error = %e, "email.ingest call failed (transient)");
                        Delivery::Transient
                    }
                }
            }
            Recipient::NoSuchUser(a) => {
                tracing::warn!(addr = %a, "550 no such user");
                Delivery::NoSuchUser
            }
            Recipient::NotOurDomain(a) => {
                tracing::warn!(addr = %a, "relay denied");
                Delivery::RelayDenied
            }
        };
        outcomes.push(outcome);
    }
    outcomes
}

/// Outbound: drive one [`crate::smtp_out::SmtpClient`] conversation to a resolved MX
/// host over plain TCP. R0 edge — no STARTTLS, no MX lookup here (resolve via
/// [`crate::smtp_out::select_mx`] over a DNS resolver and pass `host` in). Returns
/// the accepted/rejected recipient split, or an error string on abort.
pub async fn relay_to_mx(
    host: &str,
    port: u16,
    ehlo_name: &str,
    msg: crate::smtp_out::OutboundMessage,
) -> Result<(Vec<String>, Vec<String>), String> {
    use crate::smtp_out::{Action, SmtpClient};

    let stream = TcpStream::connect((host, port))
        .await
        .map_err(|e| format!("connect {host}:{port}: {e}"))?;
    let (read_half, mut write_half) = stream.into_split();
    let mut reader = BufReader::new(read_half);
    let mut client = SmtpClient::new(ehlo_name, msg);

    let mut line = String::new();
    loop {
        line.clear();
        let n = reader
            .read_line(&mut line)
            .await
            .map_err(|e| format!("read: {e}"))?;
        if n == 0 {
            return Err("MX closed connection".into());
        }
        let code: u16 = line.get(..3).and_then(|c| c.parse().ok()).unwrap_or(0);
        // Skip multiline reply continuations ("250-..."); act on the final line ("250 ...").
        if matches!(line.as_bytes().get(3), Some(b'-')) {
            continue;
        }
        match client.on_reply(code) {
            Action::Send(cmd) => {
                write_half
                    .write_all(format!("{cmd}\r\n").as_bytes())
                    .await
                    .map_err(|e| format!("write: {e}"))?;
            }
            Action::SendData(payload) => {
                write_half.write_all(&payload).await.map_err(|e| format!("write data: {e}"))?;
                write_half.write_all(b"\r\n.\r\n").await.map_err(|e| format!("write dot: {e}"))?;
            }
            Action::StartTls => {
                // Outbound opportunistic STARTTLS: the state machine asked to upgrade.
                // R0 relay is plaintext (constructed via SmtpClient::new, which never
                // emits this); wiring tokio-rustls (client, webpki-roots) here +
                // SmtpClient::new_with_starttls enables it. Abort rather than send
                // cleartext after a TLS promise.
                return Err("outbound STARTTLS handshake not wired in R0".into());
            }
            Action::Done { accepted, rejected } => return Ok((accepted, rejected)),
            Action::Abort(why) => return Err(why),
        }
    }
}

/// Execute a planned outbound job: for each destination domain, resolve its MX hosts
/// and try them in order until one accepts. `resolve_mx` is injected (wire a DNS
/// resolver here — live MX lookup is the remaining edge; an R0 caller can pass
/// `|d| vec![d.to_string()]`). Returns per-domain delivery results.
pub async fn execute_plan(
    plan: &crate::orchestrate::OutboundPlan,
    ehlo_name: &str,
    port: u16,
    resolve_mx: impl Fn(&str) -> Vec<String>,
) -> Vec<(String, Result<(Vec<String>, Vec<String>), String>)> {
    use crate::orchestrate::OutboundStatus;
    let mut results = Vec::new();
    if !matches!(plan.status, OutboundStatus::Planned) {
        return results; // NoExternal or Held → nothing for the bridge to relay
    }
    for delivery in &plan.deliveries {
        let hosts = resolve_mx(&delivery.domain);
        let mut outcome = Err(format!("no MX hosts for {}", delivery.domain));
        for host in &hosts {
            match relay_to_mx(host, port, ehlo_name, delivery.message.clone()).await {
                Ok(r) => {
                    outcome = Ok(r);
                    break;
                }
                Err(e) => {
                    tracing::warn!(domain = %delivery.domain, host = %host, error = %e, "MX attempt failed");
                    outcome = Err(e); // fall through to the next MX
                }
            }
        }
        results.push((delivery.domain.clone(), outcome));
    }
    results
}

/// Publish a member's DKIM records to Cloudflare (the ARK-enrollment hook's HTTP
/// edge). `reqs` come from `provision::enrollment_requests` (public keys only).
pub async fn publish_dkim_records(
    reqs: &[crate::provision::CloudflareRequest],
    cf_token: &str,
    http: &reqwest::Client,
) -> Vec<Result<(), String>> {
    let mut out = Vec::with_capacity(reqs.len());
    for r in reqs {
        let res = http.post(&r.url).bearer_auth(cf_token).json(&r.body).send().await;
        out.push(match res {
            Ok(resp) if resp.status().is_success() => Ok(()),
            Ok(resp) => Err(format!("cloudflare {}", resp.status())),
            Err(e) => Err(e.to_string()),
        });
    }
    out
}

/// Fetch + decode the on-chain `Paid` postage receipt for `message_hash` via an
/// `eth_getLogs` JSON-RPC call. Returns `Ok(None)` when no matching event exists.
pub async fn fetch_postage_receipt(
    rpc_url: &str,
    contract: &str,
    message_hash: &str,
    from_block: &str,
    http: &reqwest::Client,
) -> Result<Option<crate::postage::PostageReceipt>, String> {
    let filter = crate::postage::paid_log_filter(contract, message_hash, from_block);
    let req = serde_json::json!({
        "jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [filter],
    });
    let resp = http.post(rpc_url).json(&req).send().await.map_err(|e| e.to_string())?;
    let body: serde_json::Value = resp.json().await.map_err(|e| e.to_string())?;
    if let Some(err) = body.get("error") {
        return Err(format!("eth_getLogs error: {err}"));
    }
    let result = body.get("result").ok_or("eth_getLogs: no result")?;
    Ok(crate::postage::receipt_from_logs(result))
}
